import json
import time
from pathlib import Path
import pytest
from juting.transcripts import TranscriptParser,model_sentences,align_reference,is_announcement,preserve_practice
from juting.server import create_app
from juting.audio import new_segment
from fastapi.testclient import TestClient


def test_reference_section_and_speaker_parsing():
    p=TranscriptParser(2)
    p.feed('<div id="ielts-listening-transcript-1"><p>Wrong section.</p></div><div id="ielts-listening-transcript-2"><p>MAN: A short sentence.</p><p>Another one.</p></div><p>Ignore.</p>')
    assert p.lines==['A short sentence.','Another one.']


def test_sentences_use_model_punctuation_not_long_pauses():
    words=[dict(word=' Hello',start=1,end=2),dict(word=' there.',start=5,end=6),dict(word=' Goodbye!',start=7,end=8)]
    s=model_sentences(words,9)
    assert len(s)==2 and s[0]['text']=='Hello there.'
    assert s[0]['start']<1 and s[0]['end']>6


def test_alignment_excludes_exam_intro_and_rejects_wrong_transcript():
    words=[dict(word=w,start=i,end=i+.8) for i,w in enumerate([' Section',' one.',' Hello',' there.',' Goodbye!',' End.'])]
    segments,ratio=align_reference(['Hello there. Goodbye!'],words,8)
    assert ratio==1 and len(segments)==2 and segments[0]['start']>1
    assert segments[-1]['end']<5
    with pytest.raises(ValueError): align_reference(['A completely unrelated recording.'],words,8)
    assert is_announcement('Now listen and answer questions eleven to twenty.')
    assert is_announcement("You'll hear an introduction to a conference.")
    assert not is_announcement('Now we will discuss the research results.')


def test_recut_keeps_answer_once_and_marks_for_review():
    a=new_segment(0,5);a.update(answer='saved',note='note',starred=True)
    result=[new_segment(0,2),new_segment(2,5)]
    preserve_practice([a],result)
    assert sum(s['answer']=='saved' for s in result)==1
    assert result[1]['practice']['needs_review'] and result[1]['starred']


def test_cache_never_removes_imported_audio_or_records(tmp_path):
    app=create_app(tmp_path/'data',tmp_path/'models',Path(__file__).resolve().parents[1]/'web')
    client=TestClient(app);client.headers['X-Juting-Token']=app.state.token
    store=app.state.store
    for cid,source in [('a'*32,'cam-21-1-1'),('b'*32,None)]:
        store.save(dict(id=cid,title='demo',segments=[new_segment(0,1)],source_id=source))
        (store.folder(cid)/'audio.wav').write_bytes(b'audio')
    original=(store.folder('a'*32)/'course.json').read_bytes()
    app.state.jobs['busy']=dict(status='running')
    assert client.post('/api/cache/clear',json={'downloads':True}).status_code==409
    app.state.jobs.clear()
    assert client.post('/api/cache/clear',json={'downloads':True}).json()['removed_bytes']==5
    assert not (store.folder('a'*32)/'audio.wav').exists()
    assert (store.folder('b'*32)/'audio.wav').exists()
    assert (store.folder('a'*32)/'course.json').read_bytes()==original
    assert client.get('/api/courses/'+'a'*32).json()['audio_cached'] is False
