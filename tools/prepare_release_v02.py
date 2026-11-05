from pathlib import Path
import argparse
import importlib.util
import json
import shutil
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]


def install_update(stage:Path,target:Path,backup:Path):
    for path in (stage,target,backup):
        path.resolve().relative_to(ROOT.resolve())
    if not (stage/'句听.exe').is_file():
        raise ValueError('The staged executable is missing.')
    if __import__('os').name=='nt':
        import msvcrt
        lock_path=target/'data/.instance.lock'
        lock_path.parent.mkdir(parents=True,exist_ok=True)
        instance_guard=open(lock_path,'a+b')
        if instance_guard.seek(0,2)==0:
            instance_guard.write(b'0');instance_guard.flush()
        instance_guard.seek(0)
        try:
            msvcrt.locking(instance_guard.fileno(),msvcrt.LK_NBLCK,1)
        except OSError:
            instance_guard.close()
            raise RuntimeError('请先关闭正在运行的句听，再更新程序。')
    # Save practice data and the previous code before replacing program files.
    if backup.exists():
        raise ValueError('Backup path already exists; choose a new timestamp.')
    backup.mkdir(parents=True)
    if (target/'data').exists():
        shutil.copytree(target/'data',backup/'data',ignore=shutil.ignore_patterns('.instance.lock'))
    if (target/'句听.exe').exists():
        shutil.copy2(target/'句听.exe',backup/'句听.exe')
    if (target/'_internal/web').exists():
        shutil.copytree(target/'_internal/web',backup/'web')
    before={str(p.relative_to(target/'data')):p.read_bytes() for p in (target/'data/courses').glob('*/course.json')}
    # Neither data nor models is overwritten by a software update.
    for name in ('_internal','_licenses'):
        if (stage/name).exists():
            shutil.copytree(stage/name,target/name,dirs_exist_ok=True)
    for name in ('句听.exe','使用说明.md','THIRD_PARTY_NOTICES.md','更新记录.md'):
        if (stage/name).exists():
            shutil.copy2(stage/name,target/name)
    after={str(p.relative_to(target/'data')):p.read_bytes() for p in (target/'data/courses').glob('*/course.json')}
    if before!=after:
        raise RuntimeError('Practice data changed during installation. Check the backup.')
    return dict(preserved_courses=len(before),backup=str(backup))


if __name__=='__main__':
    result=install_update(ROOT/'outputs/staging-v0.2.0/句听',ROOT/'outputs/句听',ROOT/'outputs/backups'/('before-v0.2.0-'+datetime.now().strftime('%Y%m%d-%H%M%S')))
    print(json.dumps(result,ensure_ascii=False),flush=True)
