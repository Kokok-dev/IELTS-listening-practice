from pathlib import Path
import hashlib
import json
import zipfile
import argparse

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--folder',type=Path,default=root/'outputs/staging-v0.3.0/句听')
parser.add_argument('--version',default='0.3.0')
args=parser.parse_args()
folder=args.folder
archive=root/f'outputs/句听-Windows-v{args.version}.zip'
files=[]
for path in folder.rglob('*'):
    if not path.is_file():
        continue
    rel=path.relative_to(folder)
    if rel.parts[0]=='data' and (len(rel.parts)<2 or rel.parts[1]!='courses'):
        continue
    files.append(path)
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as out:
    for i,path in enumerate(files):
        out.write(path,Path('句听')/path.relative_to(folder))
        if i%200==0:
            print('PACKED',i,'/',len(files),flush=True)
with zipfile.ZipFile(archive) as check:
    bad=check.testzip()
    if bad:
        raise ValueError('Archive verification failed: '+bad)
with archive.open('rb') as file:
    digest=hashlib.file_digest(file,'sha256').hexdigest()
(archive.with_suffix('.zip.sha256')).write_text(digest+'  '+archive.name+'\n','utf-8')
report=dict(archive=archive.name,bytes=archive.stat().st_size,sha256=digest,files=len(files),
            includes_model=True,excludes_webview_profile=True)
(root/'outputs/release-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(report,ensure_ascii=False),flush=True)
