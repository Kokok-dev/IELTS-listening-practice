"""Apply the v0.3 frontend wiring to the existing desktop UI."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'web/index.html';s=p.read_text('utf-8')
s=s.replace('按停顿分段适合精听，但不一定等于语法上的完整句子。可以随时手动拆分、合并。','优先使用网上剑桥文本并对齐时间；其他音频按模型标点和时间戳切句。停顿切句仅作导入预览和备用。')
s=s.replace('生成参考原文</button>','匹配文本并按句切分</button>')
s=s.replace('导入或下载音频后，自动在后台识别原文','导入或下载后，自动匹配网上文本或本地识别并切句')
s=s.replace('<div class="divider"></div><div class="model-setting">','<label class="checkbox-setting"><input type="checkbox" id="skipAnnouncements" checked>跳过识别出的题目播报（保留音频，可随时恢复）</label><label class="setting-label">练习范围<select id="practiceScope"><option value="all">全部句子</option><option value="key">重点句：较长句子与待复习句</option><option value="sample">抽练：每三句练一句</option></select></label><button id="cacheBtn" class="secondary full">管理音频缓存</button><div class="divider"></div><div class="model-setting">')
s=s.replace('<div id="toast"','<dialog id="cacheDialog"><form method="dialog" class="dialog-header"><h2>缓存管理</h2><button class="icon-button">关闭</button></form><div class="dialog-body"><p id="cacheSummary"></p><p>仅清理可重新下载的在线音频和超过 24 小时的临时文件。保留听写、笔记、网上文本、本地导入音频、模型和备份。</p><button id="clearTempBtn" class="secondary full">清理过期临时文件</button><button id="clearAudioBtn" class="secondary full">清理在线音频缓存</button></div></dialog><div id="toast"')
s=s.replace('0.2.0','0.3.0').replace('class="version">0.2','class="version">0.3')
p.write_text(s,'utf-8')
p=root/'web/app.js';s=p.read_text('utf-8')
s=s.replace("audio.src=`/api/courses/${id}/audio`;", "if(C.audio_cached===false){if(window.confirm('此音频缓存已清理，是否重新下载？听写记录保留。'))watchJob(await api(`/courses/${id}/restore-audio`,{method:'POST'}));return;}audio.src=`/api/courses/${id}/audio`;")
s=s.replace("showView('practice');renderCourse();", "if($('skipAnnouncements').checked&&C.segments[I]?.announcement){const first=C.segments.findIndex(x=>!x.announcement);if(first>=0)I=first;}showView('practice');renderCourse();")
s=s.replace("C.source_url?'在线资料 · 已缓存':'本地导入'", "(C.reference?.kind==='web'?'网上文本 · 已对齐':C.segmentation==='model'?'本地模型 · 按句切分':C.source_url?'在线资料 · 待匹配文本':'本地导入 · 待模型切句')")
s=s.replace("if(!seg())return;const count=", "if(!seg())return;if($('skipAnnouncements').checked&&seg().announcement){return navigate(1);}const count=")
s=s.replace("if(modelReady&&$('autoAsr').checked)", "if(last.kind!=='restore'&&modelReady&&$('autoAsr').checked)")
s=s.replace("toast('参考原文已生成，可以开始核对了。');", "toast(C?.transcript_warning||C?.reference?.warning||'文本与句子时间已更新。');")
s=s.replace("if(!modelReady){openSettings();", "if(!modelReady&&!C.words?.length){openSettings();")
s=s.replace("重新识别这份音频？已人工校正的原文会保留。", "重新匹配文本并按句切分？原记录自动备份，迁移过的输入标记为待复习；人工校正的分句保留。")
s=s.replace('参考原文由本地模型生成。','优先匹配网上文本，无可用文本时使用本地识别；首次定位时间仍需本地模型。')
anchor="bind('bookSelect',renderCatalog,'change');"
s=s.replace(anchor,"""bind('skipAnnouncements',async()=>{localStorage.setItem('juting-skip-announcements',String($('skipAnnouncements').checked));if(C&&seg()?.announcement&&$('skipAnnouncements').checked)await navigate(1);renderList();},'change');
bind('practiceScope',()=>{localStorage.setItem('juting-scope',$('practiceScope').value);renderList();},'change');
async function showCache(){const info=await api('/cache');$('cacheSummary').textContent=`在线音频 ${(info.download_bytes/1048576).toFixed(1)} MiB；过期临时文件 ${(info.temporary_bytes/1048576).toFixed(1)} MiB`;$('cacheDialog').showModal();}
bind('cacheBtn',()=>{$('settingsDialog').close();return showCache();});
async function clearCache(downloads){await flushDraft();stop();if(downloads&&!window.confirm('清理所有在线音频缓存？下次练习需重新下载，听写和笔记保留。'))return;if(downloads){audio.removeAttribute('src');audio.load();}const result=await api('/cache/clear',{method:'POST',body:{downloads}});toast(`已释放 ${(result.removed_bytes/1048576).toFixed(1)} MiB`);await showCache();if(downloads&&C?.source_id)C.audio_cached=false;}
bind('clearTempBtn',()=>clearCache(false));bind('clearAudioBtn',()=>clearCache(true));
"""+anchor)
s=s.replace("if(!seg())return;if($('skipAnnouncements')", "if(!seg())return;if(C.audio_cached===false){await openCourse(C.id);return;}if($('skipAnnouncements')")
s=s.replace("(async()=>{try{$('autoAsr')", "(async()=>{try{$('skipAnnouncements').checked=localStorage.getItem('juting-skip-announcements')!=='false';$('practiceScope').value=localStorage.getItem('juting-scope')||'all';$('autoAsr')")
p.write_text(s,'utf-8')
p=root/'web/enhancements.js';s=p.read_text('utf-8')
s=s.replace("accepts(s){return", "accepts(s){if($('skipAnnouncements')?.checked&&s.announcement)return false;const scope=$('practiceScope')?.value;if(scope==='key'&&!s.practice?.needs_review&&(s.text.match(/\\S+/g)||[]).length<12)return false;if(scope==='sample'&&this.host.course().segments.indexOf(s)%3!==0&&!s.practice?.needs_review)return false;return")
s=s.replace("const content=$('referenceContent');", "$('referenceHint').textContent=this.s.text_source==='web'?'来源网站参考文本；时间戳由本地音频匹配，对照准确率不代表雅思分数。':'本地模型识别参考，可能有误，可手动校正。';const content=$('referenceContent');")
p.write_text(s,'utf-8')
