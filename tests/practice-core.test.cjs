const test=require('node:test');
const assert=require('node:assert/strict');
const core=require('../web/practice-core.js');

test('case and punctuation are ignored, safe contraction variants are accepted',()=>{
  assert.equal(core.evaluate('I do not know.','i DON’T know').correct,true);
  assert.equal(core.evaluate("We can't leave.",'We cannot leave').score,100);
  assert.equal(core.evaluate("She's here.",'She has here').correct,false);
});
test('missing and substituted words remain identifiable without revealing the answer',()=>{
  const result=core.evaluate('The garden room is on the ground floor.','The garden is on a ground floor');
  assert.equal(result.correct,false);
  assert.ok(result.statuses.filter(s=>s!=='correct').length>=2);
  assert.equal(result.firstIssue,2);
  assert.ok(result.score<100);
  assert.ok(!Object.hasOwn(result,'html'));
});
test('extra words are counted, empty input does not pass',()=>{
  assert.equal(core.evaluate('Hello there.','Hello there everyone').extra,1);
  assert.equal(core.evaluate('Hello.','').score,0);
  assert.equal(core.evaluate('','').correct,false);
});
test('cloze positions stay stable per sentence and difficulty, and never hide punctuation alone',()=>{
  const text='A good trip takes us to a quiet garden - every summer.';
  const a=core.cloze(text,30),b=core.cloze(text,30),hard=core.cloze(text,100);
  assert.deepEqual(a,b);
  assert.ok(a.selected.length>=1&&a.selected.length<hard.selected.length);
  assert.notEqual(a.signature,hard.signature);
  assert.ok(a.selected.every(i=>core.normalize(a.words[i])));
});
test('word timing stays inside this sentence and unavailable manual words have no fake timestamp',()=>{
  const segment={text:'Good morning everyone.',start:1,end:3};
  const words=[{word:' Good',start:.95,end:1.3},{word:' morning',start:1.4,end:1.8},{word:' everyone.',start:2,end:3.1}];
  const aligned=core.alignTimedWords(segment,words);
  assert.equal(aligned.length,3);
  assert.ok(aligned.every(w=>w.start>=1&&w.end<=3));
  assert.equal(core.alignTimedWords({...segment,text:'Different manual words'},words)[0],null);
});
