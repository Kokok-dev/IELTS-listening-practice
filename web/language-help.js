'use strict';

const languageCache=new Map();
let wordLookup=null;

async function lookupJSON(url,signal){
  let response;
  try {
    response=await fetch(url,{signal,referrerPolicy:'no-referrer',credentials:'omit'});
  } catch(error) {
    if(signal.aborted)throw error;
    throw Error('无法连接查询服务，请检查网络后重试。');
  }
  if(!response.ok)throw Error(`查询服务暂时不可用（${response.status}）`);
  return response.json();
}

async function translateEnglish(text,signal){
  const key='zh:'+text;
  if(languageCache.has(key))return languageCache.get(key);
  if(new TextEncoder().encode(text).length>500)throw Error('这句超过在线翻译的长度限制，请先拆成短句。');
  const query=new URLSearchParams({q:text,langpair:'en|zh-CN'});
  const data=await lookupJSON('https://api.mymemory.translated.net/get?'+query,signal);
  if(Number(data.responseStatus)!==200||!data.responseData?.translatedText){
    throw Error(Number(data.responseStatus)===429?'翻译额度暂时用完，请稍后再试。':'翻译服务没有返回可用结果。');
  }
  const decoder=document.createElement('textarea');
  decoder.innerHTML=data.responseData.translatedText;
  const result=decoder.value.trim();
  if(!result)throw Error('翻译服务没有返回可用结果。');
  if(languageCache.size>=200)languageCache.delete(languageCache.keys().next().value);
  languageCache.set(key,result);
  return result;
}

async function englishDefinitions(word,signal){
  const data=await lookupJSON('https://api.dictionaryapi.dev/api/v2/entries/en/'+encodeURIComponent(word),signal);
  if(!Array.isArray(data))return [];
  const definitions=[];
  for(const entry of data){
    for(const meaning of entry.meanings||[]){
      for(const sense of (meaning.definitions||[]).slice(0,2)){
        if(typeof sense.definition!=='string'||definitions.some(item=>item.definition===sense.definition))continue;
        definitions.push({part:meaning.partOfSpeech,definition:sense.definition});
        if(definitions.length===6)return definitions;
      }
    }
  }
  return definitions;
}

function addLanguageResult(target,label,value){
  const line=document.createElement('p');
  const title=document.createElement('b');
  title.textContent=label;
  line.append(title,document.createTextNode(' '+value));
  target.append(line);
}

function lookupWordKey(text){
  return text.trim().toLowerCase().replace(/’/g,"'").replace(/^[^a-z]+|[^a-z]+$/g,'');
}

async function showWordHelp(text,{retry=false}={}){
  const word=lookupWordKey(text);
  if(!word||wordLookup?.word===word&&!(retry&&wordLookup.failed))return;
  wordLookup?.request.abort();
  const request=new AbortController();
  const lookup={word,request,failed:false};
  wordLookup=lookup;
  const result=$('languageResult');
  $('languageOriginal').textContent=word;
  $('wordResult').classList.remove('hidden');
  result.textContent='正在查询…';
  const timer=setTimeout(()=>request.abort(),12000);
  try {
    const [translation,definitions]=await Promise.allSettled([
      translateEnglish(word,request.signal),
      englishDefinitions(word,request.signal),
    ]);
    if(wordLookup!==lookup)return;
    result.replaceChildren();
    if(translation.status==='fulfilled')addLanguageResult(result,'中文参考',translation.value);
    if(definitions.status==='fulfilled'){
      for(const sense of definitions.value)addLanguageResult(result,sense.part||'英文释义',sense.definition);
    }
    if(!result.childNodes.length){
      lookup.failed=true;
      const detail=translation.status==='rejected'&&translation.reason?.message;
      result.textContent=request.signal.aborted?'查询超时，请稍后再试。':detail||'暂未查到释义。';
    }else if(definitions.status==='rejected'||!definitions.value.length){
      addLanguageResult(result,'英文释义','暂未查到，可尝试单词原形。');
    }
  }finally{
    clearTimeout(timer);
  }
}
