/* Practice controls built from observed public-site interaction patterns. */
class StudyController {
  constructor(host){
    this.host=host;this.mode=localStorage.getItem('juting-mode')||'dictation';if(!['dictation','cloze','shadow'].includes(this.mode))this.mode='dictation';
    this.percent=Number(localStorage.getItem('juting-cloze-percent'))||30;this.checked=false;this.hinted=new Set();this.helpUsed=0;this.filter='all';
    this.interval=Number(localStorage.getItem('juting-loop-gap'))||1.5;this.repeatLimit=Number(localStorage.getItem('juting-loop-count'))||0;
    this.insertControls();this.bind();
  }
  get s(){return this.host.segment();} get c(){return this.host.course();}
  get practice(){if(!this.s)return {};return this.s.practice||(this.s.practice={});}
  insertControls(){
    document.querySelector('.study-progress').insertAdjacentHTML('afterend',`<div class="practice-toolbar"><div class="mode-tabs" role="tablist" aria-label="练习模式"><button data-mode="dictation" role="tab">逐句听写</button><button data-mode="cloze" role="tab">重点填空</button><button data-mode="shadow" role="tab">听读跟读</button></div><div id="clozeDifficulty" class="cloze-difficulty hidden"><label for="clozePercent">隐藏比例</label><select id="clozePercent"><option value="20">20%</option><option value="30">30%</option><option value="50">50%</option><option value="75">75%</option><option value="100">100%</option></select></div><button id="rhythmBtn" class="text-button">${icon('sliders')}播放节奏</button></div>`);
    $('answerInput').insertAdjacentHTML('afterend','<div id="clozeInput" class="cloze-input hidden" aria-label="填空练习"></div><div id="shadowInput" class="shadow-input hidden"></div>');
    $('checkBtn').insertAdjacentHTML('afterend',`<button id="wordHintBtn" class="secondary">提示一词</button><button id="revealBtn" class="text-button">显示原文</button>`);
    $('referenceCard').insertAdjacentHTML('beforebegin','<div id="practiceFeedback" class="practice-feedback hidden" role="status" aria-live="polite"></div>');
    document.querySelector('.sentence-panel>p').insertAdjacentHTML('afterend','<select id="sentenceFilter" aria-label="句子筛选"><option value="all">全部句子</option><option value="unfinished">未完成</option><option value="review">待复习</option><option value="starred">已收藏</option></select>');
    document.querySelector('.sentence-heading').insertAdjacentHTML('afterend','<div class="listening-detail"><span id="playCount">本句重听 0 次</span><span id="practiceBadge"></span></div>');
    document.body.insertAdjacentHTML('beforeend',`<dialog id="rhythmDialog"><form method="dialog" class="dialog-header"><h2>播放节奏</h2><button class="icon-button" aria-label="关闭">${icon('x')}</button></form><div class="dialog-body"><p class="small muted">开启播放器的「循环」后，按照这里的次数和间隔重播。每句听完仍由你决定何时继续。</p><div class="setting-row"><label>单句播放次数<select id="repeatCount"><option value="0">一直循环</option><option value="2">2 次</option><option value="3">3 次</option><option value="5">5 次</option></select></label><label>两次之间停顿<select id="repeatGap"><option value="0.5">0.5 秒</option><option value="1">1 秒</option><option value="1.5">1.5 秒</option><option value="2">2 秒</option><option value="3">3 秒</option><option value="5">5 秒</option></select></label></div><div class="rhythm-tip">跟读时可以增加停顿，在重播前自己复述。F4 重播 · Ctrl + Enter 检查 · Alt + ← / → 切句</div></div></dialog>`);
    $('clozePercent').value=String(this.percent);$('repeatCount').value=String(this.repeatLimit);$('repeatGap').value=String(this.interval);
  }
  bind(){
    document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',action(()=>this.changeMode(button.dataset.mode))));
    bind('wordHintBtn',()=>this.hint());bind('revealBtn',()=>this.reveal());
    bind('clozePercent',async()=>{await this.host.flush();this.percent=Number($('clozePercent').value);localStorage.setItem('juting-cloze-percent',this.percent);this.checked=false;this.hinted.clear();this.render();},'change');
    bind('sentenceFilter',()=>{this.filter=$('sentenceFilter').value;this.host.list();},'change');
    bind('rhythmBtn',()=>$('rhythmDialog').showModal());
    bind('repeatGap',()=>{this.interval=Number($('repeatGap').value);localStorage.setItem('juting-loop-gap',this.interval);},'change');
    bind('repeatCount',()=>{this.repeatLimit=Number($('repeatCount').value);localStorage.setItem('juting-loop-count',this.repeatLimit);},'change');
  }
  async changeMode(mode){if(mode===this.mode)return;await this.host.flush();this.host.stop();this.mode=mode;localStorage.setItem('juting-mode',mode);this.reset();this.host.render();}
  reset(){this.checked=false;this.hinted.clear();this.helpUsed=0;$('practiceFeedback').classList.add('hidden');}
  accepts(s){if($('skipAnnouncements')?.checked&&s.announcement)return false;const scope=$('practiceScope')?.value;if(scope==='key'&&!s.practice?.needs_review&&(s.text.match(/\S+/g)||[]).length<12)return false;if(scope==='sample'&&this.host.course().segments.indexOf(s)%3!==0&&!s.practice?.needs_review)return false;return this.filter==='all'||this.filter==='unfinished'&&!s.done||this.filter==='review'&&s.practice?.needs_review||this.filter==='starred'&&s.starred;}
  render(){
    const s=this.s;if(!s)return;
    document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.mode===this.mode);b.setAttribute('aria-selected',String(b.dataset.mode===this.mode));});
    $('clozeDifficulty').classList.toggle('hidden',this.mode!=='cloze');$('answerInput').classList.toggle('hidden',this.mode!=='dictation');$('clozeInput').classList.toggle('hidden',this.mode!=='cloze');$('shadowInput').classList.toggle('hidden',this.mode!=='shadow');
    $('wordHintBtn').classList.toggle('hidden',this.mode==='shadow');$('checkBtn').classList.toggle('hidden',this.mode==='shadow');$('revealBtn').classList.toggle('hidden',this.mode==='shadow');$('referenceCard').classList.toggle('hidden',this.mode==='shadow');
    document.querySelector('label[for=answerInput]').innerHTML='<em>02</em> '+({dictation:'写下你听到的',cloze:'补全听到的词',shadow:'听一句，再跟着复述'}[this.mode]);
    $('playCount').textContent=`本句重听 ${this.practice.plays||0} 次`;$('practiceBadge').textContent=this.practice.needs_review?'待复习':'';
    if(this.mode==='cloze')this.renderCloze();else if(this.mode==='shadow')this.renderShadow();
    this.renderReference();
  }
  clozeState(){
    const plan=PracticeCore.cloze(this.s.text,this.percent),practice=this.practice;
    if(!practice.cloze_sets)practice.cloze_sets={};
    return {plan,answers:practice.cloze_sets[plan.signature]||(practice.cloze_sets[plan.signature]={})};
  }
  renderCloze(){
    const target=$('clozeInput');if(!this.s.text){target.innerHTML='<p class="practice-unavailable">参考原文还没有生成。你可以先逐句听写，或点击右上角生成原文。</p>';return;}
    const {plan,answers}=this.clozeState();const selected=new Set(plan.selected);
    target.innerHTML=plan.words.map((word,index)=>selected.has(index)?`<span class="cloze-slot"><input aria-label="第 ${index+1} 个词" data-cloze="${index}" value="${esc(answers[index]||'')}" autocomplete="off" spellcheck="false" style="--letters:${Math.max(5,Math.min(16,PracticeCore.normalize(word).length+1))}" class="${this.checked?(PracticeCore.normalize(answers[index])===PracticeCore.normalize(word)?'slot-correct':'slot-wrong'):''}"></span>`:`<span class="cloze-given">${esc(word)}</span>`).join(' ');
    target.querySelectorAll('[data-cloze]').forEach(input=>{input.addEventListener('input',()=>{answers[input.dataset.cloze]=input.value;input.classList.remove('slot-correct','slot-wrong');this.onInput();this.host.queue({practice:true});});input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.ctrlKey){event.preventDefault();const fields=[...target.querySelectorAll('input')],i=fields.indexOf(input);fields[i+1]?.focus();}});});
  }
  renderShadow(){
    if(!this.s.text){$('shadowInput').innerHTML='<p class="practice-unavailable">生成参考原文后，可以使用点词重听与同步跟读。</p>';return;}
    $('shadowInput').innerHTML='<p class="shadow-guide">听清楚 → 自己复述 → 点词重听。可在「播放节奏」中留出跟读时间。</p><div class="shadow-script">'+this.wordButtons(PracticeCore.tokens(this.s.text).map(()=> 'correct'),true)+'</div><div class="shadow-footer">基于本地音频回放，不使用在线语音评分。</div>';
    this.bindWordButtons($('shadowInput'));
  }
  result(){
    if(this.mode==='cloze'){
      const {plan,answers}=this.clozeState(),statuses=plan.words.map(()=> 'given');let correct=0;
      for(const index of plan.selected){const ok=PracticeCore.normalize(answers[index])===PracticeCore.normalize(plan.words[index]);statuses[index]=ok?'correct':'missing';if(ok)correct++;}
      return {score:Math.round(correct/Math.max(1,plan.selected.length)*100),correct:correct===plan.selected.length,statuses,firstIssue:statuses.findIndex(s=>s==='missing'),extra:0};
    }
    return PracticeCore.evaluate(this.s.text,this.s.answer);
  }
  async check(){
    if(!this.s||this.mode==='shadow')return;await this.host.flush();if(!this.s.text){toast('先生成参考原文，才能检查输入。');return;}
    const result=this.result();this.checked=true;this.practice.checks=(this.practice.checks||0)+1;this.practice.last_score=result.score;
    if(!result.correct||this.helpUsed)this.practice.needs_review=true;else if(this.mode==='dictation')this.practice.needs_review=false;
    this.host.setRevealed(false);this.host.queue({practice:true});this.feedback(result);if(this.mode==='cloze')this.renderCloze();this.renderReference();this.host.list();$('practiceBadge').textContent=this.practice.needs_review?'待复习':'';$('referenceCard').scrollIntoView({block:'nearest',behavior:'smooth'});
  }
  feedback(result){
    const el=$('practiceFeedback');el.className='practice-feedback '+(result.correct?'is-correct':'needs-work');
    const message=result.correct?(this.helpUsed?'这句已补全，可以再脱离提示听写一次。':'这句写对了，试着跟读一遍。'):`还有 ${result.statuses.filter(s=>['wrong','missing'].includes(s)).length} 处需要再听${result.extra?'，另多写了 '+result.extra+' 个词':''}。答案仍然隐藏，可以先提示一个词。`;
    el.innerHTML=icon(result.correct?'checkCircle':'headphones')+`<span>${message}</span><b>${result.score===null?'':result.score+'%'}</b>`;
  }
  async hint(){
    if(!this.s?.text){toast('请先生成参考原文。');return;}await this.host.flush();
    const result=this.result();let index=result.statuses.findIndex((s,i)=>['wrong','missing','unknown'].includes(s)&&!this.hinted.has(i));
    if(index<0){toast('当前没有新的提示词，可以检查输入或显示原文。');return;}
    this.hinted.add(index);this.helpUsed++;this.practice.hints=(this.practice.hints||0)+1;this.practice.needs_review=true;
    this.host.setRevealed(false);this.host.queue({practice:true});this.renderReference();this.host.list();$('practiceBadge').textContent='待复习';$('referenceCard').scrollIntoView({block:'nearest',behavior:'smooth'});
  }
  async reveal(){if(!this.s)return;await this.host.flush();this.host.setRevealed(!this.host.isRevealed());this.renderReference();}
  wordButtons(statuses,all=false){
    const words=PracticeCore.tokens(this.s.text),ranges=PracticeCore.alignTimedWords(this.s,this.c.words||[]);
    return words.map((word,index)=>{
      const status=statuses[index]||'unknown',visible=all||status==='correct'||status==='given'||this.hinted.has(index);
      if(!visible)return `<span class="masked-word ${status}" aria-label="第 ${index+1} 个词待听写">${PracticeCore.mask(word)}</span>`;
      const timed=ranges[index],help=this.hinted.has(index);return `<button type="button" class="word-token ${help?'hinted':status}" data-word="${index}" ${timed?`data-start="${timed.start}" data-end="${timed.end}"`:''} title="${timed?'点击重听这个词':'暂无可靠词级定位，点击重听整句'}">${esc(word)}</button>`;
    }).join(' ');
  }
  bindWordButtons(root){root.querySelectorAll('[data-word]').forEach(button=>button.onclick=action(()=>{const start=Number(button.dataset.start),end=Number(button.dataset.end);return Number.isFinite(start)&&Number.isFinite(end)?this.host.play(start,{end,kind:'word'}):this.host.play();}));}
  renderReference(){
    if(!this.s)return;const revealed=this.host.isRevealed();$('checkBtn').innerHTML=icon('checkCircle')+'检查输入<kbd>Ctrl ↵</kbd>';$('revealBtn').textContent=revealed?'隐藏原文':'显示原文';$('editTextBtn').classList.toggle('hidden',!revealed);
    $('referenceHint').textContent=this.s.text_source==='web'?'来源网站参考文本；时间戳由本地音频匹配，对照准确率不代表雅思分数。':'本地模型识别参考，可能有误，可手动校正。';const content=$('referenceContent');$('referenceHint').classList.toggle('hidden',!this.s.text||!(revealed||this.checked||this.hinted.size));
    if(!this.s.text){content.className='reference-placeholder';content.innerHTML=icon('eyeOff')+'<p>参考原文尚未生成。<br><span>可以先听写，或使用本地模型生成原文。</span></p>';return;}
    if(!revealed&&!this.checked&&!this.hinted.size){content.className='reference-placeholder';content.innerHTML=icon('eyeOff')+'<p>先检查输入，再逐步找出漏听的词。<br><span>「提示一词」只揭开一个词；「显示原文」才展开整句。</span></p>';return;}
    const result=this.result();content.className='';content.innerHTML='<div class="reference-text assisted-reference">'+this.wordButtons(result.statuses,revealed)+'</div><div class="reference-actions"><span>已显示的词可以点击重听</span>'+(this.practice.needs_review?'<button id="clearReviewBtn" class="text-button">移出待复习</button>':'')+'</div>';
    this.bindWordButtons(content);if($('clearReviewBtn'))$('clearReviewBtn').onclick=()=>{this.practice.needs_review=false;this.host.queue({practice:true});this.renderReference();this.host.list();$('practiceBadge').textContent='';};
    $('referenceHint').textContent=this.s.text_source==='manual'?'人工校正的参考原文；对照准确率不代表雅思分数。':'本地 AI 参考，可能有误。点词定位来自识别时间戳；可校正原文。';
  }
  onInput(){if(this.checked){this.checked=false;$('practiceFeedback').classList.add('hidden');}this.renderReference();}
  onPlayed(){if(!this.s)return;this.practice.plays=(this.practice.plays||0)+1;$('playCount').textContent=`本句重听 ${this.practice.plays} 次`;this.host.queue({practice:true});}
  highlight(time){document.querySelectorAll('.word-token[data-start]').forEach(button=>button.classList.toggle('speaking',time>=Number(button.dataset.start)&&time<=Number(button.dataset.end)));}
}
