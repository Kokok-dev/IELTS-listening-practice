import importlib.util
from pathlib import Path


def test_updating_program_preserves_every_existing_course_and_model(tmp_path):
    source=Path(__file__).resolve().parents[1]/'tools/prepare_release_v02.py'
    spec=importlib.util.spec_from_file_location('release_update',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=tmp_path
    stage=tmp_path/'staged';target=tmp_path/'installed';backup=tmp_path/'backup'
    for folder in [stage/'_internal/web',target/'_internal/web',target/'data/courses/abc',target/'models']:
        folder.mkdir(parents=True)
    (stage/'句听.exe').write_bytes(b'new executable')
    (stage/'_internal/web/app.js').write_text('new UI','utf-8')
    (target/'句听.exe').write_bytes(b'previous executable')
    (target/'_internal/web/app.js').write_text('previous UI','utf-8')
    record=target/'data/courses/abc/course.json'
    record.write_text('{"answer":"user writing", "note":"my note"}','utf-8')
    (target/'models/custom.bin').write_bytes(b'keep this model')
    result=module.install_update(stage,target,backup)
    assert result['preserved_courses']==1
    assert record.read_bytes()==(backup/'data/courses/abc/course.json').read_bytes()
    assert (target/'句听.exe').read_bytes()==b'new executable'
    assert (backup/'句听.exe').read_bytes()==b'previous executable'
    assert (target/'models/custom.bin').read_bytes()==b'keep this model'
