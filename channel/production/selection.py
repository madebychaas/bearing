"""One selected opportunity through review to a finished, unpublished preview.

The local ProducerStore owns the lock. This is not another intake or publisher;
revisions preserve the source, editorial choice and explicit review together.
"""
import copy, hashlib, json, re, threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import producer, scriptdesk

PRIMARY_REVIEW_SECONDS=3600
MONITORING_NOTE='The guard monitors coherent selected intake and explicitly maintained primary evidence. It cannot detect an unobserved remote-page change. Re-read primary sources before production; each primary review expires after one hour.'


class Conflict(ValueError):pass


def text(value, label, limit=2000, minimum=0):
    if not isinstance(value,str) or not minimum<=len(value.strip())<=limit:
        raise ValueError(f'{label} must contain {minimum}–{limit} characters')
    return value.strip()


def digest(value):return scriptdesk.fingerprint(value)
def speech(draft,phase=None):
    phases=(phase,) if phase else ('opening','body','closing')
    return ' '.join(block['text'].strip() for key in phases for block in draft[key])
def script_hash(draft):return hashlib.sha256(speech(draft).encode('utf-8')).hexdigest()


def source_url(value):
    try:
        parsed=urlsplit(value)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):raise ValueError()
    except (ValueError,TypeError):raise ValueError('Reviewed evidence requires an ordinary HTTPS source URL')
    return value


def bound_content(evidence):
    # Deliberately retain dates and negation. Desk material alerts are useful
    # explanations but cannot safely clear an already approved production.
    return digest([{k:re.sub(r'\s+',' ',str(e.get(k,''))).strip() for k in ('id','url','headline','excerpt','publishedTime')} for e in sorted(evidence,key=lambda item:item['id'])])


def validate_film(packet):
    from produce_film import validate_packet
    try:return validate_packet(packet)
    except (KeyError,TypeError,AttributeError) as exc:raise ValueError('The reviewed finished-film packet is incomplete or malformed') from exc


