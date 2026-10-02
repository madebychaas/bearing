"""A small, source-linked producer desk over Bearing's existing intake.

No ingestion, production or publication happens here. Heuristic leads are not
verified facts. One local server owns this store; its RLock serializes observer,
GET and decision calls. Do not run a second writer against the same state file.
"""
from __future__ import annotations
import copy, hashlib, json, os, re, threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit

UTC=timezone.utc
HERE=Path(__file__).resolve().parent
ACTIONS={'shortlist','watch','dismiss','reset'}
STOP=set('a an and are as at be been but by for from has have in into is it its of on or over that the their this to was were what when which who why will with says said reports report new updated latest live read more'.split())
ACTION_TERMS={'approved','blocked','suspended','recalled','expanded','corrected','closed','reopened','cancelled','enacted','overturned','rescinded'}
DATE_NOISE=re.compile(r'\b(?:mon|tues|wednes|thurs|fri|satur|sun)day\b|\b\d{4}-\d{2}-\d{2}(?:[tT][\d:.+zZ-]+)?\b|\b\d{1,2}:\d{2}(?:\s*[ap]m)?\b|\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,?\s+\d{4})?\b',re.I)
NUMBER=re.compile(r'(?<!\w)(?:\$\s*\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s*(?:%|million|billion|thousand|products|units|people|households|workers|homes|customers|dollars|percent)|\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?!\w)',re.I)

def _read(path,default):
    try:return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError,ValueError):return copy.deepcopy(default)

def _input(path,default):
    path=Path(path)
    if not path.exists():return copy.deepcopy(default)
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value,dict):raise ValueError('Expected an object')
        return value
    except (OSError,ValueError) as exc:raise RuntimeError(f'Producer input {path.name} is unreadable; history and decisions were preserved') from exc

def _stamp(value):return value.astimezone(UTC).isoformat().replace('+00:00','Z')

def _time(value):
    if isinstance(value,datetime):return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    if not isinstance(value,str) or 'T' not in value:return None
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        return parsed.astimezone(UTC) if parsed.tzinfo else None
    except ValueError:return None

def _items(value):
    if isinstance(value,list):return value
    if isinstance(value,dict):return value.get('items',value.get('candidates',value.get('stories',[])))
    return []

def _normal(value):
    text=DATE_NOISE.sub(' ',str(value).lower().replace('’',"'"))
    text=re.sub(r'\b(?:sign up for our|subscribe to our|follow us on|read more at|click here to|download our app)\b[^.!?]*(?:[.!?]|$)',' ',text)
    return re.sub(r'\s+',' ',re.sub(r'[^a-z0-9%$\s]',' ',text)).strip()

def _tokens(value):return set(_normal(value).split())-STOP

