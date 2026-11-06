'use strict';
const $ = id => document.getElementById(id);
const ICONS = {
  headphones:'M3 14v-3a9 9 0 0 1 18 0v3M3 13h3v8H4a1 1 0 0 1-1-1zm18 0h-3v8h2a1 1 0 0 0 1-1z',
  studio:'M4 4h16v16H4zM8 8v8m4-6v4m4-7v10', library:'M4 4h4v16H4zm6 0h4v16h-4zm6 1 3-1 4 15-4 1z',
  plus:'M12 5v14M5 12h14', chevronRight:'m9 5 7 7-7 7', upload:'M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5',
  download:'M12 3v13m-5-5 5 5 5-5M4 16v5h16v-5', arrowRight:'M4 12h16m-6-6 6 6-6 6',
  sliders:'M4 6h4m4 0h8M4 12h10m4 0h2M4 18h1m4 0h11M8 3v6m6 0v6m-5 0v6',
  star:'m12 3 2.8 5.7 6.3.9-4.5 4.4 1.1 6.2L12 17.3l-5.7 2.9 1.1-6.2L3 9.6l6.2-.9z',
  previous:'M5 5v14m14-14L8 12l11 7z', next:'M19 5v14M5 5l11 7-11 7z',
  play:'m8 5 11 7-11 7z', pause:'M8 5v14M16 5v14', repeat:'M20 7H6a3 3 0 0 0-3 3v1m13-8 4 4-4 4M4 17h14a3 3 0 0 0 3-3v-1m-13 0-4 4 4 4',
  scissors:'M8 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0zm0 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM8 8l13 12M8 16 21 4',
  checkCircle:'M21 11v1a9 9 0 1 1-5.3-8.2M9 11l3 3L22 4', check:'m5 12 4 4L19 6',
  eyeOff:'m3 3 18 18M10 5h2c5 0 9 7 9 7a17 17 0 0 1-4 4M7 6a20 20 0 0 0-4 6s4 7 9 7a13 13 0 0 0 5-1M10 10a3 3 0 0 0 4 4',
  pencil:'m15 4 5 5M4 20l4-1L21 6l-4-4L4 15z', note:'M14 3H5v18h14V8zM14 3v5h5M8 12h8m-8 4h6',
  keyboard:'M2 5h20v14H2zM6 9h1m3 0h1m3 0h1m3 0h1M6 12h1m3 0h1m3 0h1m3 0h1M7 16h10',
  cloudDownload:'M7 17a6 6 0 1 1 10-7h1a4 4 0 0 1 1 8M12 12v9m-3-3 3 3 3-3',
  x:'m6 6 12 12M6 18 18 6', cpu:'M6 6h12v12H6zM9 9h6v6H9zM9 2v4m6-4v4m-6 12v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4',
  sparkles:'m12 3 2 6 6 3-6 2-2 7-2-7-6-2 6-3zM20 2v4m-2-2h4',
  merge:'M5 3v3c0 4 14 5 14 10v5M19 3v3c0 4-14 5-14 10v5m0-5 7 5 7-5',
  captions:'M3 5h18v14H3zM10 10H7v4h3m7-4h-3v4h3',
};
function icon(name){return `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${ICONS[name]||ICONS.note}"/></svg>`;}
function hydrate(root=document){root.querySelectorAll('[data-icon]').forEach(el=>el.innerHTML=icon(el.dataset.icon));}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function fmt(t,dec=false){t=Math.max(0,t||0);return `${Math.floor(t/60)}:${String(Math.floor(t%60)).padStart(2,'0')}${dec?'.'+String(Math.floor(t%1*10)):''}`;}
const token=document.querySelector('meta[name=juting-token]').content;
let C=null,I=0,library=[],catalog=[],modelReady=false,view='practice',revealed=false,compare=false,loop=false,onlyStars=false;
let playToken=0,loopTimer=null,frame=null,saveTimer=null,saveChain=Promise.resolve(),toastTimer=null,activeJobs=new Map();
let segmentDrafts=new Map();
let activeRange=null,repetitions=0,boundaryTimer=null;
let continuous=false,startingPlayback=false;
let pausedPlayback=null;
const audio=$('audio');
const seg=()=>C?.segments[I];
function toast(message,error=false){clearTimeout(toastTimer);$('toast').textContent=message;$('toast').className='toast'+(error?' error':'');toastTimer=setTimeout(()=>$('toast').classList.add('hidden'),error?9000:4000);}
async function api(path,options={}){let headers={'X-Juting-Token':token,...options.headers};if(options.body&&typeof options.body==='object'&&!(options.body instanceof FormData)){options.body=JSON.stringify(options.body);headers['Content-Type']='application/json';}let r=await fetch('/api'+path,{...options,headers});if(!r.ok){let info;try{info=await r.json();}catch{info={detail:`请求失败（${r.status}）`};}throw Error(typeof info.detail==='string'?info.detail:JSON.stringify(info.detail));}return r.json();}
function action(fn){return async e=>{try{await fn(e);}catch(error){toast(error.message,true);console.error(error);}};}
function bind(id,fn,event='click'){$(id).addEventListener(event,action(fn));}
function showView(next){view=next;stop();$('navPractice').classList.toggle('active',next==='practice');$('navCatalog').classList.toggle('active',next==='catalog');$('catalogView').classList.toggle('hidden',next!=='catalog');$('practiceView').classList.toggle('hidden',next!=='practice'||!C);$('emptyView').classList.toggle('hidden',next!=='practice'||!!C);if(next==='catalog')loadCatalog();else if(C)requestAnimationFrame(drawWave);}
async function loadLibrary(){
  library=await api('/library');
  const visible=library.filter(c=>!/^cam-\d+-\d+-\d+$/.test(c.source_id||''));
  $('libraryCount').textContent=visible.length;
  $('libraryList').innerHTML=visible.length?visible.map(c=>`<button class="library-item ${C?.id===c.id?'active':''}" data-course="${c.id}" title="${esc(c.title)}"><span class="track-icon">${icon('headphones')}</span><span class="item-info"><b>${esc(c.title)}</b><small>${fmt(c.duration)} · ${c.done}/${c.total} 句完成</small></span></button>`).join(''):'<p class="side-empty">导入一段音频，<br>从第一句开始。</p>';
  $('libraryList').querySelectorAll('[data-course]').forEach(el=>el.onclick=action(()=>openCourse(el.dataset.course)));
}
async function openCourse(id,preferred){stop();await flushDraft();C=await api('/courses/'+id);I=Math.min(Math.max(0,preferred??C.current??0),Math.max(0,C.segments.length-1));if(C.audio_cached===false){if(window.confirm('此音频缓存已清理，是否重新下载？听写记录保留。'))watchJob(await api(`/courses/${id}/restore-audio`,{method:'POST'}));return;}audio.src=`/api/courses/${id}/audio`;audio.playbackRate=Number($('speedSelect').value);localStorage.setItem('juting-last',id);revealed=false;compare=false;onlyStars=false;study.reset();segmentDrafts.clear();$('starFilter').classList.remove('on');for(const s of C.segments){try{const draft=JSON.parse(localStorage.getItem('juting-draft-'+C.id+'-'+s.id));if(draft){s.answer=draft.answer;s.note=draft.note;if(draft.practice)s.practice=draft.practice;segmentDrafts.set(s.id,{...draft,course:C.id,id:s.id});}}catch{}}
  if($('skipAnnouncements').checked&&C.segments[I]?.announcement){const first=C.segments.findIndex(x=>!x.announcement);if(first>=0)I=first;}showView('practice');renderCourse();await loadLibrary();if(segmentDrafts.size)toast('已恢复上次未保存的听写。');
}
function renderCourse(){if(!C)return;$('courseTitle').textContent=C.title;$('durationLabel').textContent=`${Math.floor(C.duration/60)} 分 ${Math.round(C.duration%60)} 秒`;$('segmentCount').textContent=C.segments.length+' 个片段';$('sourceLabel').textContent=(C.reference?.kind==='web'?'网上文本 · 已对齐':C.segmentation==='model'?'本地模型 · 按句切分':C.source_url?'在线资料 · 待匹配文本':'本地导入 · 待模型切句');$('recognizeBtn').classList.toggle('hidden',!!C.words?.length);updateProgress();renderSentence();}
function updateProgress(){const done=C.segments.filter(s=>s.done).length,n=C.segments.length;$('doneCount').textContent=done;$('totalCount').textContent=' / '+n;$('percentLabel').textContent=`${n?Math.round(done/n*100):0}%`;$('studyBar').style.width=`${n?done/n*100:0}%`;}
function renderSentence(){const s=seg();renderFavorite();renderPlaybackModes();if(!s){study.renderLanguagePanel();$('sentenceLabel').textContent='未检测到语音';$('answerInput').value='';$('playBtn').disabled=true;$('checkBtn').disabled=true;$('doneBtn').disabled=true;$('boundaryBtn').disabled=true;$('sentenceList').innerHTML='<p class="side-empty">可在切句设置中降低静音阈值，重新检测。</p>';return;}
  for(const id of ['playBtn','checkBtn','doneBtn','boundaryBtn'])$(id).disabled=false;
  $('sentenceNumber').textContent=String(I+1).padStart(2,'0');$('sentenceLabel').textContent=`第 ${I+1} 句 / 共 ${C.segments.length} 句`;$('sentenceTime').textContent=`${fmt(s.start,true)} — ${fmt(s.end,true)} · ${(s.end-s.start).toFixed(1)} 秒`;$('playLength').textContent=fmt(s.end-s.start,true);$('playElapsed').textContent='0:00.0';$('longCut').classList.toggle('hidden',s.reason!=='length');$('answerInput').value=s.answer||'';$('noteInput').value=s.note||'';$('doneBtn').innerHTML=icon('check')+(s.done?'已完成':'标记完成');$('doneBtn').style.color=s.done?'#639a82':'';$('prevBtn').disabled=I===0;$('nextBtn').disabled=I===C.segments.length-1;$('continueBtn').disabled=I===C.segments.length-1;$('saveStatus').innerHTML='<span class="green-dot"></span> 已保存到本地';wordCount();study.render();renderList();requestAnimationFrame(drawWave);}
