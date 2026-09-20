#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re
from datetime import datetime, timezone, date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
UA='LINEAiGE-ALW/1.0 (+https://lineaige.barbph.com/methodology/)'
NAV_LABELS={'skip to main content','skip to content','main content','home','menu','search','next','previous','back to top'}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except FileNotFoundError:return d
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def fetch(u,limit=1200000):
    r=urlopen(Request(u,headers={'User-Agent':UA}),timeout=18)
    return r.geturl(),getattr(r,'status',200),r.read(limit)
def canon(u):
    p=urlparse(u)
    return f'{p.scheme.lower()}://{p.netloc.lower()}{re.sub(r"/+$","",p.path) or "/"}'+(('?'+p.query) if p.query else '')
def navigation_only(label):
    clean=re.sub(r'\s+',' ',html.unescape(label or '')).strip().lower()
    return clean in NAV_LABELS or clean.startswith('skip to ')
class L(HTMLParser):
    def __init__(self):super().__init__();self.h=None;self.t=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='a':self.h=dict(attrs).get('href');self.t=[]
    def handle_data(self,d):
        if self.h is not None:self.t.append(d)
    def handle_endtag(self,tag):
        if tag.lower()=='a' and self.h is not None:
            self.links.append((self.h,re.sub(r'\s+',' ',html.unescape(' '.join(self.t))).strip()))
            self.h=None;self.t=[]
def known():
    out=set()
    for p in [ROOT/'data/events.json',ROOT/'data/future-announcements.json',ROOT/'data/research-ledger.json']:
        x=load(p,{})
        rows=x.get('events') or x.get('records') or x.get('entries') or []
        for r in rows:
            for s in r.get('sources',[]):
                if s.get('url'):out.add(canon(s['url']))
            for k in ('source','primaryDocument'):
                if r.get(k):out.add(canon(r[k]))
    for p in (ROOT/'data/candidates').glob('*.json'):
        r=load(p,{})
        for s in r.get('sources',[]):
            if s.get('url'):out.add(canon(s['url']))
    return out
def lane(text,configured,future_words):
    if configured in ('future','historical'):return configured
    low=text.lower()
    years=[int(x) for x in re.findall(r'\b20\d{2}\b',low)]
    return 'future' if any(w in low for w in future_words) or any(y>date.today().year for y in years) else 'historical-or-current'
def add(inbox,seen,row):
    u=canon(row['url'])
    if not u.startswith(('http://','https://')) or u in seen:return 0
    seen.add(u)
    row.update(id='alw-'+hashlib.sha1(u.encode()).hexdigest()[:16],url=u,status='unreviewed',discoveredAt=now())
    inbox['records'].append(row)
    return 1
def main():
    cfg=load(ROOT/'config/alw-sources.json',{})
    inbox=load(ROOT/'data/alw/inbox.json',{'schemaVersion':'1.0','records':[]})
    state=load(ROOT/'data/alw/source-state.json',{'schemaVersion':'1.0','sources':{}})
    seen=known()|{canon(r['url']) for r in inbox['records'] if r.get('url')}
    added=0
    kws=[x.lower() for x in cfg['linkKeywords']]
    fw=[x.lower() for x in cfg['futureKeywords']]
    for src in cfg['officialRoots']:
        ss=state['sources'].setdefault(src['id'],{'seenUrls':[]})
        old=set(ss.get('seenUrls',[]));new=set(old)
        try:
            final,status,body=fetch(src['url'])
            parser=L();parser.feed(body.decode('utf-8','replace'))
            allowed=set(src.get('allowedHosts') or [urlparse(src['url']).netloc])
            for href,label in parser.links:
                u=canon(urljoin(final,href));p=urlparse(u);hay=(label+' '+u).lower()
                if navigation_only(label):continue
                if p.scheme not in ('http','https') or p.netloc.lower() not in allowed or not any(k in hay for k in kws):continue
                new.add(u)
                if u in old:continue
                added+=add(inbox,seen,{'laneHint':lane(label+' '+u,src.get('lane','both'),fw),'title':label or u.rsplit('/',1)[-1],'sourceName':src['name'],'sourceClass':'official-root','evidenceTier':'primary-candidate','url':u,'note':'Discovery only; claim-level review required before canonical admission.'})
            ss.update(seenUrls=sorted(new)[-2500:],lastChecked=now(),lastStatus=status,pageHash=hashlib.sha256(body).hexdigest())
        except Exception as e:
            ss.update(lastChecked=now(),lastError=(type(e).__name__+': '+str(e))[:400])
    for feed in cfg.get('discoveryFeeds',[]):
        try:
            _,_,body=fetch(feed['url'])
            root=ET.fromstring(body)
            for item in root.findall('.//item')[:60]:
                title=item.findtext('title') or ''
                u=item.findtext('link')
                if u:
                    added+=add(inbox,seen,{'laneHint':feed['lane'],'title':title,'sourceName':feed['name'],'sourceClass':'discovery-feed','evidenceTier':'discovery-only','url':u,'note':'Discovery lead only; locate primary evidence before admission.'})
        except Exception:pass
    inbox['records']=inbox['records'][-1500:]
    inbox['updatedAt']=now()
    state['lastRun']=now()
    save(ROOT/'data/alw/inbox.json',inbox)
    save(ROOT/'data/alw/source-state.json',state)
    print(json.dumps({'added':added,'inbox':len(inbox['records'])}))
if __name__=='__main__':main()
