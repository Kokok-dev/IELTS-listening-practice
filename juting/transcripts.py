"""Public reference extraction and conservative matching to real ASR timestamps."""
import re
import copy
from html.parser import HTMLParser
from difflib import SequenceMatcher
from .audio import new_segment


def tokens(text):
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower().replace('’', "'"))


class TranscriptParser(HTMLParser):
    def __init__(self, section):
        super().__init__(); self.target=f'ielts-listening-transcript-{section}'
        self.depth=0; self.lines=[]; self.current=[]

    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='div':
            if self.depth: self.depth+=1
            elif attrs.get('id')==self.target: self.depth=1
        if self.depth and tag in ('p','br'): self.flush()

    def handle_endtag(self, tag):
        if self.depth and tag=='p': self.flush()
        if self.depth and tag=='div':
            self.depth-=1
            if not self.depth: self.flush()

    def handle_data(self, data):
        if self.depth: self.current.append(data)

    def flush(self):
        value=re.sub(r'\s+',' ',''.join(self.current)).strip()
        value=re.sub(r'^[A-Z][A-Z\s\d\-]{0,35}:\s*','',value)
        if value: self.lines.append(value)
        self.current=[]


def sentences(text):
    # Protect common abbreviations and decimal points before sentence splitting.
    protected=re.sub(r'\b(?:Mr|Mrs|Ms|Dr|Prof|St|e\.g|i\.e)\.',lambda m:m[0].replace('.', '∯'),text)
    protected=re.sub(r'(?<=\d)\.(?=\d)','∯',protected)
    return [x.replace('∯','.').strip() for x in re.split(r'(?<=[.!?])\s+(?=[A-Z“"\d])',protected) if x.strip()]


def model_sentences(words, duration):
    """Punctuation in model output defines sentences; pauses alone never cut one."""
    groups=[]; current=[]
    for w in words:
        current.append(w)
        value=w['word'].strip()
        if re.search(r'[.!?]["\u201d\u2019]*$',value) and not re.search(r'^(?:Mr|Mrs|Ms|Dr|Prof|St)\.$',value):
            groups.append(current);current=[]
    if current: groups.append(current)
    result=[]
    for group in groups:
        start=max(0,float(group[0]['start'])-.06)
        if result: start=max(start,result[-1]['end'])
        end=min(duration,float(group[-1]['end'])+.06)
        if end<=start: continue
        s=new_segment(start,end,'model-sentence')
        s.update(text=''.join(w['word'] for w in group).strip(),text_source='asr')
        result.append(s)
    return result


def align_reference(lines, words, duration):
    units=[sentence for line in lines for sentence in sentences(line)]
    ref=[]; owners=[]
    for i,line in enumerate(units):
        ts=tokens(line);ref.extend(ts);owners.extend([i]*len(ts))
    heard=[]; heard_owner=[]
    for i,w in enumerate(words):
        ts=tokens(w['word']);heard.extend(ts);heard_owner.extend([i]*len(ts))
    matches={}
    for block in SequenceMatcher(None,ref,heard,autojunk=False).get_matching_blocks():
        for j in range(block.size): matches[block.a+j]=heard_owner[block.b+j]
    coverage=len(matches)/max(1,len(ref))
    if coverage<.72: raise ValueError(f'网上文本与音频匹配度不足（{coverage:.0%}），未自动替换，请检查版本。')
    result=[]
    for i,line in enumerate(units):
        indices=[j for j,owner in enumerate(owners) if owner==i]
        aligned=[matches[j] for j in indices if j in matches]
        if not aligned or len(aligned)/max(1,len(indices))<.5:
            raise ValueError('有句子无法可靠定位，未自动替换。')
        first,last=words[min(aligned)],words[max(aligned)]
        start=max(0,float(first['start'])-.06,result[-1]['end'] if result else 0)
        end=min(duration,float(last['end'])+.06)
        if end<=start: raise ValueError('文本时间顺序异常，未自动替换。')
        s=new_segment(start,end,'reference-sentence');s.update(text=line,text_source='web')
        result.append(s)
    return result,coverage


def is_announcement(text):
    text=' '.join(tokens(text))
    if re.match(r"^(?:you'll|you will|you are going to) hear\b",text): return True
    return bool(re.match(r'^(?:(?:now|first|next|before|you)\b.*?\b)?(?:look at (?:the )?questions|listen (?:carefully )?and answer|have (?:some )?time to|will hear|that is the end of|this is (?:the )?end of|section (?:one|two|three|four|[1-4])$|part (?:one|two|three|four|[1-4])$)',text))


def preserve_practice(old, new):
    """Each old answer goes to at most one overlapping new sentence; originals are backed up."""
    for previous in old:
        if not any(previous.get(k) for k in ('answer','note','done','starred','practice')): continue
        target=max(new,key=lambda s:max(0,min(s['end'],previous['end'])-max(s['start'],previous['start'])),default=None)
        if not target: continue
        overlap=min(target['end'],previous['end'])-max(target['start'],previous['start'])
        if overlap<=0: continue
        for key in ('answer','note'):
            target[key]='\n'.join(filter(None,[target.get(key,''),previous.get(key,'')]))
        target['starred']=target.get('starred',False) or previous.get('starred',False)
        previous_practice=copy.deepcopy(previous.get('practice',{}))
        combined=target.setdefault('practice',{})
        for key in ('plays','checks','hints'):
            if key in previous_practice: combined[key]=combined.get(key,0)+previous_practice[key]
        combined.setdefault('cloze_sets',{}).update(previous_practice.get('cloze_sets',{}))
        combined['needs_review']=True
