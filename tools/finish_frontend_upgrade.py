from pathlib import Path

root=Path(__file__).resolve().parents[1]
path=root/'web/app.js'
text=path.read_text('utf-8')
start=text.index('function renderReference(){')
end=text.index('async function check()',start)
text=text[:start]+'function renderReference(){return study.renderReference();}\n'+text[end:]
if 'function adjacentIndex(' not in text:
    marker='function wordCount()'
    helpers="""function adjacentIndex(direction){if(!C)return -1;for(let index=I+direction;index>=0&&index<C.segments.length;index+=direction){const candidate=C.segments[index];if((!onlyStars||candidate.starred)&&study.accepts(candidate))return index;}return -1;}
async function navigate(direction){const index=adjacentIndex(direction);if(index>=0)return choose(index);toast('当前筛选中没有更多句子。');}
function updateNavigation(){const left=adjacentIndex(-1)<0,right=adjacentIndex(1)<0;$('prevBtn').disabled=left;$('nextBtn').disabled=right;$('continueBtn').disabled=right;}
"""
    text=text.replace(marker,helpers+marker,1)
    text=text.replace("function renderList(){if(!C)return;","function renderList(){if(!C)return;updateNavigation();",1)
    text=text.replace("bind('prevBtn',()=>choose(I-1))","bind('prevBtn',()=>navigate(-1))")
    text=text.replace("bind('nextBtn',()=>choose(I+1))","bind('nextBtn',()=>navigate(1))")
    text=text.replace("bind('continueBtn',()=>choose(I+1))","bind('continueBtn',()=>navigate(1))")
    text=text.replace('return choose(I+1);','return navigate(1);').replace('return choose(I-1);','return navigate(-1);')
path.write_text(text,'utf-8')
path=root/'web/index.html'
text=path.read_text('utf-8').replace('<em>0.1</em>','<em>0.2</em>')
path.write_text(text,'utf-8')
