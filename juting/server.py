import json
import logging
import re
import secrets
import shutil
import threading
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin
import urllib.request

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .storage import Store, now
from .audio import decode, read_wav, split_pauses, align_words, new_segment
from .asr import Recognizer, direct_opener


class SplitOptions(BaseModel):
    pause: float = Field(.45, ge=.15, le=2)
    threshold_db: float = Field(-36, ge=-65, le=-15)
    max_length: float = Field(18, ge=5, le=40)


class PracticeData(BaseModel):
    plays: int | None = Field(None, ge=0, le=1000000)
    checks: int | None = Field(None, ge=0, le=1000000)
    hints: int | None = Field(None, ge=0, le=1000000)
    last_score: float | None = Field(None, ge=0, le=100)
    needs_review: bool | None = None
    cloze_sets: dict[str, dict[str, str]] | None = Field(None, max_length=100)


class SegmentUpdate(BaseModel):
    answer: str | None = Field(None, max_length=20000)
    done: bool | None = None
    starred: bool | None = None
    note: str | None = Field(None, max_length=10000)
    text: str | None = Field(None, max_length=20000)
    practice: PracticeData | None = None


def create_app(data_root: Path, model_root: Path, assets: Path):
    app = FastAPI(title='句听', docs_url=None, redoc_url=None)
    store = Store(data_root)
    recognizer = Recognizer(model_root)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='juting')
    token = secrets.token_urlsafe(32)
    jobs, active = {}, {}
    job_lock = threading.Lock()
    app.state.store, app.state.recognizer = store, recognizer
    app.state.executor = executor
    app.state.token = token
    app.state.jobs = jobs

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        host = request.headers.get('host','').split(':')[0]
        if host not in ('127.0.0.1','localhost','testserver'):
            return JSONResponse({'detail':'仅允许本机访问。'},403)
        origin = request.headers.get('origin')
        if origin and urlparse(origin).netloc != request.headers.get('host'):
            return JSONResponse({'detail':'不允许跨站访问。'},403)
        if request.url.path.startswith('/api/') and request.method not in ('GET','HEAD'):
            if request.headers.get('x-juting-token') != token:
                return JSONResponse({'detail':'请重新打开软件。'},403)
        return await call_next(request)

    @app.exception_handler(FileNotFoundError)
    async def missing(request, exc):
        return JSONResponse({'detail':'找不到这份音频，请刷新资料库。'},404)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'detail':str(exc)},400)

    def course(course_id):
        return store.load(course_id)

    def submit(key, kind, work, course_id=None):
        with job_lock:
            if key in active:
                return jobs[active[key]].copy()
            job_id = uuid.uuid4().hex
            jobs[job_id] = dict(id=job_id, kind=kind, course_id=course_id, status='queued', progress=0, message='等待处理…')
            active[key] = job_id
        def report(progress, message):
            with job_lock:
                jobs[job_id].update(progress=round(progress,1),message=message)
        def run():
            with job_lock:
                jobs[job_id]['status'] = 'running'
            try:
                result = work(report)
                with job_lock:
                    jobs[job_id].update(status='done',progress=100,message='处理完成',result=result)
            except Exception as exc:
                logging.exception('Background job failed')
                with job_lock:
                    jobs[job_id].update(status='error',message=str(exc) or type(exc).__name__)
            finally:
                with job_lock:
                    active.pop(key,None)
        executor.submit(run)
        return jobs[job_id].copy()

    def ensure_idle(course_id):
        if any(j.get('course_id') == course_id and j['status'] in ('running','queued') for j in jobs.values()):
            raise HTTPException(409,'请等待当前音频处理完成后再修改切句。')

    def import_audio(source, title, report, source_id=None, source_url=None):
        course_id = uuid.uuid4().hex
        folder = store.folder(course_id)
        folder.mkdir(parents=True)
        try:
            report(15,'正在解码音频…')
            samples, rate = decode(source, folder / 'audio.wav')
            report(70,'正在检测停顿并切句…')
            segments, peaks, gate = split_pauses(samples)
            c = dict(id=course_id,title=title,duration=round(len(samples)/rate,3),created=now(),
                     segments=segments,peaks=peaks,words=[],asr_raw=[],current=0,
                     split=dict(pause=.45,threshold_db=-36,max_length=18),gate=gate,
                     source_id=source_id,source_url=source_url)
            store.save(c)
            return dict(course_id=course_id, count=len(segments))
        except Exception:
            # Only this operation's newly-created temporary course directory.
            shutil.rmtree(folder,ignore_errors=True)
            raise

    app.state.import_audio = import_audio

    @app.get('/',response_class=HTMLResponse)
    def index():
        return (assets / 'index.html').read_text('utf-8').replace('__JUTING_TOKEN__',token)

    @app.get('/api/status')
    def status():
        with job_lock:
            pending = [j.copy() for j in jobs.values() if j['status'] in ('queued','running')]
        return dict(version='0.2.0',model_ready=recognizer.ready(),jobs=pending,data_path=str(data_root))

    @app.get('/api/library')
    def library():
        return store.library()

    @app.get('/api/courses/{course_id}')
    def get_course(course_id: str):
        return course(course_id)

    @app.get('/api/courses/{course_id}/audio')
    def audio(course_id: str):
        course(course_id)
        return FileResponse(store.folder(course_id) / 'audio.wav',media_type='audio/wav')

    @app.post('/api/import')
    async def upload(file: UploadFile = File(...)):
        suffix = Path(file.filename or '').suffix.lower()
        if suffix not in ('.mp3','.wav','.m4a','.flac','.ogg','.aac','.mp4','.wma'):
            raise ValueError('请导入 MP3、WAV、M4A、FLAC、OGG、AAC、WMA 或 MP4 音频。')
        incoming = data_root / 'incoming'
        incoming.mkdir(exist_ok=True)
        path = incoming / (uuid.uuid4().hex + suffix)
        try:
            size = 0
            with path.open('wb') as out:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > 300 * 1024 * 1024:
                        raise ValueError('单个文件最大支持 300 MB。')
                    out.write(chunk)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        finally:
            await file.close()
        title = Path(file.filename).stem[:150]
        def work(report):
            try:
                return import_audio(path,title,report)
            finally:
                path.unlink(missing_ok=True)
        return submit(str(path),'import',work)

    @app.get('/api/jobs/{job_id}')
    def job(job_id: str):
        with job_lock:
            if job_id not in jobs:
                raise HTTPException(404,'任务已过期，请重新操作。')
            return jobs[job_id].copy()

    @app.patch('/api/courses/{course_id}/segments/{segment_id}')
    def update_segment(course_id: str, segment_id: str, body: SegmentUpdate):
        fields = body.model_dump(exclude_none=True)
        def update(c):
            s = next((s for s in c['segments'] if s['id']==segment_id),None)
            if s is None:
                raise HTTPException(404,'这句已经被重新切分，请刷新。')
            if 'practice' in fields:
                practice=fields.pop('practice')
                if any(len(answers)>500 or any(len(value)>500 for value in answers.values()) for answers in practice.get('cloze_sets',{}).values()):
                    raise ValueError('填空记录过长。')
                s.setdefault('practice',{}).update(practice)
            s.update(fields)
            if 'text' in fields:
                s['text_source'] = 'manual'
        store.update(course_id,update)
        return dict(ok=True)

    @app.patch('/api/courses/{course_id}')
    def update_course(course_id: str, body: dict):
        def update(c):
            if 'current' in body:
                c['current'] = max(0,min(int(body['current']),len(c['segments'])-1))
            if 'title' in body and isinstance(body['title'],str):
                c['title'] = body['title'].strip()[:150] or c['title']
        store.update(course_id,update)
        return dict(ok=True)

    def backup(c):
        folder = store.folder(c['id']) / 'backups'
        folder.mkdir(exist_ok=True)
        (folder / (now().replace(':','-') + '-' + uuid.uuid4().hex[:5] + '.json')).write_text(json.dumps(c,ensure_ascii=False),'utf-8')

    @app.post('/api/courses/{course_id}/resplit')
    def resplit(course_id: str, body: SplitOptions):
        ensure_idle(course_id)
        samples = read_wav(store.folder(course_id) / 'audio.wav')
        segments, peaks, gate = split_pauses(samples, **body.model_dump())
        def update(c):
            backup(c)
            c.update(segments=segments,peaks=peaks,gate=gate,split=body.model_dump(),current=0)
            align_words(c['segments'],c.get('words',[]))
        return store.update(course_id,update)

    @app.post('/api/courses/{course_id}/edit-boundary')
    def edit_boundary(course_id: str, body: dict):
        ensure_idle(course_id)
        def update(c):
            segments=c['segments']
            index=next((i for i,s in enumerate(segments) if s['id']==body.get('segment_id')),None)
            if index is None:
                raise ValueError('请先选择一句。')
            backup(c)
            s=segments[index]
            action=body.get('action')
            if action=='split':
                at=float(body.get('at',0))
                if not s['start']+.25 < at < s['end']-.25:
                    raise ValueError('请把播放位置放在句子中间，距两端至少 0.25 秒。')
                right=new_segment(at,s['end'],'manual')
                # Preserve original writing on the left. Never silently duplicate it.
                s['end']=round(at,3)
                s['text_source']=''
                segments.insert(index+1,right)
                align_words(segments,c.get('words',[]))
            elif action=='merge':
                if index+1>=len(segments):
                    raise ValueError('已经是最后一句。')
                right=segments.pop(index+1)
                s.update(end=right['end'],text=' '.join(filter(None,[s['text'],right['text']])),
                         answer=' '.join(filter(None,[s['answer'],right['answer']])),
                         note='\n'.join(filter(None,[s.get('note',''),right.get('note','')])),
                         done=False,starred=s['starred'] or right['starred'],text_source='manual')
            elif action=='trim':
                start,end=round(float(body['start']),3),round(float(body['end']),3)
                low=segments[index-1]['end'] if index else 0
                high=segments[index+1]['start'] if index+1<len(segments) else c['duration']
                if not low <= start < end <= high or end-start<.15:
                    raise ValueError('边界不能与相邻句重叠，且时长至少为 0.15 秒。')
                s.update(start=start,end=end)
                align_words(segments,c.get('words',[]))
            else:
                raise ValueError('未知操作。')
        return store.update(course_id,update)

    @app.post('/api/model/download')
    def download_model():
        return submit('model','model',lambda report: recognizer.download(report))

    @app.post('/api/courses/{course_id}/transcribe')
    def transcribe(course_id: str):
        course(course_id)
        ensure_idle(course_id)
        def work(report):
            words,raw=recognizer.transcribe(store.folder(course_id)/'audio.wav',report)
            def update(c):
                c.update(words=words,asr_raw=raw)
                align_words(c['segments'],words)
            store.update(course_id,update)
            return dict(course_id=course_id,words=len(words))
        return submit('asr:'+course_id,'asr',work,course_id)

    @app.get('/api/courses/{course_id}/export/{kind}')
    def export(course_id: str, kind: str):
        c=course(course_id)
        if kind=='json':
            content=json.dumps(c,ensure_ascii=False,indent=2)
        elif kind=='srt':
            def stamp(t):
                ms=round(t*1000); return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
            content='\n\n'.join(f"{i}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['text']}" for i,s in enumerate(c['segments'],1))
        elif kind=='md':
            content='# '+c['title']+'\n\n参考原文由本地语音识别或人工校正生成。\n\n'
            for i,s in enumerate(c['segments'],1):
                content+=f"## {i:02} · {s['start']:.2f}–{s['end']:.2f}s\n\n听写：{s['answer']}\n\n参考：{s['text']}\n\n笔记：{s.get('note','')}\n\n"
        else:
            raise HTTPException(404)
        return Response(content.encode('utf-8-sig'),media_type='application/octet-stream',headers={'Content-Disposition':f'attachment; filename="juting-{course_id[:8]}.{kind}"'})

    @app.get('/api/catalog')
    def catalog():
        path=assets/'catalog.json'
        entries=json.loads(path.read_text('utf-8')) if path.exists() else []
        downloaded={c.get('source_id'):c['id'] for c in store.library() if c.get('source_id')}
        return [entry | dict(course_id=downloaded.get(entry['id'])) for entry in entries]

    @app.post('/api/catalog/{entry_id}/download')
    def download_entry(entry_id: str):
        entries=json.loads((assets/'catalog.json').read_text('utf-8'))
        entry=next((e for e in entries if e['id']==entry_id),None)
        if not entry:
            raise HTTPException(404,'没有这份资料。')
        previous=next((c for c in store.library() if c.get('source_id')==entry_id),None)
        if previous:
            return dict(status='done',result=dict(course_id=previous['id']))
        def work(report):
            incoming=data_root/'incoming'; incoming.mkdir(exist_ok=True)
            path=incoming/(uuid.uuid4().hex+Path(urlparse(entry['audio_url']).path).suffix)
            try:
                report(1,'正在连接音频来源…')
                urls=list(dict.fromkeys(u for u in [entry['audio_url'],entry.get('fallback_audio_url')] if u))
                for attempt,url in enumerate(urls):
                    try:
                        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':entry['source_url']})
                        with direct_opener().open(request,timeout=40) as response,path.open('wb') as out:
                            total=int(response.headers.get('content-length',0)); received=0
                            while chunk:=response.read(512*1024):
                                received+=len(chunk)
                                if received>300*1024*1024:
                                    raise ValueError('音频超过 300 MB，请从来源页面检查后手动导入。')
                                out.write(chunk)
                                report(min(65,received/max(total,received)*65),f'正在下载 · {received/1e6:.1f} MB')
                            if total and received!=total:
                                raise ValueError('音频下载不完整，请重试。')
                        break
                    except (urllib.error.URLError,TimeoutError,OSError):
                        if attempt==len(urls)-1:
                            raise
                        report(1,'主音源暂时不可用，正在尝试备用音源…')
                return import_audio(path,entry['title'],report,entry_id,entry['source_url'])
            except (urllib.error.URLError,TimeoutError) as exc:
                raise ValueError('无法连接资料来源。请稍后重试，或打开来源页面下载后导入。详情：'+str(exc)) from exc
            finally:
                path.unlink(missing_ok=True)
        return submit('catalog:'+entry_id,'download',work)

    app.mount('/static',StaticFiles(directory=assets),name='static')
    return app
