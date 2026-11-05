"""Build a portable Windows distribution using the project venv."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import importlib.metadata

ROOT=Path(__file__).resolve().parents[1]


def main():
    os.chdir(ROOT)
    distribution=ROOT/'outputs/staging-v0.2.0'
    distribution.resolve().relative_to(ROOT.resolve())
    cmd=[sys.executable,'-m','PyInstaller','--noconfirm','--windowed','--onedir',
         '--name','句听','--distpath',str(distribution),'--workpath','build',
         '--add-data',f'{ROOT / "web"};web',
         '--hidden-import','webview.platforms.winforms','--hidden-import','webview.platforms.edgechromium',
         '--hidden-import','uvicorn.logging','--hidden-import','uvicorn.loops.auto',
         '--hidden-import','uvicorn.protocols.http.auto','--hidden-import','uvicorn.protocols.websockets.auto',
         '--hidden-import','uvicorn.lifespan.on',
         '--exclude-module','pytest','--exclude-module','IPython','--exclude-module','tkinter']
    for package in ['faster_whisper','ctranslate2','av','onnxruntime','tokenizers','webview','pythonnet','clr_loader']:
        cmd+=['--collect-all',package]
    icon=ROOT/'assets/juting.ico'
    if icon.exists():
        cmd+=['--icon',str(icon)]
    # The bundled Python runtime's SSLContext loads this CA-policy file next to
    # ssl.py. Preserve that file when freezing, without weakening TLS checks.
    ca_policy=Path(sys.base_prefix)/'Lib/codex-rejected-cas.pem'
    if ca_policy.exists():
        cmd+=['--add-data',f'{ca_policy};.']
    cmd+=['main.py']
    subprocess.run(cmd,check=True)
    dest=distribution/'句听'
    shutil.copytree(ROOT/'models',dest/'models',dirs_exist_ok=True)
    # Include only the supplied sample and an online download smoke-test. Avoid
    # copying WebView profiles, development logs, or synthetic test data.
    shutil.copytree(ROOT/'data/courses',dest/'data/courses',dirs_exist_ok=True)
    for filename in ['使用说明.md','THIRD_PARTY_NOTICES.md']:
        if (ROOT/filename).exists():
            shutil.copy2(ROOT/filename,dest/filename)
    for distribution in importlib.metadata.distributions():
        info=Path(distribution._path)
        license_dest=dest/'_licenses'/info.name
        license_dest.mkdir(parents=True,exist_ok=True)
        for item in info.iterdir():
            if item.name.lower().startswith(('license','copying','notice')) or item.name=='METADATA':
                if item.is_dir():
                    shutil.copytree(item,license_dest/item.name,dirs_exist_ok=True)
                else:
                    shutil.copy2(item,license_dest/item.name)
    print('BUILT',dest/'句听.exe',flush=True)


if __name__=='__main__':
    main()
