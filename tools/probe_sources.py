import urllib.request
import re
from pathlib import Path
op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urls = [
    'https://www.ieltsweb.com/listening',
    'https://engexam.info/ielts-listening-practice-test-1/',
    'https://ieltstestsimulation.com/wpt-free-ielts-online-practice-tests.php',
    'https://ieltsextremes.com/ielts-listening-audios/',
    'https://dailydictation.com/',
]
Path('research').mkdir(exist_ok=True)
for i,u in enumerate(urls):
    try:
        req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
        s=op.open(req,timeout=25).read().decode('utf-8','replace')
        Path(f'research/source-{i}.html').write_text(s,'utf-8')
        print(u, 'OK',len(s))
        print('AUDIO', re.findall(r'[^\s\x22\x27<>]+[.]mp3[^\s\x22\x27<>]*',s)[:8])
        print('SCRIPTS',re.findall(r'<script[^>]+src=[\x22\x27]([^\x22\x27]+)',s)[-8:])
        print('LINKS',re.findall(r'href=[\x22\x27]([^\x22\x27]+)',s)[-25:])
    except Exception as e:
        print(u,type(e).__name__,e)
