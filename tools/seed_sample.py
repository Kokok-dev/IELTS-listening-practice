from pathlib import Path
import json
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from juting.server import create_app
from juting.audio import align_words

root=Path(__file__).resolve().parents[1]
app=create_app(root/'data',root/'models'/'small.en',root/'web')
store=app.state.store
started=time.monotonic()
existing=store.library()
if existing:
    course_id=existing[0]['id']
else:
    result=app.state.import_audio(Path(r'C:\Users\MR\Downloads\Test 1-Section 2.mp3'),
        'Test 1 · Section 2',lambda p,m: print(round(p),m,flush=True))
    course_id=result['course_id']
c=store.load(course_id)
print('IMPORTED',course_id,c['duration'],'seconds',len(c['segments']),'segments',flush=True)
if not c.get('words'):
    words,raw=app.state.recognizer.transcribe(store.folder(course_id)/'audio.wav',lambda p,m: print(round(p),m,flush=True))
    c=store.load(course_id)
    c.update(words=words,asr_raw=raw)
    align_words(c['segments'],words)
    store.save(c)
report=dict(id=course_id,duration=c['duration'],segments=len(c['segments']),words=len(c['words']),
    elapsed_seconds=round(time.monotonic()-started,2),gate_db=c['gate'],
    first_sentences=[dict(start=s['start'],end=s['end'],text=s['text']) for s in c['segments'][:12]])
Path('outputs').mkdir(exist_ok=True)
Path('outputs/sample-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
