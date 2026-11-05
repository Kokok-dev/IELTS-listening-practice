from pathlib import Path
import re
import sys
import urllib.request
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for i,u in enumerate(sys.argv[1:]):
    try:
        s=op.open(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf-8','replace')
        p=Path('research')/('ref-'+re.sub('[^a-zA-Z0-9]+','-',u)[-110:]+'.html')
        p.write_text(s,'utf-8')
        print('URL',u,'FILE',p,'LENGTH',len(s),flush=True)
        print('AUDIO',list(dict.fromkeys(re.findall(r'[^\s\x22\x27<>]+[.](?:mp3|m4a|MP3)[^\s\x22\x27<>]*',s)))[:12],flush=True)
        print('MATCHES',[(s[max(0,m.start()-80):m.start()+220]) for m in list(re.finditer(r'load.more|pagination|cambridge-ielts-0?1[^0-9]|audio_url|audioUrl|audio_file',s,re.I))[:12]],flush=True)
    except Exception as e:
        print(u,type(e).__name__,e,flush=True)
