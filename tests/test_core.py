from pathlib import Path
import io
import json
import time
import wave
import numpy as np
import pytest
from fastapi.testclient import TestClient
from juting.audio import split_pauses, align_words, new_segment, RATE
from juting.server import create_app


def speech(seconds,volume=.2):
    t=np.arange(round(seconds*RATE))/RATE
    return (volume*np.sin(2*np.pi*220*t)).astype(np.float32)


def test_pause_cuts_and_speech_coverage():
    samples=np.concatenate([np.zeros(RATE),speech(1),np.zeros(RATE//2),speech(2),np.zeros(RATE)])
    segments,_,_=split_pauses(samples)
    assert len(segments)==2
    assert segments[0]['start']<=1 and segments[0]['end']>=2
    assert segments[1]['start']<=2.5 and segments[1]['end']>=4.5
    assert segments[0]['end']<segments[1]['start']


def test_short_dips_do_not_split_and_long_audio_has_safe_limits():
    samples=np.concatenate([speech(1),np.zeros(1600),speech(1)])
    assert len(split_pauses(samples)[0])==1
    segments,_,_=split_pauses(speech(50),max_length=18)
    assert all(0<s['end']-s['start']<=18.01 for s in segments)
    assert segments[0]['start']==0
    assert segments[-1]['end']==50
    assert all(a['end']==b['start'] for a,b in zip(segments,segments[1:]))


def test_silence_and_quiet_recording():
    assert split_pauses(np.zeros(RATE*4))[0]==[]
    assert len(split_pauses(np.concatenate([np.zeros(RATE),speech(1,.004),np.zeros(RATE)]))[0])==1


def test_short_pause_padding_does_not_overlap():
    segments,_,_=split_pauses(np.concatenate([speech(1),np.zeros(3200),speech(1)]),pause=.15)
    assert len(segments)==2
    assert segments[0]['end']<=segments[1]['start']


def test_each_word_assigned_once_manual_correction_survives():
    segments=[new_segment(0,1),new_segment(2,3)]
    words=[dict(start=.1,end=.6,word=' Hello'),dict(start=2,end=2.8,word=' world.')]
    align_words(segments,words)
    assert [s['text'] for s in segments]==['Hello','world.']
    segments[0].update(text='A correction.',text_source='manual')
    align_words(segments,words)
    assert segments[0]['text']=='A correction.'


@pytest.fixture
def setup_app(tmp_path):
    assets=Path(__file__).resolve().parents[1]/'web'
    app=create_app(tmp_path/'data',tmp_path/'models',assets)
    c=TestClient(app)
    c.headers['X-Juting-Token']=app.state.token
    return app,c


def wav_bytes():
    pcm=(np.concatenate([speech(1),np.zeros(RATE),speech(2)])*32767).astype('<i2')
    b=io.BytesIO()
    with wave.open(b,'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(RATE);out.writeframes(pcm.tobytes())
    return b.getvalue()


def imported(app,c):
    job=c.post('/api/import',files={'file':('test.wav',wav_bytes(),'audio/wav')}).json()
    for _ in range(100):
        result=c.get('/api/jobs/'+job['id']).json()
        if result['status'] not in ['running','queued']:
            assert result['status']=='done',result
            return c.get('/api/courses/'+result['result']['course_id']).json()
        time.sleep(.02)
    pytest.fail('import timed out')


def test_real_import_persistence_range_and_export(setup_app):
    app,c=setup_app
    course=imported(app,c); cid=course['id']; sid=course['segments'][0]['id']
    assert len(course['segments'])==2
    assert c.patch(f'/api/courses/{cid}/segments/{sid}',json={'answer':'Hello there','done':True,'note':'弱读'}).status_code==200
    assert app.state.store.load(cid)['segments'][0]['answer']=='Hello there'
    assert c.get('/api/library').json()[0]['done']==1
    response=c.get(f'/api/courses/{cid}/audio',headers={'Range':'bytes=0-99'})
    assert response.status_code==206 and len(response.content)==100
    assert 'Hello there' in c.get(f'/api/courses/{cid}/export/md').content.decode('utf-8-sig')
    assert c.get(f'/api/courses/{cid}/export/srt').status_code==200
    assert c.get(f'/api/courses/{cid}/export/json').status_code==200


def test_split_merge_boundary_and_backup(setup_app):
    app,c=setup_app
    course=imported(app,c); cid=course['id']; s=course['segments'][0]; sid=s['id']
    c.patch(f'/api/courses/{cid}/segments/{sid}',json={'answer':'keep my words','text':'Manual transcript'})
    url=f'/api/courses/{cid}/edit-boundary'
    split=c.post(url,json={'action':'split','segment_id':sid,'at':.5})
    assert split.status_code==200,split.text
    assert len(split.json()['segments'])==3
    assert split.json()['segments'][0]['answer']=='keep my words'
    merged=c.post(url,json={'action':'merge','segment_id':sid})
    assert merged.status_code==200 and len(merged.json()['segments'])==2
    assert merged.json()['segments'][0]['answer']=='keep my words'
    assert list((app.state.store.folder(cid)/'backups').glob('*.json'))
    assert c.post(url,json={'action':'trim','segment_id':sid,'start':0,'end':99}).status_code==400
    assert c.post(url,json={'action':'split','segment_id':sid,'at':0}).status_code==400


def test_security_and_bad_inputs(setup_app):
    app,c=setup_app
    assert c.get('/api/library',headers={'Host':'evil.example'}).status_code==403
    assert c.post('/api/model/download',headers={'X-Juting-Token':'wrong'}).status_code==403
    assert c.post('/api/model/download',headers={'Origin':'https://evil.example'}).status_code==403
    assert c.get('/api/courses/not-a-valid-id').status_code==404
    assert c.post('/api/import',files={'file':('bad.exe',b'x')}).status_code==400
    course=imported(app,c)
    assert c.post('/api/courses/'+course['id']+'/resplit',json={'pause':-1}).status_code==422


def test_resplit_retains_asr_and_backs_up_answers(setup_app):
    app,c=setup_app
    course=imported(app,c);cid=course['id']
    course['segments'][0]['answer']='a saved answer'
    course['words']=[dict(start=.1,end=.6,word=' Hello')]
    app.state.store.save(course)
    response=c.post('/api/courses/'+cid+'/resplit',json={'pause':.5,'threshold_db':-36,'max_length':18})
    assert response.status_code==200
    assert response.json()['segments'][0]['text']=='Hello'
    backup=list((app.state.store.folder(cid)/'backups').glob('*.json'))[0]
    assert json.loads(backup.read_text('utf-8'))['segments'][0]['answer']=='a saved answer'


def test_practice_state_keeps_dictation_and_cloze_separate(setup_app):
    app,c=setup_app
    course=imported(app,c);cid=course['id'];sid=course['segments'][0]['id']
    url=f'/api/courses/{cid}/segments/{sid}'
    result=c.patch(url,json={'answer':'my full dictation','practice':{'plays':2,'hints':1,'checks':1,'needs_review':True,'last_score':75,'cloze_sets':{'stable-signature':{'2':'garden'}}}})
    assert result.status_code==200,result.text
    saved=app.state.store.load(cid)['segments'][0]
    assert saved['answer']=='my full dictation'
    assert saved['practice']['cloze_sets']['stable-signature']['2']=='garden'
    c.patch(url,json={'practice':{'plays':3}})
    saved=app.state.store.load(cid)['segments'][0]
    assert saved['answer']=='my full dictation'
    assert saved['practice']['plays']==3 and saved['practice']['needs_review']
    assert c.patch(url,json={'practice':{'plays':-1}}).status_code==422
    assert c.patch(url,json={'practice':{'cloze_sets':{'x':{'0':'x'*501}}}}).status_code==400