function renderList(){if(!C)return;updateNavigation();$('sentenceList').innerHTML=C.segments.map((s,i)=>({s,i})).filter(({s})=>(!onlyStars||s.starred)&&study.accepts(s)).map(({s,i})=>`<button class="sentence-item ${i===I?'active':''}" data-index="${i}"><span>${String(i+1).padStart(2,'0')}</span><span><b>第 ${i+1} 句 ${s.starred?'☆':''}${s.practice?.needs_review?'<i class="review-dot" title="待复习"></i>':''}</b><small>${fmt(s.start)} · ${(s.end-s.start).toFixed(1)}s</small></span><span class="status">${s.done?icon('check'):i===I?'•••':''}</span></button>`).join('')||'<p class="side-empty">当前筛选下没有句子。</p>';$('sentenceList').querySelectorAll('[data-index]').forEach(el=>el.onclick=action(()=>choose(Number(el.dataset.index))));$('sentenceList .active')?.scrollIntoView({block:'nearest'});}
async function choose(index,{autoplay=false,autoAdvance=false}={}){
  if(!C||index<0||index>=C.segments.length)return;
  const course=C;
  stop();
  const request=playToken;
  try {
    await flushDraft();
    if(request!==playToken||course!==C||(autoAdvance&&!continuous))return;
    I=index;revealed=false;compare=false;study.reset();C.current=I;
    renderSentence();
    saveChain=saveChain.catch(()=>{}).then(()=>api('/courses/'+course.id,{method:'PATCH',body:{current:index}}));
    await saveChain;
    if(autoplay&&request===playToken&&course===C)await play();
  } catch(error) {
    if(request===playToken)stop();
    throw error;
  }
}
function adjacentIndex(direction,all=false){
  if(!C)return -1;
  for(let index=I+direction;index>=0&&index<C.segments.length;index+=direction){
    const candidate=C.segments[index];
    const eligible=all?(!$('skipAnnouncements').checked||!candidate.announcement):(!onlyStars||candidate.starred)&&study.accepts(candidate);
    if(eligible)return index;
  }
  return -1;
}
async function navigate(direction){const index=adjacentIndex(direction);if(index>=0)return choose(index,{autoplay:true});toast('当前筛选中没有更多句子。');}
function updateNavigation(){const left=adjacentIndex(-1)<0,right=adjacentIndex(1)<0;$('prevBtn').disabled=left;$('nextBtn').disabled=right;$('continueBtn').disabled=right;}
function wordCount(){if(study.mode==='shadow'){$('wordCount').textContent='点词重听';return;}if(study.mode==='cloze'&&seg()?.text){const {plan,answers}=study.clozeState();$('wordCount').textContent=`${plan.selected.filter(i=>answers[i]?.trim()).length} / ${plan.selected.length} 空`;return;}const count=($('answerInput').value.trim().match(/\S+/g)||[]).length;$('wordCount').textContent=count+' '+(count===1?'word':'words');}
function queueDraft(extra={}){if(!seg())return;let s=seg();const answer=$('answerInput').value,note=$('noteInput').value;if(s.answer===answer&&s.note===note&&!segmentDrafts.has(s.id)&&!extra.practice)return;s.answer=answer;s.note=note;let draft={course:C.id,id:s.id,answer:s.answer,note:s.note,practice:JSON.parse(JSON.stringify(s.practice||{}))};segmentDrafts.set(s.id,draft);try{localStorage.setItem('juting-draft-'+C.id+'-'+s.id,JSON.stringify(draft));}catch(error){console.warn('Draft cache unavailable',error);}$('saveStatus').textContent='正在保存…';clearTimeout(saveTimer);saveTimer=setTimeout(()=>flushDraft().catch(()=>{}),400);wordCount();if(!extra.practice)study.onInput();}
async function flushDraft(){clearTimeout(saveTimer);const drafts=Array.from(segmentDrafts.values());segmentDrafts.clear();saveChain=saveChain.catch(()=>{}).then(async()=>{for(const draft of drafts){try{await api(`/courses/${draft.course}/segments/${draft.id}`,{method:'PATCH',body:{answer:draft.answer,note:draft.note,practice:draft.practice},keepalive:true});const key='juting-draft-'+draft.course+'-'+draft.id;if(localStorage.getItem(key)===JSON.stringify(draft))localStorage.removeItem(key);}catch(error){if(!segmentDrafts.has(draft.id))segmentDrafts.set(draft.id,draft);$('saveStatus').textContent='保存失败 · 草稿已暂存';toast('保存失败，已暂存草稿。请保持软件打开并重试。',true);throw error;}}if(!segmentDrafts.size)$('saveStatus').innerHTML='<span class="green-dot"></span> 已保存到本地';});return saveChain;}
window.jutingFlush=()=>{queueDraft();flushDraft().catch(()=>{});return true;};
function renderPlaybackButtons(label='播放这句'){
  const playing=startingPlayback||!audio.paused;
  $('playBtn').innerHTML=icon(playing?'pause':'play')+`<b>${playing?'暂停播放':pausedPlayback?'继续播放':label}</b>`;
}
function renderPlaybackModes(){
  $('continuousBtn').disabled=!seg();
  $('continuousBtn').classList.toggle('on',continuous);
  $('continuousBtn').setAttribute('aria-pressed',String(continuous));
  $('loopBtn').classList.toggle('on',loop);
  $('loopBtn').setAttribute('aria-pressed',String(loop));
  $('loopBtn').disabled=continuous||!seg();
  $('loopBtn').title=continuous?'关闭连播后可开启单句循环':'单句循环';
}
function stop(){
  playToken++;
  clearTimeout(loopTimer);clearTimeout(boundaryTimer);cancelAnimationFrame(frame);
  audio.pause();activeRange=null;startingPlayback=false;pausedPlayback=null;
  renderPlaybackButtons();
  if(C)drawWave();
}
function pausePlayback(){
  const sentence=seg();
  const resume=sentence?{
    sentence,
    kind:activeRange?.kind||'sentence',
    end:activeRange?.end??sentence.end,
    repetitions:repetitions||1,
  }:null;
  stop();
  pausedPlayback=resume;
  renderPlaybackButtons();
}
function resumePlayback(){
  const resume=pausedPlayback;
  if(!resume||resume.sentence!==seg())return play();
  return play(audio.currentTime,{kind:resume.kind,end:resume.end,resume});
}
function togglePlayback(){
  return startingPlayback||!audio.paused?pausePlayback():resumePlayback();
}
function toggleContinuous(){
  if(!seg())return;
  continuous=!continuous;
  if(continuous){loop=false;clearTimeout(loopTimer);}
  renderPlaybackModes();
}
function toggleLoop(){
  if(continuous||!seg())return;
  loop=!loop;
  if(!loop)clearTimeout(loopTimer);
  renderPlaybackModes();
}
function waitForAudio(){
  if(audio.readyState>0)return Promise.resolve();
  return new Promise((resolve,reject)=>{
    const cleanup=()=>{clearTimeout(timer);audio.removeEventListener('loadedmetadata',ready);audio.removeEventListener('error',failed);};
    const ready=()=>{cleanup();resolve();};
    const failed=()=>{cleanup();reject(Error('无法读取音频，请重新打开这份练习。'));};
    const timer=setTimeout(failed,15000);
    audio.addEventListener('loadedmetadata',ready,{once:true});
    audio.addEventListener('error',failed,{once:true});
    // The source assignment already starts loading. Calling load() again would cancel a pending play.
  });
}
async function play(start,options={}){
  const s=seg();
  if(!s)return;
  if(C.audio_cached===false){await openCourse(C.id);return;}
  const kind=options.kind||'sentence';
  if($('skipAnnouncements').checked&&s.announcement){
    const next=adjacentIndex(1,continuous);
    if(next>=0)return choose(next,{autoplay:true});
    stop();return;
  }
  const count=options.resume?.repetitions??(options.continue?repetitions+1:1);
  stop();
  startingPlayback=true;repetitions=count;
  renderPlaybackButtons();
  const request=playToken;
  try {
    await waitForAudio();
    if(request!==playToken)return;
    activeRange={end:Math.min(s.end,options.end??s.end),kind,finished:false};
    const position=Math.max(s.start,Math.min(start??s.start,activeRange.end));
    if(audio.currentTime!==position)audio.currentTime=position;
    audio.playbackRate=Number($('speedSelect').value);
    audio.preservesPitch=true;
    await audio.play();
    if(request!==playToken)return;
    startingPlayback=false;
    renderPlaybackButtons();
    if(!options.resume)study.onPlayed();
    tick(request);
  } catch(error) {
    if(request!==playToken)return;
    stop();throw error;
  }
}
function scheduleBoundary(myToken){clearTimeout(boundaryTimer);if(myToken!==playToken||!activeRange||activeRange.finished||audio.paused)return;const remaining=activeRange.end-audio.currentTime;if(remaining<=.012){finishSentence(myToken);return;}boundaryTimer=setTimeout(()=>scheduleBoundary(myToken),Math.max(8,(remaining/Math.max(.1,audio.playbackRate))*1000-8));}
function finishSentence(myToken){
  if(myToken!==playToken||!activeRange||activeRange.finished)return;
  activeRange.finished=true;audio.pause();
  if(audio.currentTime>=activeRange.end-.03)audio.currentTime=activeRange.end;
  clearTimeout(boundaryTimer);cancelAnimationFrame(frame);study.highlight(-1);
  $('playElapsed').textContent=fmt(audio.currentTime-seg().start,true);
  if(continuous&&activeRange.kind==='sentence'){
    const next=adjacentIndex(1,true);
    if(next>=0){choose(next,{autoplay:true,autoAdvance:true}).catch(e=>toast(e.message,true));return;}
  }else if(loop&&activeRange.kind==='sentence'&&(!study.repeatLimit||repetitions<study.repeatLimit)){
    loopTimer=setTimeout(()=>{if(myToken===playToken)play(undefined,{continue:true}).catch(e=>toast(e.message,true));},study.interval*1000);
  }
  renderPlaybackButtons('再听一遍');drawWave();
}
function tick(myToken){if(myToken!==playToken)return;const s=seg();if(!s||!activeRange)return;if(audio.currentTime>=activeRange.end-.015){audio.currentTime=activeRange.end;finishSentence(myToken);return;}$('playElapsed').textContent=fmt(audio.currentTime-s.start,true);study.highlight(audio.currentTime);drawWave();if(!audio.paused)frame=requestAnimationFrame(()=>tick(myToken));}
audio.addEventListener('timeupdate',()=>{if(seg()&&activeRange&&!audio.paused&&audio.currentTime>=activeRange.end-.015)finishSentence(playToken);});audio.addEventListener('ended',()=>finishSentence(playToken));audio.addEventListener('error',()=>{if(audio.src)toast('播放失败：请重新打开这份练习。',true);});
audio.addEventListener('playing',()=>scheduleBoundary(playToken));audio.addEventListener('ratechange',()=>scheduleBoundary(playToken));audio.addEventListener('seeked',()=>scheduleBoundary(playToken));
function drawWave(){const canvas=$('waveform'),s=seg();if(!s||!canvas.clientWidth)return;let dpr=window.devicePixelRatio||1,w=canvas.clientWidth,h=canvas.clientHeight;canvas.width=w*dpr;canvas.height=h*dpr;const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);const peaks=C.peaks||[],count=Math.floor(w/5),p=Math.max(0,Math.min(1,(audio.currentTime-s.start)/(s.end-s.start)));let local=[];for(let i=0;i<count;i++){let t=s.start+(s.end-s.start)*(i+.5)/count;local.push(peaks[Math.min(peaks.length-1,Math.floor(t/C.duration*peaks.length))]||.01);}const max=Math.max(.02,...local);ctx.fillStyle='#f9f8fd';ctx.fillRect(0,0,w,h);for(let i=0;i<count;i++){const v=Math.max(3,Math.pow(local[i]/max,.65)*(h-12));ctx.fillStyle=i/count<p?'#8979cc':'#dbd5ed';ctx.beginPath();ctx.roundRect(i*5+1,(h-v)/2,2.5,v,2);ctx.fill();}const x=p*w;ctx.fillStyle='#a28cd0';ctx.fillRect(x,4,1,h-8);canvas.setAttribute('aria-valuenow',Math.round(p*100));}
function tokenize(s){return s.replace(/[’‘]/g,"'").toLowerCase().match(/[a-z0-9]+(?:'[a-z0-9]+)*/g)||[];}
function diffWords(reference,answer){const refs=reference.match(/\S+/g)||[];const r=refs.map(w=>tokenize(w).join('')),a=(answer.match(/\S+/g)||[]).map(w=>({raw:w,key:tokenize(w).join('')})).filter(w=>w.key);const clean=refs.map((raw,i)=>({raw,key:r[i]})).filter(w=>w.key);let n=clean.length,m=a.length;if(n*m>200000)return {html:esc(reference),extra:[],score:null};const dp=Array.from({length:n+1},()=>new Uint16Array(m+1));for(let i=0;i<=n;i++)dp[i][0]=i;for(let j=0;j<=m;j++)dp[0][j]=j;for(let i=1;i<=n;i++)for(let j=1;j<=m;j++)dp[i][j]=Math.min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+(clean[i-1].key===a[j-1].key?0:1));let out=[],extra=[],i=n,j=m;while(i||j){if(i&&j&&dp[i][j]===dp[i-1][j-1]+(clean[i-1].key===a[j-1].key?0:1)){const same=clean[i-1].key===a[j-1].key;out.unshift(`<span class="diff-word ${same?'correct':'wrong'}" ${same?'':`title="你写的是：${esc(a[j-1].raw)}"`}>${esc(clean[i-1].raw)}</span>`);i--;j--;}else if(i&&dp[i][j]===dp[i-1][j]+1){out.unshift(`<span class="diff-word missed" title="漏听的词">${esc(clean[i-1].raw)}</span>`);i--;}else{extra.unshift(a[j-1].raw);j--;}}return {html:out.join(' '),extra,score:n?Math.max(0,Math.round((1-dp[n][m]/n)*100)):0};}
function renderReference(){return study.renderReference();}
async function check(){return study.check();}
function renderFavorite(){
  const sentence=seg(),starred=Boolean(sentence?.starred);
  const top=$('starBtn'),favorite=$('favoriteBtn');
  for(const button of [top,favorite]){
    button.disabled=!sentence;
    button.classList.toggle('starred',starred);
    button.setAttribute('aria-pressed',String(starred));
  }
  top.title=starred?'取消收藏':'收藏这句';
  top.setAttribute('aria-label',top.title);
  favorite.innerHTML=icon('star')+(starred?'已收藏':'收藏这句');
}
async function toggleFavorite(){
  const sentence=seg(),course=C;
  if(!sentence)return;
  const starred=!sentence.starred;
  await api(`/courses/${course.id}/segments/${sentence.id}`,{method:'PATCH',body:{starred}});
  sentence.starred=starred;
  if(C===course){renderFavorite();renderList();}
}
async function toggleDone(){if(!seg())return;await flushDraft();const value=!seg().done;await api(`/courses/${C.id}/segments/${seg().id}`,{method:'PATCH',body:{done:value}});seg().done=value;$('doneBtn').innerHTML=icon('check')+(value?'已完成':'标记完成');$('doneBtn').style.color=value?'#639a82':'';updateProgress();renderList();await loadLibrary();}
async function status(){let s=await api('/status');modelReady=s.model_ready;$('modelLabel').textContent=modelReady?'已就绪':'未下载';$('modelBadge').textContent=modelReady?'已就绪':'未下载';$('downloadModelBtn').disabled=modelReady;$('downloadModelBtn').textContent=modelReady?'模型已就绪':'下载英语模型';for(const job of s.jobs)if(!activeJobs.has(job.id))watchJob(job);return s;}
async function watchJob(job){if(job.status==='done'&&job.result?.course_id){await openCourse(job.result.course_id);return;}if(!job.id||activeJobs.has(job.id))return;activeJobs.set(job.id,job);renderJobBanner();let last=job;try{while(true){await new Promise(r=>setTimeout(r,850));last=await api('/jobs/'+job.id);activeJobs.set(job.id,last);renderJobBanner();if(last.status==='done'||last.status==='error')break;}if(last.status==='error')throw Error(last.message);await status();if(last.kind==='asr'){if(C?.id===last.course_id){stop();const oldI=I;const oldReveal=revealed;await flushDraft();C=await api('/courses/'+C.id);I=Math.min(oldI,C.segments.length-1);revealed=oldReveal;renderCourse();}await loadLibrary();toast(C?.transcript_warning||C?.reference?.warning||'文本与句子时间已更新。');}else if(last.result?.course_id){await loadLibrary();await openCourse(last.result.course_id);if(last.kind!=='restore'&&modelReady&&$('autoAsr').checked){toast('切句完成，可以先听写；参考原文正在后台识别。');await startTranscribe();}else toast('切句完成，可以开始逐句听写。');}else toast('本地英语模型已就绪。');}catch(error){toast(error.message,true);}finally{activeJobs.delete(job.id);renderJobBanner();if(view==='catalog')renderCatalog();}}
function renderJobBanner(){const jobs=Array.from(activeJobs.values()).filter(j=>!['done','error'].includes(j.status));$('jobBanner').classList.toggle('hidden',!jobs.length);if(!jobs.length)return;const j=jobs.find(j=>j.status==='running')||jobs[0];$('jobMessage').textContent=j.message+(jobs.length>1?` · 另有 ${jobs.length-1} 个任务`:'');$('jobProgress').style.width=j.progress+'%';$('jobPercent').textContent=Math.round(j.progress)+'%';}
async function importFile(file){if(!file)return;await flushDraft();const form=new FormData();form.append('file',file);toast('正在导入 '+file.name);const job=await api('/import',{method:'POST',body:form});watchJob(job);}
function openSettings(){if(C){$('pauseRange').value=C.split.pause;$('thresholdSelect').value=C.split.threshold_db;$('maxSelect').value=C.split.max_length;}$('pauseValue').textContent=Number($('pauseRange').value).toFixed(2)+' 秒';$('resplitBtn').disabled=!C;$('transcribeBtn').disabled=!C;$('settingsDialog').showModal();status();}
async function startTranscribe(){if(!C)return;await flushDraft();if(!modelReady&&!C.words?.length){openSettings();toast('先下载本地英语模型，再生成参考原文。');return;}if(C.words?.length&&!window.confirm('重新匹配文本并按句切分？原记录自动备份，迁移过的输入标记为待复习；人工校正的分句保留。'))return;if($('settingsDialog').open)$('settingsDialog').close();const job=await api(`/courses/${C.id}/transcribe`,{method:'POST'});watchJob(job);}
async function loadCatalog(){catalog=await api('/catalog');const old=$('bookSelect').value;const books=[...new Set(catalog.filter(e=>e.book).map(e=>e.book))].sort((a,b)=>b-a);$('bookSelect').innerHTML='<option value="all">全部册数</option>'+books.map(b=>`<option value="${b}">剑桥 IELTS ${b}</option>`).join('')+(catalog.some(e=>!e.book)?'<option value="engexam">EngExam 练习</option>':'');if([...$('bookSelect').options].some(o=>o.value===old))$('bookSelect').value=old;else $('bookSelect').value=books[0]||'all';renderCatalog();}
function renderCatalog(){const book=$('bookSelect').value,query=$('catalogSearch').value.toLowerCase().trim();const items=catalog.filter(e=>(book==='all'||book==='engexam'&&!e.book||String(e.book)===book)&&(!query||e.title.toLowerCase().includes(query)||`${e.book} ${e.test} ${e.section}`.includes(query)));$('catalogCount').textContent=items.length+' 段音频';$('catalogNotice').textContent=catalog.length?`已收录 ${[...new Set(catalog.filter(e=>e.book).map(e=>e.book))].length} 册的公开音源。按册号和 Test / Section 选择，点击后下载；优先匹配网上文本，无可用文本时使用本地识别；首次定位时间仍需本地模型。`:'正在核对资料来源，暂时可以导入你自己的音频。';$('catalogGrid').innerHTML=items.map(e=>`<article class="catalog-card" data-test="${Number(e.test)}"><div class="book-cover">${e.book||'E'}</div><div class="catalog-details"><h3>${e.book?'剑桥 IELTS '+e.book:'EngExam'}</h3><p>Test ${e.test}${e.section?' · Section '+e.section:' · 完整音频'}</p><div class="catalog-actions"><button data-download="${e.id}">${icon(e.course_id?'play':'cloudDownload')}${e.course_id?'继续练习':'下载并切句'}</button><a href="${esc(e.source_url)}" target="_blank" rel="noreferrer">来源 ↗</a></div></div></article>`).join('')||'<p class="muted small">没有匹配的音频。</p>';$('catalogGrid').querySelectorAll('[data-download]').forEach(btn=>btn.onclick=action(async()=>{const e=catalog.find(x=>x.id===btn.dataset.download);if(e.course_id)return openCourse(e.course_id);btn.disabled=true;btn.textContent='正在准备…';try{const job=await api('/catalog/'+e.id+'/download',{method:'POST'});watchJob(job);}finally{btn.disabled=false;btn.innerHTML=icon('cloudDownload')+'下载并切句';}}));}
async function boundary(actionName,extra={}){await flushDraft();stop();const id=seg().id;C=await api(`/courses/${C.id}/edit-boundary`,{method:'POST',body:{segment_id:id,action:actionName,...extra}});I=C.segments.findIndex(s=>s.id===id);revealed=false;$('boundaryDialog').close();renderCourse();loadLibrary();toast('已调整，原记录已自动备份。');}
bind('navPractice',()=>showView('practice'));bind('navCatalog',()=>showView('catalog'));bind('emptyCatalog',()=>showView('catalog'));
for(const id of ['importBtn','emptyImport'])bind(id,()=>$('fileInput').click());bind('fileInput',e=>{const file=e.target.files[0];e.target.value='';return importFile(file);},'change');
bind('settingsBtn',openSettings);bind('modelBtn',openSettings);bind('pauseRange',()=>$('pauseValue').textContent=Number($('pauseRange').value).toFixed(2)+' 秒','input');
bind('playBtn',togglePlayback);bind('continuousBtn',toggleContinuous);bind('prevBtn',()=>navigate(-1));bind('nextBtn',()=>navigate(1));bind('continueBtn',()=>navigate(1));bind('checkBtn',check);bind('doneBtn',toggleDone);
bind('loopBtn',toggleLoop);bind('speedSelect',()=>{audio.playbackRate=Number($('speedSelect').value);localStorage.setItem('juting-speed',$('speedSelect').value);},'change');
bind('starBtn',toggleFavorite);bind('favoriteBtn',toggleFavorite);bind('starFilter',()=>{onlyStars=!onlyStars;$('starFilter').classList.toggle('on',onlyStars);renderList();});
bind('answerInput',queueDraft,'input');bind('noteInput',queueDraft,'input');bind('waveform',e=>{if(!seg())return;const box=$('waveform').getBoundingClientRect();const at=seg().start+Math.max(0,Math.min(1,(e.clientX-box.left)/box.width))*(seg().end-seg().start);if(audio.paused){audio.currentTime=at;drawWave();$('playElapsed').textContent=fmt(at-seg().start,true);}else return play(at);});
bind('waveform',e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)&&seg()){e.preventDefault();audio.currentTime=Math.max(seg().start,Math.min(seg().end,audio.currentTime+(e.key==='ArrowLeft'?-.25:.25)));drawWave();}},'keydown');
bind('downloadModelBtn',async()=>{const job=await api('/model/download',{method:'POST'});$('settingsDialog').close();watchJob(job);});bind('transcribeBtn',startTranscribe);
bind('recognizeBtn',startTranscribe);bind('autoAsr',()=>localStorage.setItem('juting-auto-asr',String($('autoAsr').checked)),'change');
bind('resplitBtn',async()=>{if(!C)return;await flushDraft();if(!window.confirm('重新切句会重置这份音频的听写、笔记和完成状态。原记录会自动备份到本地。确定继续吗？'))return;stop();C=await api(`/courses/${C.id}/resplit`,{method:'POST',body:{pause:Number($('pauseRange').value),threshold_db:Number($('thresholdSelect').value),max_length:Number($('maxSelect').value)}});I=0;revealed=false;$('settingsDialog').close();renderCourse();await loadLibrary();toast('重新切句完成。');});
bind('boundaryBtn',()=>{if(!seg())return;stop();$('startInput').value=seg().start;$('endInput').value=seg().end;const at=Math.max(seg().start,Math.min(seg().end,audio.currentTime));$('splitAtLabel').textContent=at.toFixed(2)+'s';$('splitHereBtn').dataset.at=at;$('mergeBtn').disabled=I===C.segments.length-1;$('boundaryDialog').showModal();});bind('trimBtn',()=>boundary('trim',{start:Number($('startInput').value),end:Number($('endInput').value)}));bind('splitHereBtn',()=>boundary('split',{at:Number($('splitHereBtn').dataset.at)}));bind('mergeBtn',()=>boundary('merge'));
bind('editTextBtn',()=>{$('editText').value=seg().text;$('editDialog').showModal();});bind('saveTextBtn',async()=>{const text=$('editText').value.trim();await api(`/courses/${C.id}/segments/${seg().id}`,{method:'PATCH',body:{text}});seg().text=text;seg().text_source='manual';$('editDialog').close();renderReference();toast('参考原文已校正。');});
bind('exportBtn',async()=>{await flushDraft();$('exportDialog').showModal();});document.querySelectorAll('[data-export]').forEach(btn=>btn.onclick=action(async()=>{await flushDraft();const kind=btn.dataset.export;const response=await fetch(`/api/courses/${C.id}/export/${kind}`);if(!response.ok)throw Error('导出失败，请重试。');const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=C.title.replace(/[<>:"/\\|?*]/g,'-')+'.'+kind;link.click();setTimeout(()=>URL.revokeObjectURL(url),5000);$('exportDialog').close();toast('已生成导出文件。');}));
bind('skipAnnouncements',async()=>{localStorage.setItem('juting-skip-announcements',String($('skipAnnouncements').checked));if(C&&seg()?.announcement&&$('skipAnnouncements').checked){const next=adjacentIndex(1);if(next>=0)await choose(next);}renderList();},'change');
bind('practiceScope',async()=>{localStorage.setItem('juting-scope',$('practiceScope').value);if(C&&!study.accepts(seg())){const first=C.segments.findIndex(x=>study.accepts(x));if(first>=0)await choose(first);else toast('当前范围没有匹配句子。');}renderList();},'change');
async function showCache(){const info=await api('/cache');$('cacheSummary').textContent=`在线音频 ${(info.download_bytes/1048576).toFixed(1)} MiB；过期临时文件 ${(info.temporary_bytes/1048576).toFixed(1)} MiB`;$('cacheDialog').showModal();}
bind('cacheBtn',()=>{$('settingsDialog').close();return showCache();});
async function clearCache(downloads){await flushDraft();stop();if(downloads&&!window.confirm('清理所有在线音频缓存？下次练习需重新下载，听写和笔记保留。'))return;if(downloads){audio.removeAttribute('src');audio.load();}const result=await api('/cache/clear',{method:'POST',body:{downloads}});toast(`已释放 ${(result.removed_bytes/1048576).toFixed(1)} MiB`);await showCache();if(downloads&&C?.source_id)C.audio_cached=false;}
bind('clearTempBtn',()=>clearCache(false));bind('clearAudioBtn',()=>clearCache(true));
bind('bookSelect',renderCatalog,'change');bind('catalogSearch',renderCatalog,'input');
document.addEventListener('keydown',action(async e=>{if(document.querySelector('dialog[open]')||e.isComposing)return;const typing=['TEXTAREA','INPUT','SELECT'].includes(document.activeElement?.tagName);if(e.key==='F4'||(e.ctrlKey&&e.code==='Space')){e.preventDefault();return play();}if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();return check();}if(e.altKey&&e.key==='ArrowRight'){e.preventDefault();return navigate(1);}if(e.altKey&&e.key==='ArrowLeft'){e.preventDefault();return navigate(-1);}if(e.code==='Space'&&!typing&&view==='practice'){e.preventDefault();return togglePlayback();}}));
window.addEventListener('resize',drawWave);window.addEventListener('beforeunload',()=>{if(seg())queueDraft();flushDraft().catch(()=>{});});
document.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('Files'))e.preventDefault();});document.addEventListener('drop',action(e=>{if(e.dataTransfer.files.length){e.preventDefault();return importFile(e.dataTransfer.files[0]);}}));
hydrate();
const study=new StudyController({segment:seg,course:()=>C,flush:flushDraft,queue:queueDraft,stop,play,render:renderSentence,list:renderList,isRevealed:()=>revealed,setRevealed:value=>{revealed=value;}});
(async()=>{try{$('skipAnnouncements').checked=localStorage.getItem('juting-skip-announcements')!=='false';$('practiceScope').value=localStorage.getItem('juting-scope')||'all';$('autoAsr').checked=localStorage.getItem('juting-auto-asr')!=='false';const speed=localStorage.getItem('juting-speed');if(speed&&[...$('speedSelect').options].some(o=>o.value===speed))$('speedSelect').value=speed;await status();await loadLibrary();const last=localStorage.getItem('juting-last');if(library.length)await openCourse(library.some(c=>c.id===last)?last:library[0].id);else showView('practice');}catch(error){toast(error.message,true);}})();