def _terms(text,terms):return [term for term in terms if re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',text,re.I)]

def _url(value):
    try:
        part=urlsplit(value)
        return value if part.scheme in ('http','https') and part.hostname and not part.username else ''
    except (ValueError,TypeError):return ''

def _canonical(value):
    part=urlsplit(_url(value));return (part.hostname or '')+part.path.rstrip('/')

def _config(config=None):return copy.deepcopy(config or _read(HERE/'producer-strategy.json',{}))

def _evidence(report,candidate,health):
    item={**candidate,**report};source=item.get('source') or {};feed=health.get(item.get('sourceId'),{})
    def meta(key,default=None):return item.get(key,source.get(key,default))
    mismatch=bool(report.get('version') and candidate.get('contentHash') and report['version']!=candidate['contentHash'])
    excerpt='' if mismatch else str(item.get('sourceExcerpt','')).strip()
    return {'id':str(item.get('id','')),'publisher':str(item.get('publisherGroup') or source.get('name','Unknown source')),
            'title':str(item.get('title','Untitled report')),'url':_url(source.get('url','')),'publishedAt':item.get('publishedTime'),
            'excerpt':excerpt,'level':'excerpt' if len(excerpt.split())>=12 else 'headline',
            'available':item.get('sourceAvailable',True) is not False and feed.get('status') not in ('error','unavailable','disabled'),
            'sourceId':item.get('sourceId'),'sourceLastSuccess':item.get('sourceLastSuccess') or feed.get('lastSuccess'),
            'market':meta('market'),'local':meta('local',False) is True,'originalReporting':meta('originalReporting',False) is True,
            'owner':meta('owner') or item.get('publisherGroup') or source.get('name'),'syndication':meta('syndication'),
            'syndicatedFrom':meta('syndicatedFrom'),'originalId':meta('originalId'),'topic':item.get('topic','general'),
            'suppressed':bool(item.get('editorial',{}).get('suppressed')),'foreignLocal':bool(item.get('editorial',{}).get('foreignLocal')),
            'domestic':item.get('editorial',{}).get('domestic',item.get('domestic')),'revisionMismatch':mismatch,'holdReasons':item.get('holdReasons',[]),
            **{key:item.get(key) for key in ('firstSeenAt','firstRevisionSeenAt','discoveryKind','publicationLagSeconds','sourceTimeKind','sourceUpdatedAt','alert','discoveryOnly','filing')}}

def _owners(reports):
    return {str((r.get('syndication') or {}).get('provider') or r.get('syndicatedFrom') or r['owner']) for r in reports}

def _lead(report):
    return report['title']+' '+' '.join(report['excerpt'].split()[:85])

def _us_link(text):
    return bool(re.search(r'\bUS\b|\bU\.S\.',text) or re.search(r'\b(?:Americans?|United States|Texas|California|Florida|New York|federal student loans?)\b',text,re.I))

def _groups(reporting,candidates,source_health,state=None):
    lookup={s['id']:s for s in _items(candidates) if s.get('id')}
    health={s['id']:s for s in source_health.get('sources',[]) if s.get('id')};groups={}
    reports=_items(reporting)
    for report in reports:
        if not report.get('id'):continue
        identity=report.get('coverage',{}).get('id')
        if not identity:identity='event-'+hashlib.sha256((_canonical(report.get('source',{}).get('url','')) or report['id']).encode()).hexdigest()[:14]
        groups.setdefault(identity,[]).append(_evidence(report,lookup.get(report['id'],{}),health))
    # Preserve an active editorial choice when a rolling intake window drops it.
    for identity,entry in (state or {}).get('events',{}).items():
        if identity not in groups and entry.get('decision',{}).get('action') in ('shortlist','watch','dismiss'):
            groups[identity]=[{**r,'available':False} for r in entry.get('reports',{}).values()]
    return {key:sorted({r['id']:r for r in values}.values(),key=lambda r:r['id']) for key,values in groups.items() if values}

def _semantic(report):return _normal(report.get('title','')+' '+report.get('excerpt',''))

def _quantity(value):return {re.sub(r'[\s,]+','',s.lower()) for s in NUMBER.findall(DATE_NOISE.sub(' ',value))}

def _change(old,reports,now):
    current={r['id']:r for r in reports};previous=old.get('reports',{})
    base={'material':False,'at':_stamp(now),'evidenceIds':[],'details':[]}
    if not previous:return {**base,'kind':'new','text':'New to this desk. Discovery time is not evidence of a new development.'}
    changed=[];cosmetic=False
    for key,report in current.items():
        before=previous.get(key)
        if not before:continue
        old_text=_semantic(before);new_text=_semantic(report)
        if old_text==new_text:continue
        cosmetic=True
        if _normal(before.get('excerpt',''))==_normal(report.get('excerpt','')):continue
        left,right=_tokens(old_text),_tokens(new_text);overlap=len(left&right)/max(1,min(len(left),len(right)))
        # A newly fetched full excerpt or a headline alone is not proof of a factual change.
        if before.get('level')!='excerpt' or report.get('level')!='excerpt' or overlap<.5:continue
        old_raw=before['title']+' '+before.get('excerpt','');new_raw=report['title']+' '+report.get('excerpt','')
        old_numbers,new_numbers=_quantity(old_raw),_quantity(new_raw)
        added_actions=(right-left)&ACTION_TERMS
        if old_numbers and new_numbers and old_numbers!=new_numbers:
            reason='A sourced quantity changed: '+', '.join(sorted(old_numbers))+' → '+', '.join(sorted(new_numbers))+'.'
        elif added_actions:
            reason='Reporting adds a consequential action: '+', '.join(sorted(added_actions))+'.'
        else:continue
        changed.append({'reportId':key,'reason':reason,'before':before['title']+' — '+before.get('excerpt',''),'after':report['title']+' — '+report.get('excerpt','')})
    if changed:return {**base,'kind':'material','material':True,'text':'Potential material change in existing reporting. Inspect the before/after evidence.','evidenceIds':[d['reportId'] for d in changed],'details':changed}
    added=[key for key in current if key not in previous]
    if added:return {**base,'kind':'source-added','text':'Additional reporting is available; source count alone is not a material development.','evidenceIds':added}
    if cosmetic:return {**base,'kind':'cosmetic','text':'Wording changed without a detected consequential fact or action. No material-update alert.'}
    return {**base,'kind':'unchanged','text':'No material change detected in the retained reporting.'}

def _fingerprint(reports):
    # Timestamps, feed retrieval, formatting and source ordering do not create revisions.
    return hashlib.sha256(json.dumps([(r['id'],_semantic(r)) for r in reports],ensure_ascii=False).encode()).hexdigest()

def _observe(groups,state,now):
    result=copy.deepcopy(state);ledger=result.setdefault('events',{})
    for identity,reports in groups.items():
        old=ledger.get(identity,{})
        # The collector writes candidates and reporting separately. Never compare
        # a half-updated pair or replace the last coherent comparison baseline.
        if any(r.get('revisionMismatch') for r in reports):
            ledger.setdefault(identity,{'firstSeenAt':_stamp(now),'lastSeenAt':_stamp(now),'reports':{},'history':[]})
            continue
        fingerprint=_fingerprint(reports)
        entry={**old,'firstSeenAt':old.get('firstSeenAt',_stamp(now)),'lastSeenAt':_stamp(now),'reports':{r['id']:r for r in reports},'fingerprint':fingerprint}
        if fingerprint!=old.get('fingerprint'):
            change=_change(old,reports,now);entry['change']=change
            entry['history']=[*old.get('history',[]),change][-24:]
        ledger[identity]=entry
    return result

def _local_signals(groups,config,now):
    signals={};minimum=config.get('localMinimumMarkets',3)
    for pattern in config.get('localPatterns',[]):
        candidates=[]
        for identity,reports in groups.items():
            for report in reports:
                at=_time(report.get('publishedAt'));age=(now-at).total_seconds()/3600 if at else None
                if not(report['local'] and report['originalReporting'] and report['market'] and report['owner'] and report['available']):continue
                if report.get('syndicatedFrom') or report.get('syndication') or report.get('originalId'):continue
                if age is None or not 0<=age<=config.get('localWindowHours',72):continue
                if report['level']!='excerpt':continue
                text=report['title']+' '+report['excerpt']
                if not all(_terms(text,options) for options in pattern['allOf']):continue
                tokens=_tokens(report['excerpt'])
                # Different market names pasted into the same wire story are not independent.
                if any(len(tokens&other)/max(1,len(tokens|other))>=.78 for _,_,other in candidates):continue
                if any(report['owner']==r['owner'] or report['market']==r['market'] for _,r,_ in candidates):continue
                candidates.append((identity,report,tokens))
        if len(candidates)<minimum:continue
        signal={'label':pattern['label'],'markets':[r['market'] for _,r,_ in candidates],
                'publishers':[r['publisher'] for _,r,_ in candidates],'reportIds':[r['id'] for _,r,_ in candidates],
                'reason':f'{len(candidates)} distinct markets and separately identified original-reporting owners show matching practical-impact terms.',
                'caveat':'An editorial lead to investigate, not proof of a national trend. Check comparability, scale and original reporting.'}
        # Configured order prefers the more specific reporting question when
        # the same evidence also matches a broader pattern (insurance/housing).
        for identity,_,_ in candidates:signals.setdefault(identity,signal)
    return signals

def build_snapshot(reporting,candidates,source_health,state=None,config=None,now=None):
    """Pure view builder. Neither inputs nor persisted state are modified."""
    now=_time(now) or datetime.now(UTC);config=_config(config);state=copy.deepcopy(state or {})
    source_health=copy.deepcopy(source_health or {});groups=_groups(reporting,candidates,source_health,state)
    local=_local_signals(groups,config,now);events=[]
    for identity,reports in groups.items():
        ledger=state.get('events',{}).get(identity,{})
        valid=[r for r in reports if _time(r.get('publishedAt')) and _time(r['publishedAt'])<=now]
        latest=max(valid,key=lambda r:_time(r['publishedAt'])) if valid else reports[0]
        latest_at=_time(latest.get('publishedAt'));age=(now-latest_at).total_seconds()/60 if latest_at else None
        status='unknown' if age is None else 'future' if age < 0 else 'stale' if age>72*60 else 'fresh'
        all_text=' '.join(_lead(r) for r in reports)
        human_training=bool(re.search(r'\b(?:jobs?|workforce|workers?|careers?|students?|apprenticeships?|vocational|employment)\b',all_text,re.I))
        civic_recall=bool(re.search(r'\brecall (?:election|petitions?)\b|\b(?:their|mayoral) recall\b',all_text,re.I))
        matches=[]
        for rule in config['rules']:
            terms=[t for t in rule['terms'] if not(t=='training' and not human_training) and not(t in ('recall','recalled') and civic_recall)]
            hits=[(r,_terms(_lead(r),terms)) for r in reports]
            found=sorted(set(term for _,terms in hits for term in terms))
            if found:matches.append({'id':rule['id'],'label':rule['label'],'terms':found,'evidenceIds':[r['id'] for r,terms in hits if terms]})
        suppressed=any(r['suppressed'] for r in reports) or any(_terms(r['title'],config['suppressTerms']) for r in reports)
        foreign_local=all(r.get('foreignLocal',False) for r in reports) or bool(_terms(all_text,config.get('foreignPlaceTerms',[]))) and not _us_link(all_text)
        preview=_terms(latest['title'],config.get('previewTerms',[]))
        core_impact=any(m['id'] in ('household','work') for m in matches) or bool(_terms(all_text,config.get('publicConsequenceTerms',[])))
        direct_change=_terms(latest['title'],config.get('directChangeTerms',[]))
        political_frame=bool(_terms(all_text,config.get('politicalFrameTerms',[]))) and not _terms(all_text,config.get('civicUtilityTerms',[]))
        reaction=bool(_terms(latest['title'],config.get('reactionTerms',[])))
        utility=[(r,_terms(_lead(r),config.get('utilityTerms',[]))) for r in reports] if core_impact else []
        available=any(r['available'] for r in reports);rich=[r for r in reports if r['level']=='excerpt']
        gaps=[]
        if not rich:gaps.append('Headline-only evidence: confirm the underlying facts, scale and consequence before assignment.')
        if any(r.get('revisionMismatch') for r in reports):gaps.append('The intake files are between revisions; the mismatched excerpt is withheld until they agree.')
        if len(_owners(reports))<2:gaps.append('One reporting origin in this cluster; seek independent reporting or primary evidence.')
        if not available:gaps.append('Current source availability is degraded; inspect the retained report before relying on it.')
        if status=='stale':gaps.append('No recent dated development in the available reporting; explain why this belongs today.')
        if status=='future':gaps.append('Source timestamp is in the future; freshness is withheld pending review.')
        if status=='unknown':gaps.append('No usable source publication time; freshness is unknown.')
        if suppressed:gaps.append('Promotional, roundup or political-sparring cues reduce suitability; inspect before using.')
        if foreign_local:gaps.append('This is local coverage outside the U.S.; an American audience consequence has not been established.')
        if not core_impact:gaps.append('A practical household, work or public-service consequence is not established in the headline and lead excerpt.')
        if political_frame:gaps.append('The available framing centers on political positioning or election sentiment; find the underlying consequence before making it a primary candidate.')
        if reaction:gaps.append('This headline centers on reaction to a decision; prefer reporting that establishes the decision and its practical effect.')
        if preview:gaps.append('Preview or proposal language is not a completed decision; establish what has actually changed.')
        change=copy.deepcopy(ledger.get('change') or _change({},reports,now))
        material=next((entry for entry in reversed(ledger.get('history',[])) if entry.get('material')),None)
        if material and _time(material.get('at')) and 0<=(now-_time(material['at'])).total_seconds()<=config.get('changeWindowHours',24)*3600:
            change=copy.deepcopy(material)
        change_at=_time(change.get('at'));recent_change=bool(change.get('material') and change_at and 0<=(now-change_at).total_seconds()<=config.get('changeWindowHours',24)*3600)
        decision=copy.deepcopy(ledger.get('decision') or {'action':'none','note':'','at':None,'history':[]})
        fresh_text=f"{latest['publisher']} published this report at {latest.get('publishedAt')}." if latest_at else 'The reporting has no usable dated news peg.'
        immediate=next((m for m in matches if m['id']=='immediate'),None)
        if immediate:fresh_text+=' It contains '+', '.join(immediate['terms'][:3])+' language worth checking for immediate consequence.'
        if status!='fresh':fresh_text+=' '+{'stale':'This is context unless a current consequence is established.','future':'Do not interpret the future timestamp as freshness.','unknown':'Retrieval time does not make the development new.'}[status]
        fits={}
        for product in config['products']:
            pid=product['id'];score=0;reasons=[]
            for match in matches:
                rule=next(r for r in config['rules'] if r['id']==match['id']);weight=rule[pid];score+=weight
                reasons.append({'text':match['label']+': '+', '.join(match['terms'][:4])+'.','terms':match['terms'],'evidenceIds':match['evidenceIds'],'contribution':weight})
            in_window=age is not None and 0<=age<=product['freshnessHours']*60
            if in_window:score+=24 if pid=='brief' else 12
            else:score-=45 if pid=='brief' else 25
            if rich:score+=5 if pid=='brief' else 20
            else:score-=15 if pid=='brief' else 35
            if len(_owners(reports))>=2:score+=6 if pid=='brief' else 10
            if pid=='brief' and any(terms for _,terms in utility):
                score+=35;reasons.append({'text':'The Brief can give viewers a practical action: '+', '.join(sorted({term for _,terms in utility for term in terms}))+'.','terms':sorted({term for _,terms in utility for term in terms}),'evidenceIds':[r['id'] for r,terms in utility if terms],'contribution':35})
            if core_impact and direct_change:
                gain=25 if pid=='brief' else 8;score+=gain
                reasons.append({'text':('The Brief can establish a concrete development: ' if pid=='brief' else 'In Focus can explain the consequences of this reported change: ')+', '.join(direct_change)+'.','terms':direct_change,'evidenceIds':[latest['id']],'contribution':gain})
            mechanism=next((m for m in matches if m['id']=='mechanism'),None)
            if pid=='focus' and mechanism and len(mechanism['terms'])>1:
                score+=12;reasons.append({'text':'In Focus has multiple connected explanatory components: '+', '.join(mechanism['terms'][:4])+'.','terms':mechanism['terms'],'evidenceIds':mechanism['evidenceIds'],'contribution':42})
            if identity in local:score+=5 if pid=='brief' else 25;reasons.append({'text':local[identity]['reason'],'terms':[],'evidenceIds':local[identity]['reportIds']})
            if recent_change:score+=20 if pid=='brief' else 8;reasons.append({'text':'Potential consequential change in a retained source; compare before and after.','terms':[],'evidenceIds':change['evidenceIds']})
            if suppressed:score-=100
            if foreign_local:score-=90
            if not core_impact:score-=70
            if political_frame:score-=70
            if reaction:score-=70
            if preview:score-=20 if pid=='brief' else 5
            if not available:score-=25
            if status in ('future','unknown'):score-=60
            reasons.append({'text':f"Dated reporting {'is' if in_window else 'is not'} within this product's {product['freshnessHours']}-hour review window.",'terms':[],'evidenceIds':[latest['id']]})
            product_gaps=list(gaps)
            if pid=='focus':product_gaps.append('Before production: establish the explanatory question, visuals, source rights and what remains unresolved.')
            reasons.sort(key=lambda reason:-reason.get('contribution',0))
            fits[pid]={'score':max(0,score),'rank':None,'label':'Strong lead' if score>=70 and not suppressed and not foreign_local and core_impact and not political_frame and not reaction else 'Consider' if score>=35 and not suppressed and not foreign_local and core_impact and not political_frame and not reaction else 'Needs development','reasons':reasons,'gaps':product_gaps}
        events.append({'id':identity,'title':latest['title'],'topic':latest['topic'],'summary':latest['excerpt'] or 'Only the source headline is available; there is no synthesized factual summary.',
                       'whyNow':{'text':fresh_text,'at':latest.get('publishedAt'),'status':status,'ageMinutes':round(age,1) if age is not None else None},
                       'strategy':{'reason':'; '.join(m['label']+' ('+', '.join(m['terms'][:3])+')' for m in matches) or 'No configured practical-impact cue matched; retain as an alternative, not a priority.', 'matches':matches},
                       'fits':fits,'evidence':reports,'change':change,'history':copy.deepcopy(ledger.get('history',[change])),'decision':decision,
                       'localSignal':local.get(identity),'gaps':gaps,'signals':{'watch':bool(_terms(all_text,config['watchTerms'])) or bool(preview) or decision['action']=='watch','update':recent_change,'local':identity in local},
                       'eligible':core_impact and not political_frame and not reaction and not suppressed and not foreign_local and status=='fresh' and available and not any(r.get('revisionMismatch') for r in reports),'readiness':'Editorial lead; not verified or assigned'})
    rankings={}
    for product in config['products']:
        pid=product['id'];ordered=sorted(events,key=lambda e:(-e['fits'][pid]['score'],e['id']))
        rankings[pid]=[e['id'] for e in ordered]
        for index,event in enumerate(ordered):event['fits'][pid]['rank']=index+1
    observed=_time(reporting.get('checkedAt')) if isinstance(reporting,dict) else None
    source_health['stale']=not observed or (now-observed).total_seconds()>config.get('sourceStaleMinutes',120)*60 or observed>now+timedelta(minutes=5)
    stats={'events':len(events),'reports':sum(len(e['evidence']) for e in events),'shortlisted':sum(e['decision']['action']=='shortlist' for e in events),'watching':sum(e['decision']['action']=='watch' for e in events),'dismissed':sum(e['decision']['action']=='dismiss' for e in events),'materialUpdates':sum(e['signals']['update'] for e in events),'localSignals':sum(e['signals']['local'] for e in events),'stale':sum(e['whyNow']['status']=='stale' for e in events),'future':sum(e['whyNow']['status']=='future' for e in events)}
    return {'schema':1,'mode':'live','label':'Live reporting · editorial leads','generatedAt':_stamp(now),'asOf':reporting.get('checkedAt') if isinstance(reporting,dict) else None,'strategy':{k:copy.deepcopy(config[k]) for k in ('name','summary','products')},'stats':stats,'sourceHealth':source_health,'events':events,'rankings':rankings,'demo':None,'limitations':['Recommendations are explainable heuristics, not verified facts or assignments.','Publication timestamps establish recency, not independent verification of a new event.','Material-change flags compare retained excerpts; missing or subtle changes may not be detected.','Local convergence requires explicit original-reporting provenance from distinct owners and markets; it is not a national-trend finding.']}

class ProducerStore:
    def __init__(self,channel_root,now=None):
        self.root=Path(channel_root);self.work=self.root/'production';self.runs=self.work/'runs';self.clock=now or (lambda:datetime.now(UTC));self.lock=threading.RLock()
        self.config=_input(self.work/'producer-strategy.json',_config())
    def _path(self,mode):
        if mode not in ('live','demo'):raise ValueError('Unknown producer mode')
        return self.runs/('producer-state.json' if mode=='live' else 'producer-demo-state.json')
    def _save(self,mode,state):
        path=self._path(mode);path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temporary,path)
    def _state(self,mode):
        path=self._path(mode)
        if not path.exists():return {'schema':1,'events':{},'demoStep':0}
        try:
            state=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(state,dict) or not isinstance(state.get('events'),dict):raise ValueError('Invalid producer state')
            return state
        except (OSError,ValueError) as exc:raise RuntimeError('Producer decision state could not be read; existing file was preserved') from exc
    def _inputs(self,mode,state):
        if mode=='live':
            coherent=self.runs/'intake-snapshot.json'
            if coherent.exists():
                bundle=_input(coherent,{})
                if bundle.get('schema')!=1 or not all(isinstance(bundle.get(key),dict) for key in ('reporting','candidates','sourceHealth')):
                    raise RuntimeError('The coherent intake snapshot is incomplete; retained editorial state is preserved')
                return (bundle['reporting'],bundle['candidates'],bundle['sourceHealth'],_time(self.clock()) or datetime.now(UTC),None)
            return (_input(self.root/'dist/reporting.json',{'items':[]}),_input(self.work/'candidates/latest.json',{'items':[]}),_input(self.root/'dist/source-status.json',{'healthy':0,'total':0,'sources':[]}),_time(self.clock()) or datetime.now(UTC),None)
        fixture=_input(self.work/'producer-demo.json',{})
        if not fixture.get('steps'):raise ValueError('Representative fixture is unavailable')
        index=min(max(0,int(state.get('demoStep',0))),len(fixture['steps'])-1);step=fixture['steps'][index]
        now=_time(fixture['baseTime'])+timedelta(minutes=step.get('minutes',0))
        return step['reporting'],step['candidates'],step.get('sourceHealth',{}),now,{'step':index,'totalSteps':len(fixture['steps']),'canAdvance':index<len(fixture['steps'])-1,'label':fixture['label']+' · '+step['label']}
    def snapshot(self,mode='live'):
        with self.lock:
            state=self._state(mode)
            reporting,candidates,health,now,demo=self._inputs(mode,state)
            updated=_observe(_groups(reporting,candidates,health,state),state,now)
            self._save(mode,updated)
            result=build_snapshot(reporting,candidates,health,updated,self.config,now)
            result.update(mode=mode,demo=demo,label='Representative news cycle · synthetic examples' if mode=='demo' else result['label'])
            if mode=='live':
                import assignment
                result=assignment.enrich(result,_input(self.work/'sources.json',{'sources':[]}),now)
                import release_calendar
                calendar=release_calendar.snapshot(self.root,now)
                result['assignment']['watchpoints']=calendar['events']
                result['assignment']['calendarHealth']=calendar['health']
                import top_stories
                authored=_read(self.work/'top-stories-editorial.json',{'items':[]})
                result['topStories']=top_stories.select(result,authored if isinstance(authored,dict) else {},now)
            return result
    def decide(self,event_id,action,note='',mode='live'):
        if action not in ACTIONS:raise ValueError('Unknown editorial action')
        if not isinstance(note,str) or len(note)>500:raise ValueError('Decision note must be at most 500 characters')
        with self.lock:
            snapshot=self.snapshot(mode);state=self._state(mode)
            if event_id not in {e['id'] for e in snapshot['events']}:raise ValueError('Unknown story opportunity')
            entry=state['events'][event_id];at=_stamp(_time(self.clock()) or datetime.now(UTC));previous=entry.get('decision',{})
            event={'action':action,'note':note.strip(),'at':at}
            entry['decision']={'action':'none' if action=='reset' else action,'note':note.strip(),'at':at,'history':[*previous.get('history',[]),event]}
            self._save(mode,state);return self.snapshot(mode)
    def demo(self,action):
        if action not in ('advance','reset'):raise ValueError('Unknown representative-cycle action')
        with self.lock:
            state=self._state('demo')
            if action=='reset':state={'schema':1,'events':{},'demoStep':0}
            else:
                self.snapshot('demo');state=self._state('demo')
                fixture=_read(self.work/'producer-demo.json',{});state['demoStep']=min(state.get('demoStep',0)+1,len(fixture['steps'])-1)
            self._save('demo',state);return self.snapshot('demo')
