#!/usr/bin/env python3
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sections(body):
    d={};k=None;b=[]
    def flush():
        nonlocal b
        if k:d[k]='\n'.join(b).strip()
        b=[]
    for line in (body or '').splitlines():
        if line.startswith('### '):flush();k=line[4:].strip()
        else:b.append(line)
    flush();return d
def pick(s,n):
    v={k.lower():x for k,x in s.items()}.get(n.lower())
    return None if not v or v=='_No response_' else v.strip()
def main():
    a=argparse.ArgumentParser();a.add_argument('--event',required=True);x=a.parse_args()
    e=json.loads(Path(x.event).read_text());i=e['issue'];s=sections(i.get('body'))
    labels=[v['name'] for v in i.get('labels',[])]
    urls=re.findall(r'https?://[^\s<>)\]]+',pick(s,'Primary source URL(s)') or '')
    r={'schemaVersion':'1.0','issueNumber':i['number'],'issueUrl':i.get('html_url'),'updatedAt':now(),
       'title':pick(s,'Proposed record title') or re.sub(r'^\[CO-AUTHOR\]\s*','',i.get('title',''),flags=re.I),
       'contributionType':pick(s,'Contribution type'),'claimOrSummary':pick(s,'Claim / summary'),
       'eventOrTargetDate':pick(s,'Event or target date'),'announcementDate':pick(s,'Announcement date (future items only)'),
       'organization':pick(s,'Organization / provider'),'geography':pick(s,'Geography (if relevant)'),
       'sourceUrls':urls,'evidenceNote':pick(s,'Evidence note'),
       'contributor':{'name':pick(s,'Contributor name / credit'),'creditPreference':pick(s,'Credit preference'),
                      'githubLogin':(i.get('user') or {}).get('login'),'submittedAt':i.get('created_at')},
       'review':{'labels':labels,'approved':'co-author-approved' in labels},'entryOrigin':'co-author'}
    p=ROOT/'data/coauthor-submissions'/f"issue-{i['number']}.json"
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    if r['review']['approved']:
        q=ROOT/'data/coauthor-approved'/p.name;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'issue':i['number'],'approved':r['review']['approved']}))
if __name__=='__main__':main()
