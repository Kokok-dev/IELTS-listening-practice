"""Build a metadata-only catalogue from public source pages, never bulk audio."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import json
import re
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'research'/'catalog-cache'
CACHE.mkdir(parents=True,exist_ok=True)


def fetch(url):
    cache=CACHE/(re.sub('[^a-zA-Z0-9]+','-',url)[-140:]+'.html')
    if cache.exists():
        return cache.read_text('utf-8')
    for attempt in range(3):
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            text=opener.open(request,timeout=30).read().decode('utf-8','replace')
            cache.write_text(text,'utf-8')
            return text
        except Exception:
            if attempt==2:
                raise
            time.sleep(1)


def inspect_test(url):
    match=re.search(r'cambridge-ielts-(\d+)-academic-listening-test-(\d+)',url)
    book,test=map(int,match.groups())
    page=html.unescape(fetch(url))
    audios=list(dict.fromkeys(re.findall(r'https?[^\s\x22\x27<>\\]+\.(?:mp3|m4a|MP3)',page)))
    entries=[]
    for section in range(1,5):
        matches=[u for u in audios if re.search(rf'(?:test[-_ ]?0?{test}|test[-_ ]?0?{test}[-_ ]?part|test[-_ ]?0?{test}[-_ ]?section)[-_ ](?:part[-_ ]?|section[-_ ]?)?0?{section}\.(?:mp3|m4a)$',u,re.I)]
        # The source's own audio tags keep section order; use them when filenames
        # use a historical naming scheme. Do not invent a URL from a pattern.
        if not matches:
            tags=re.findall(r'<audio\b[^>]*>.*?</audio>',page,re.S|re.I)
            section_urls=[]
            for tag in tags:
                found=re.findall(r'(?:src|data-fallback-src)=[\x22\x27](https?[^\x22\x27]+)',tag)
                found=[u for u in found if re.search(r'\.(mp3|m4a)$',u,re.I)]
                if found:
                    section_urls.append(found)
            if len(section_urls)==4:
                matches=section_urls[section-1]
        if not matches:
            raise ValueError(f'No verified section {section}: {url}; audios={audios[:8]}')
        matches=sorted(matches,key=lambda u:0 if 'engnovatemedia.com' in u else 1)
        entries.append(dict(id=f'cam-{book:02}-{test}-{section}',book=book,test=test,section=section,
            title=f'Cambridge IELTS {book} · Test {test} · Section {section}',source='Engnovate',
            source_url=url,audio_url=matches[0],fallback_audio_url=next((u for u in matches[1:] if u!=matches[0]),None),
            indexed_date='2026-11-05'))
    return entries


if __name__=='__main__':
    index='https://engnovate.com/ielts-listening-tests/?category_type=cambridge-academic'
    links=set()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(fetch,index+('&paged_full='+str(p) if p>1 else '')) for p in range(1,8)]
        for future in as_completed(futures):
            links.update(re.findall(r'https://engnovate\.com/ielts-listening-tests/cambridge-ielts-\d+-academic-listening-test-\d+/',future.result()))
    print('FOUND TESTS',len(links),flush=True)
    entries=[]; errors=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(inspect_test,url):url for url in sorted(links)}
        for future in as_completed(futures):
            try:
                items=future.result(); entries.extend(items)
                print('OK',items[0]['book'],items[0]['test'],len(entries),flush=True)
            except Exception as exc:
                errors.append(dict(url=futures[future],error=str(exc)));print('ERROR',str(exc),flush=True)
    entries.sort(key=lambda e:(-e['book'],e['test'],e['section']))
    (ROOT/'web'/'catalog.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),'utf-8')
    (ROOT/'research'/'catalog-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),'utf-8')
    report=dict(books=sorted(set(e['book'] for e in entries)),tests=len(entries)//4,sections=len(entries),errors=errors)
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'catalog-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
