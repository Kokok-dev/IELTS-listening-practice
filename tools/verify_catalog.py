from pathlib import Path
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed

root=Path(__file__).resolve().parents[1]
entries=json.loads((root/'web/catalog.json').read_text('utf-8'))


def check(entry):
    problems=[]
    for key in ['audio_url','fallback_audio_url']:
        url=entry.get(key)
        if not url:
            continue
        try:
            request=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'Mozilla/5.0','Referer':entry['source_url']})
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request,timeout=18) as r:
                if r.status==200 and ('audio' in r.headers.get('content-type','') or int(r.headers.get('content-length','0'))>100000):
                    return dict(id=entry['id'],ok=True,url=url,size=int(r.headers.get('content-length','0')),type=r.headers.get('content-type'))
                raise ValueError(str(r.headers))
        except Exception as exc:
            problems.append(str(exc))
    return dict(id=entry['id'],ok=False,errors=problems)


if __name__=='__main__':
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(check,e) for e in entries]
        for f in as_completed(futures):
            result=f.result(); results.append(result)
            if not result['ok'] or len(results)%25==0:
                print(len(results),result,flush=True)
    report=dict(total=len(results),ok=sum(r['ok'] for r in results),failed=[r for r in results if not r['ok']],results=results)
    (root/'outputs/catalog-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    # Prefer the route actually verified, keeping a secondary source when present.
    by_id={r['id']:r for r in results}
    for e in entries:
        r=by_id[e['id']]
        e['verified']=r['ok']
        if r['ok']:
            if r['url']!=e['audio_url']:
                e['fallback_audio_url']=e['audio_url'];e['audio_url']=r['url']
            e['size']=r['size']
    (root/'web/catalog.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),'utf-8')
    print('VERIFIED',report['ok'],'/',report['total'],flush=True)