class SelectionStore:
    def __init__(self,desk):
        self.desk=desk;self.lock=desk.lock;self.root=desk.runs/'selections';self.workers={}

    def _now(self):return producer._stamp(producer._time(self.desk.clock()) or datetime.now(timezone.utc))

    def _path(self,event_id,mode):
        if mode not in ('live','demo'):raise ValueError('Unknown news mode')
        text(event_id,'Story ID',160,1)
        return self.root/mode/hashlib.sha256(event_id.encode()).hexdigest()[:24]

    def _read(self,event_id,mode):
        path=self._path(event_id,mode)/'current.json'
        if not path.exists():return None
        try:
            value=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(value,dict) or value.get('eventId')!=event_id or value.get('mode')!=mode:raise ValueError()
            return value
        except (OSError,ValueError) as exc:raise RuntimeError('Selection history could not be read; existing records were preserved') from exc

    def _save(self,record,action,note='',actor=''):
        import pipeline
        record=copy.deepcopy(record);record['revision']=record.get('revision',0)+1;record['updatedAt']=self._now()
        record['monitoring']={'note':MONITORING_NOTE,'primaryReviewSeconds':PRIMARY_REVIEW_SECONDS}
        record.setdefault('history',[]).append({'revision':record['revision'],'action':action,'at':record['updatedAt'],'note':note,'actor':actor,'sourceRevision':record['sourceRevision'],'voiceRevision':record['voiceRevision'],'scriptHash':record.get('scriptHash'),'packetHash':(record.get('prepared') or {}).get('packetHash')})
        folder=self._path(record['eventId'],record['mode'])
        archive=folder/'revisions'/f"{record['revision']:06d}-{digest(record)[:16]}.json"
        if not archive.exists():pipeline.write_json(archive,record)
        pipeline.write_json(folder/'current.json',record)
        return record

    def _snapshot(self,mode):
        state=self.desk._state(mode)
        reporting,candidates,health,now,demo=self.desk._inputs(mode,state)
        groups=producer._groups(reporting,candidates,health,state)
        updated=producer._observe(groups,state,now);self.desk._save(mode,updated)
        # Context and quoted evidence must come from the same read of the intake,
        # not a snapshot followed by a second read while the collector advances.
        value=producer.build_snapshot(reporting,candidates,health,updated,self.desk.config,now)
        value.update(mode=mode,demo=demo)
        lookup={r['id']:r for r in producer._items(candidates)}
        reports={r['id']:r for group in groups.values() for r in group}
        return value,lookup,reports

    def _sources(self,event,lookup,reports,snapshot):
        ids=[e['id'] for e in event['evidence']]
        for key in (event.get('localSignal') or {}).get('reportIds',[]):
            if key not in ids:ids.append(key)
        evidence=[]
        for key in ids:
            report=reports.get(key)
            if not report or report.get('revisionMismatch') or not report.get('available'):raise Conflict('A selected source is unavailable or intake revisions disagree. Reassess when coherent evidence is available.')
            candidate=lookup.get(key,{})
            evidence.append({'id':key,'publisher':report['publisher'],'url':source_url(report['url']),'publishedTime':report.get('publishedAt'),'headline':report['title'],'excerpt':report.get('excerpt',''),'contentHash':candidate.get('contentHash') or digest([report['title'],report.get('excerpt','')]),'origin':'intake','available':True,'holdReasons':candidate.get('holdReasons',[])})
        return evidence

    def _context(self,event,snapshot,product_id,why_now,note):
        product=next((p for p in snapshot['strategy']['products'] if p['id']==product_id),None)
        if not product:raise ValueError('Choose The Brief or In Focus')
        return {'product':copy.deepcopy(product),'whyNow':why_now,'producerNote':note,'opportunity':{k:copy.deepcopy(event.get(k)) for k in ('title','topic','summary','whyNow','strategy','fits','gaps','localSignal','change','decision')},'observedAt':snapshot.get('asOf'),'limitations':[*copy.deepcopy(snapshot.get('limitations',[])),MONITORING_NOTE]}

    def _pack(self,record):
        return {'schema':1,'storyId':record['eventId'],'sourceRevision':record['sourceRevision'],'evidence':copy.deepcopy(record['evidence']),'editorialContext':copy.deepcopy(record['context']),'selectionId':record['id']}

    def _primary_issue(self,evidence):
        checked=producer._time(evidence.get('checkedAt'))
        age=(producer._time(self._now())-checked).total_seconds() if checked else None
        if age is None or age < -300 or age>=PRIMARY_REVIEW_SECONDS:
            return f"Primary evidence {evidence['id']} needs an explicit source recheck within the last hour, followed by editorial reassessment."
        return None

    def _discovery_observation(self,evidence,reports,state,event_id):
        report=reports.get(evidence['id']) or state.get('events',{}).get(event_id,{}).get('reports',{}).get(evidence['id'])
        if not report or report.get('revisionMismatch'):return copy.deepcopy(evidence)
        return {**evidence,'headline':report['title'],'excerpt':report.get('excerpt',''),'url':report['url'],'publishedTime':report.get('publishedAt')}

    def _refresh(self,record):
        reasons=[]
        try:
            _,lookup,reports=self._snapshot(record['mode'])
            for evidence in record['evidence']:
                if evidence['origin']=='reviewed-primary':
                    issue=self._primary_issue(evidence)
                    if issue:reasons.append(issue)
                    continue
                if evidence['origin']!='intake':continue
                current=reports.get(evidence['id']);candidate=lookup.get(evidence['id'])
                if not current or not candidate:reasons.append('A bound source left the current intake; its freshness must be reassessed.');continue
                if current.get('revisionMismatch'):reasons.append('The bound intake files are between revisions.');continue
                if not current.get('available'):reasons.append('A bound reporting source is unavailable.');continue
                revised={**evidence,'headline':current['title'],'excerpt':current.get('excerpt',''),'url':current['url'],'publishedTime':current.get('publishedAt')}
                if bound_content([evidence])!=bound_content([revised]):reasons.append('Bound source wording, facts or publication context changed; compare the retained evidence before continuing.')
            # A rotated discovery item is not silently made current evidence.
            # If it returns with changed reporting, require another explicit review.
            for archived in record.get('discoveryEvidence',[]):
                original=archived['source'];current=reports.get(original['id'])
                if not current or not lookup.get(original['id']):continue
                if current.get('revisionMismatch'):
                    reasons.append('Returning discovery reporting is between revisions; reassess once its corrected evidence is coherent.');continue
                revised=self._discovery_observation(original,reports,{},record['eventId'])
                if bound_content([archived['lastObserved']])!=bound_content([revised]):reasons.append('The original discovery report returned with changed reporting; review the correction against the primary-source treatment.')
        except (OSError,RuntimeError,ValueError):reasons.append('Current reporting could not be verified; the prior selection is retained.')
        if record['voiceRevision']!=digest(scriptdesk.editorial_voice()):reasons.append('The maintained editorial voice standard changed; review the script again.')
        if reasons and not (record.get('reassessment') or {}).get('required'):
            record['reassessment']={'required':True,'reason':' '.join(dict.fromkeys(reasons)),'detectedAt':self._now()}
            record['approval']=None;record['state']='needs-reassessment'
            record=self._save(record,'reassessment-required',record['reassessment']['reason'])
        return record

    def get(self,event_id,mode='live'):
        with self.lock:
            record=self._read(event_id,mode)
            if record:
                record=self._refresh(record)
                if (record.get('production') or {}).get('state')=='running' and record['id'] not in self.workers:
                    record['production']['state']='interrupted';record['production']['error']='The local worker stopped; review and retry the same approved preparation.'
                    if record['state']=='producing':record['state']='held'
                    record=self._save(record,'production-interrupted')
            return {'selection':record}

    def _expected(self,record,payload):
        if type(payload.get('expectedRevision')) is not int or payload['expectedRevision']!=record['revision']:
            raise Conflict('The selection changed. Refresh the review before saving or approving.')

    def _clear_approval(self,record):
        record['approval']=None;record['production']=None

    def mutate(self,payload):
        action=payload.get('action');event_id=payload.get('eventId');mode=payload.get('mode','live')
        with self.lock:
            self._path(event_id,mode)
            if action not in ('select','save','evidence','prepare','review','reassess','produce'):raise ValueError('Unknown handoff action')
            record=self._read(event_id,mode)
            if record:record=self._refresh(record)
            if record and record['id'] in self.workers and not (action=='review' and payload.get('decision') in ('hold','reject')):raise Conflict('A production preview is running. Hold or reject it before changing this selection.')
            actor=text(payload.get('actor',''),'Reviewer',120)
            if action=='select':
                if record:self._expected(record,payload)
                why_now=text(payload.get('whyNow'),'Why now',2000,12);note=text(payload.get('note',''),'Selection note')
                snapshot,lookup,reports=self._snapshot(mode)
                event=next((e for e in snapshot['events'] if e['id']==event_id),None)
                if not event:raise KeyError(event_id)
                context=self._context(event,snapshot,payload.get('productId'),why_now,note)
                evidence=self._sources(event,lookup,reports,snapshot)
                record={'schema':1,'id':'selection-'+hashlib.sha256((mode+':'+event_id).encode()).hexdigest()[:24],'eventId':event_id,'mode':mode,'revision':record['revision'] if record else 0,'history':record.get('history',[]) if record else [],'state':'selected','productId':context['product']['id'],'product':context['product'],'whyNow':why_now,'note':note,'selectedAt':self._now(),'evidence':evidence,'context':context,'sourceRevision':digest(evidence),'voiceRevision':digest(scriptdesk.editorial_voice()),'responseSchema':scriptdesk.SCHEMA,'draft':None,'draftReview':None,'scriptHash':None,'prepared':None,'approval':None,'reassessment':None,'production':None}
                return {'selection':self._save(record,'select',note,actor)}
            if not record:raise KeyError(event_id)
            self._expected(record,payload)
            if action=='reassess':
                reason=text(payload.get('reason'),'Reassessment reason',2000,12)
                snapshot,lookup,reports=self._snapshot(mode)
                event=next((e for e in snapshot['events'] if e['id']==event_id),None)
                basis=payload.get('sourceBasis',record.get('sourceBasis','selected-intake'))
                if basis not in ('selected-intake','reviewed-primary'):raise ValueError('Choose selected-intake or reviewed-primary as the reassessed source basis')
                primaries=[e for e in record['evidence'] if e['origin']=='reviewed-primary']
                if basis=='reviewed-primary':
                    actor=text(payload.get('actor'),'Reassessing editor',120,1)
                    if not primaries:raise Conflict('A primary-source reassessment requires explicitly reviewed primary evidence')
                    evidence=primaries
                    archives=copy.deepcopy(record.get('discoveryEvidence',[]));known={entry['source']['id'] for entry in archives}
                    for source in record['evidence']:
                        if source['origin']=='intake' and source['id'] not in known:
                            archives.append({'source':copy.deepcopy(source),'archivedAt':self._now(),'actor':actor,'reason':reason});known.add(source['id'])
                    state=self.desk._state(mode)
                    for archived in archives:
                        archived['lastObserved']=self._discovery_observation(archived['source'],reports,state,event_id)
                        archived['reassessedAt']=self._now()
                    record['discoveryEvidence']=archives
                else:
                    if not event:raise Conflict('The selected opportunity is no longer present; explicitly reassess reviewed primary evidence or select a current opportunity instead.')
                    evidence=self._sources(event,lookup,reports,snapshot)+primaries
                # Reassessment cannot renew a primary-source check merely by
                # moving its clock. A reviewed replacement must arrive explicitly.
                for primary in evidence:
                    if primary['origin']=='reviewed-primary':
                        issue=self._primary_issue(primary)
                        if issue:raise Conflict(issue)
                record['evidence']=evidence;record['sourceRevision']=digest(evidence);record['voiceRevision']=digest(scriptdesk.editorial_voice())
                record['sourceBasis']=basis
                if payload.get('whyNow') is not None:record['whyNow']=text(payload['whyNow'],'Why now',2000,12)
                if event:record['context']=self._context(event,snapshot,record['productId'],record['whyNow'],record['note'])
                else:record['context']=copy.deepcopy(record['context']);record['context']['whyNow']=record['whyNow']
                if basis=='reviewed-primary':
                    record['context']['discoveryStatus']={'state':'outside-current-intake' if not event else 'discovery-only','checkedAt':self._now(),'note':'The original opportunity and source remain historical discovery context. Only the explicitly reviewed primary evidence supports the current script; no availability is asserted for archived reporting.'}
                    record['context']['sourceBasis']=basis
                record['context']['reassessmentReason']=reason
                record['reassessment']={'required':False,'reason':reason,'at':self._now()};record['prepared']=None;record['draftReview']=None
                self._clear_approval(record);record['state']='draft' if record['draft'] else 'selected'
                return {'selection':self._save(record,action,reason,actor)}
            if action=='review' and payload.get('decision') in ('hold','reject'):
                decision=payload['decision'];actor=text(payload.get('actor'),'Reviewer',120,1);note=text(payload.get('note',''),'Review note')
                self._clear_approval(record);record['state']='held' if decision=='hold' else 'rejected'
                return {'selection':self._save(record,decision,note,actor)}
            if (record.get('reassessment') or {}).get('required') and action!='evidence':raise Conflict(record['reassessment']['reason'])
            if action=='evidence':
                sources=payload.get('sources')
                if not isinstance(sources,list) or not 1<=len(sources)<=5:raise ValueError('Add one to five explicitly reviewed primary sources')
                updates={};existing={e['id']:e for e in record['evidence']};changed=[]
                for source in sources:
                    if not isinstance(source,dict):raise ValueError('Primary evidence must be an object')
                    identifier=text(source.get('id'),'Source ID',160,1)
                    if identifier in updates:raise ValueError('Review each primary source ID once per request')
                    previous=existing.get(identifier)
                    if previous and previous['origin']!='reviewed-primary':raise ValueError('An intake evidence ID cannot be replaced by a primary-source review')
                    checked=producer._time(source.get('checkedAt'))
                    if not checked or (checked-producer._time(self._now())).total_seconds()>300:raise ValueError('Primary evidence needs a valid checkedAt UTC timestamp')
                    value={'id':identifier,'publisher':text(source.get('publisher'),'Source publisher',200,1),'url':source_url(source.get('url')),'headline':text(source.get('title',source.get('headline')),'Source title',500,1),'excerpt':text(source.get('excerpt'),'Reviewed supporting excerpt',16000,12),'publishedTime':source.get('publishedTime'),'checkedAt':source['checkedAt'],'reviewNote':text(source.get('reviewNote'),'Source review note',2000,12),'origin':'reviewed-primary','available':True}
                    issue=self._primary_issue(value)
                    if issue:raise ValueError(issue)
                    value['contentHash']=digest([value['headline'],value['excerpt']]);updates[identifier]=value
                    if previous and bound_content([previous])!=bound_content([value]):changed.append(identifier)
                # Prior source text, script reviews and approval remain in the
                # immutable revision archive. Only this new revision is replaced.
                record['evidence']=[updates.pop(e['id'],e) for e in record['evidence']]+list(updates.values())
                record['sourceRevision']=digest(record['evidence']);record['prepared']=None;record['draftReview']=None;self._clear_approval(record)
                if changed:
                    record['reassessment']={'required':True,'reason':'Reviewed primary evidence changed: '+', '.join(changed)+'. Compare the retained revision and reassess before rewriting or approving.','detectedAt':self._now()}
                record['state']='needs-reassessment' if (record.get('reassessment') or {}).get('required') else 'draft' if record['draft'] else 'selected'
            elif action=='save':
                draft=copy.deepcopy(payload.get('draft'));review=scriptdesk.validate_draft(draft,self._pack(record))
                record.update(draft=draft,draftReview={**review,'method':'Producer-authored or assistant-authored draft; not editorial approval','checkedAt':self._now()},scriptHash=script_hash(draft),prepared=None,state='draft')
                self._clear_approval(record)
            elif action=='prepare':
                if record['productId']!='focus':raise ValueError('The Brief is selectable, but a reviewed production treatment is not prepared for this proof')
                if not record['draft'] or not record['draftReview']:raise ValueError('Save and check the source-bound script first')
                packet=copy.deepcopy(payload.get('packet'))
                if not isinstance(packet,dict):raise ValueError('Supply the reviewed finished-film packet')
                packet.pop('selection',None);plan=packet.get('plan',{});story=packet.get('story',{})
                if not isinstance(plan,dict) or not isinstance(story,dict) or not isinstance(story.get('source'),dict):raise ValueError('Supply a complete story and production plan')
                if story.get('script')!=speech(record['draft']) or any(plan.get(field)!=speech(record['draft'],phase) for field,phase in (('openingNarration','opening'),('body','body'),('closingNarration','closing'))):raise ValueError('Prepared narration must exactly match every reviewed script section')
                if story.get('source',{}).get('url') not in {e['url'] for e in record['evidence']}:raise ValueError('The film source must belong to the carried evidence')
                review=plan.get('review',{})
                if not isinstance(review,dict) or not all(review.get(key) for key in ('accuracy','voice','visuals','rights')):raise ValueError('Record the accuracy, voice, visual plan and rights review before approval')
                validate_film(packet)
                record['prepared']={'packet':packet,'packetHash':digest(packet),'preparedAt':self._now()};self._clear_approval(record);record['state']='draft'
            elif action=='review':
                if payload.get('decision')!='approve':raise ValueError('Choose approve, hold or reject')
                actor=text(payload.get('actor'),'Reviewer',120,1);note=text(payload.get('note',''),'Review note')
                if not record['draft'] or not record['prepared'] or not record['draftReview']:raise ValueError('Review a checked script and prepared picture/sound/rights plan before approval')
                if record['draft'].get('issues'):raise ValueError('Resolve the draft issues before approval')
                scriptdesk.validate_draft(record['draft'],self._pack(record));validate_film(record['prepared']['packet'])
                approval={'at':self._now(),'actor':actor,'note':note,'revision':record['revision']+1,'scriptHash':record['scriptHash'],'sourceRevision':record['sourceRevision'],'voiceRevision':record['voiceRevision'],'packetHash':record['prepared']['packetHash']}
                approval['id']='approval-'+digest(approval)[:24];record['approval']=approval;record['state']='approved';record['production']=None
                return {'selection':self._save(record,'approve',note,actor)}
            elif action=='produce':
                return self._start(record)
            return {'selection':self._save(record,action,text(payload.get('note',''),'Editorial note'),actor)}

    def _lineage(self,record):
        return {'selectionId':record['id'],'eventId':record['eventId'],'mode':record['mode'],'product':record['product'],'sourceRevision':record['sourceRevision'],'scriptRevision':record['scriptHash'],'voiceRevision':record['voiceRevision'],'approval':record['approval'],'whyNow':record['whyNow'],'selectedAt':record['selectedAt'],'context':record['context'],'evidence':record['evidence'],'sourceBasis':record.get('sourceBasis','selected-intake'),'discoveryEvidence':record.get('discoveryEvidence',[])}

    def _guard(self,event_id,mode,approval_id):
        with self.lock:
            record=self._read(event_id,mode)
            if not record:raise Conflict('The selected production no longer exists')
            record=self._refresh(record)
            approval=record.get('approval')
            if (record.get('reassessment') or {}).get('required') or not approval or approval['id']!=approval_id:raise Conflict('Production approval changed or reporting requires editorial reassessment')
            expected={'scriptHash':script_hash(record['draft']),'sourceRevision':digest(record['evidence']),'voiceRevision':record['voiceRevision'],'packetHash':digest(record['prepared']['packet'])}
            if any(approval.get(key)!=value for key,value in expected.items()):raise Conflict('Production no longer matches its approved revision')
            validate_film(record['prepared']['packet'])
            return record

    def _start(self,record):
        if record['mode']!='live':raise ValueError('Representative examples cannot produce current-news media')
        if record['productId']!='focus' or not record.get('approval'):raise ValueError('An approved In Focus script and production plan are required')
        if record['id'] in self.workers:raise Conflict('This production preview is already running')
        approval_id=record['approval']['id'];self._guard(record['eventId'],record['mode'],approval_id)
        packet=copy.deepcopy(record['prepared']['packet']);packet['selection']=self._lineage(record)
        record['production']={'state':'running','startedAt':self._now(),'completedAt':None,'result':None,'error':None};record['state']='producing'
        record=self._save(record,'produce-preview')
        worker=threading.Thread(target=self._produce,args=(record['eventId'],record['mode'],record['id'],approval_id,packet),daemon=True)
        self.workers[record['id']]=worker;worker.start()
        return {'selection':record}

    def _produce(self,event_id,mode,selection_id,approval_id,packet):
        try:
            import pipeline,produce_film
            guard=lambda:self._guard(event_id,mode,approval_id)
            with pipeline.production_lock():
                result=produce_film.produce(packet,publish_result=False,completion_guard=guard)
            with self.lock:
                record=guard();record['state']='complete';record['production']={'state':'complete','startedAt':record['production']['startedAt'],'completedAt':self._now(),'result':result,'error':None}
                self._save(record,'preview-complete')
        except Exception as exc:
            with self.lock:
                record=self._read(event_id,mode)
                if record:
                    if record['state'] not in ('needs-reassessment','rejected','held'):record['state']='held'
                    record['production']={**(record.get('production') or {}),'state':'held','completedAt':self._now(),'result':None,'error':str(exc)[:1000]}
                    self._save(record,'preview-held',str(exc)[:1000])
        finally:
            with self.lock:self.workers.pop(selection_id,None)
