/* Pure practice logic, shared by the browser and Node verification. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PracticeCore=api;})(typeof window!=='undefined'?window:globalThis,function(){
  'use strict';
  function tokens(text){return String(text||'').match(/\S+/g)||[];}
  function normalize(text){return String(text||'').replace(/[’‘]/g,"'").toLowerCase().replace(/[^a-z0-9']/g,'').replace(/^'+|'+$/g,'');}
  function canonical(text){
    const contractions={"can't":'cannot',"won't":'will not',"shan't":'shall not',"don't":'do not',"doesn't":'does not',"didn't":'did not',"isn't":'is not',"aren't":'are not',"wasn't":'was not',"weren't":'were not',"haven't":'have not',"hasn't":'has not',"hadn't":'had not',"wouldn't":'would not',"couldn't":'could not',"shouldn't":'should not',"mustn't":'must not',"i'm":'i am',"you're":'you are',"we're":'we are',"they're":'they are',"i'll":'i will',"you'll":'you will',"he'll":'he will',"she'll":'she will',"we'll":'we will',"they'll":'they will',"i've":'i have',"you've":'you have',"we've":'we have',"they've":'they have'};
    const result=[];for(const raw of tokens(text)){const key=normalize(raw);if(key)result.push(...(contractions[key]||key).split(' '));}return result;
  }
  function evaluate(reference,answer){
    const display=tokens(reference);const refs=[];display.forEach((raw,index)=>canonical(raw).forEach(key=>refs.push({key,index})));
    const entered=canonical(answer),n=refs.length,m=entered.length;
    if(n*m>250000)return {score:null,correct:false,statuses:display.map(()=> 'unknown'),firstIssue:0,extra:0};
    const dp=Array.from({length:n+1},()=>new Uint16Array(m+1));for(let i=0;i<=n;i++)dp[i][0]=i;for(let j=0;j<=m;j++)dp[0][j]=j;
    for(let i=1;i<=n;i++)for(let j=1;j<=m;j++)dp[i][j]=Math.min(dp[i-1][j]+1,dp[i][j-1]+1,dp[i-1][j-1]+(refs[i-1].key===entered[j-1]?0:1));
    const statuses=display.map(()=> 'correct');let i=n,j=m,extra=0;
    while(i||j){if(i&&j&&dp[i][j]===dp[i-1][j-1]+(refs[i-1].key===entered[j-1]?0:1)){if(refs[i-1].key!==entered[j-1])statuses[refs[i-1].index]='wrong';i--;j--;}else if(i&&dp[i][j]===dp[i-1][j]+1){statuses[refs[i-1].index]='missing';i--;}else{extra++;j--;}}
    const firstIssue=statuses.findIndex(s=>s!=='correct');return {score:n?Math.max(0,Math.round((1-dp[n][m]/n)*100)):0,correct:n>0&&dp[n][m]===0,statuses,firstIssue,extra};
  }
  function hash(text){let h=2166136261;for(const c of String(text)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return (h>>>0).toString(36);}
  function cloze(reference,percent=30){
    const words=tokens(reference),candidates=words.map((word,index)=>({index,key:normalize(word)})).filter(x=>x.key);
    const count=Math.max(1,Math.min(candidates.length,Math.round(candidates.length*percent/100)));
    const functionWords=new Set('a an the and or but so if as at by for from in into of on to up with is am are was were be been being do does did have has had i me my we our you your he him his she her it its they them their this that these those there here not no yes can could will would should may might very just also than then'.split(' '));
    const selected=candidates.map(x=>({...x,priority:functionWords.has(x.key)?0:1,rank:parseInt(hash(reference+'|'+x.index),36)})).sort((a,b)=>b.priority-a.priority||a.rank-b.rank).slice(0,count).map(x=>x.index).sort((a,b)=>a-b);
    return {words,selected,signature:hash('keywords-v2|'+reference+'|'+percent),percent};
  }
  function alignTimedWords(segment,words){
    const expected=tokens(segment.text),candidates=words.filter(w=>(w.start+w.end)/2>=segment.start-.03&&(w.start+w.end)/2<=segment.end+.03);
    const aligned=[];let cursor=0;for(const word of expected){const key=normalize(word);let found=-1;for(let i=cursor;i<Math.min(candidates.length,cursor+4);i++){if(normalize(candidates[i].word)===key){found=i;break;}}if(found<0){aligned.push(null);continue;}const w=candidates[found];aligned.push({start:Math.max(segment.start,w.start-.08),end:Math.min(segment.end,Math.max(w.start+.1,w.end+.12))});cursor=found+1;}
    return aligned;
  }
  function mask(word){return '•'.repeat(Math.max(2,Math.min(10,normalize(word).length)));}
  return {tokens,normalize,canonical,evaluate,cloze,hash,alignTimedWords,mask};
});
