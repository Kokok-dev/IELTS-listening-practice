from pathlib import Path
import json,shutil,time,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from juting.server import create_app
from juting.transcripts import TranscriptParser
ROOT=Path(__file__).resolve().parents[1]
data=ROOT/'outputs/v03-verification-data'
data.mkdir(exist_ok=True)
app=create_app(data,ROOT/'models/small.en',ROOT/'web')
c=TestClient(app);c.headers['X-Juting-Token']=app.state.token
report=[]
for cid in ['8b6b1f09cd48491f96edfe4c06d5f660','1ceeefd785454ae3bceef93ae79ae9d6']:
    old=json.loads((ROOT/'data/courses'/cid/'course.json').read_text('utf-8'))
    app.state.store.save(old)
    folder=app.state.store.folder(cid)
    if old.get('source_id'):
        p=TranscriptParser(1);p.feed((ROOT/'outputs/transcript-probe.html').read_text('utf-8'))
        (folder/'reference.json').write_text(json.dumps(dict(lines=p.lines,url=old['source_url'])),'utf-8')
    def no_repeat(*args):raise AssertionError('Cached word timing must not run ASR again')
    app.state.recognizer.transcribe=no_repeat
    job=c.post(f'/api/courses/{cid}/transcribe').json()
    for _ in range(500):
        state=c.get('/api/jobs/'+job['id']).json()
        if state['status'] in ('done','error'):break
        time.sleep(.02)
    assert state['status']=='done',state
    saved=c.get('/api/courses/'+cid).json()
    report.append(dict(id=cid,before=len(old['segments']),after=len(saved['segments']),kind=saved['segmentation'],
        reference=saved.get('reference'),first_start=saved['segments'][0]['start'],
        announcements=sum(s.get('announcement',False) for s in saved['segments'])))
coverage=[]
for f in (ROOT/'research/catalog-cache').glob('*.html'):
    html=f.read_text('utf-8')
    for section in range(1,5):
        p=TranscriptParser(section);p.feed(html)
        coverage.append(sum(len(x) for x in p.lines)>100)
report.append(dict(cached_reference_sections=sum(coverage),checked=len(coverage)))
(ROOT/'outputs/v03-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
app.state.executor.shutdown()
