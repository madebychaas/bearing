"""Bearing: bounded source intake, neural audio production, and atomic editions.

No model is permitted to invent reporting. Automated briefs use attributed text
from allowlisted publishers. More complex stories remain in the review queue.
"""
from __future__ import annotations
import argparse, asyncio, copy, hashlib, html, json, os, re, shutil, subprocess, sys, tempfile, time
import urllib.request, urllib.parse, urllib.error, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
import editorial
import coverage

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
WORK = ROOT / 'production'
VOICES = {'warm':'en_US-ljspeech-medium', 'measured':'en_US-bryce-medium'}
DISCOVERY_VERSION = 3
FEEDS = [feed for feed in json.loads((WORK/'sources.json').read_text(encoding='utf-8'))['sources'] if feed['enabled']]
TOPICS = {'space':'Space & discovery','nature':'Nature & our planet','culture':'Art & culture','world':'World & society','technology':'Technology','business':'Business & economy','health':'Health','sport':'Sport','local':'North Texas'}
ALLOWED_HOSTS = {h for feed in FEEDS for h in feed['hosts']} | {'www.fisheries.noaa.gov','musee.louvre.fr','www.louvre.fr','www.metmuseum.org','www.coe.int','pace.coe.int'}
REVIEW_TERMS = re.compile(r'\b(death|dead|killed|war|attack|election|vote|cancer|treatment|vaccine|stock|investment|alleged|accused|emergency|evacuat\w*|hurricane|tsunami|warning|damaging|flood\w*|tornado\w*)\b',re.I)

class PlainText(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
        if tag in ('p','br','div'): self.parts.append(' ')
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.skip:self.skip-=1
        if tag in ('p','div'):self.parts.append(' ')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

def plain(value):
    parser=PlainText();parser.feed(value or '')
    return re.sub(r'\s+',' ',html.unescape(' '.join(parser.parts))).strip()

def stamp(): return datetime.now(timezone.utc).isoformat()

@contextmanager
def _file_lock(path,message):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as handle:
        if path.stat().st_size==0:handle.write(b'\0');handle.flush()
        handle.seek(0)
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise RuntimeError(message)
        else:
            import fcntl
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError:raise RuntimeError(message)
        try:yield
        finally:
            handle.seek(0)
            if os.name=='nt':msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(handle,fcntl.LOCK_UN)
@contextmanager
def production_lock():
    with _file_lock(WORK/'.production.lock','Another Bearing production run is active'):yield

@contextmanager
def intake_lock():
    # Reporting must keep arriving while a finished film occupies production.
    with _file_lock(WORK/'runs'/'intake.lock','Another Bearing intake check is active'):yield

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as handle:
        temporary=Path(handle.name)
        json.dump(data,handle,ensure_ascii=False,indent=2)
    try:os.replace(temporary,path)
    finally:temporary.unlink(missing_ok=True)

def validate_url(url,hosts=ALLOWED_HOSTS):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname not in hosts or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError('Source URL is outside the approved publishers')
    return url

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        validate_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url,headers=None):
    validate_url(url)
    request=urllib.request.Request(url,headers={'User-Agent':'BearingNewsPreview/1.1 (source-attributed personal briefing)','Accept':'application/rss+xml,application/atom+xml,application/xml,text/xml,application/json',**(headers or {})})
    try:
        with urllib.request.build_opener(SafeRedirect).open(request,timeout=18) as response:
            data=response.read(2_000_001)
            if len(data)>2_000_000:raise ValueError('Source exceeds intake size limit')
            return {'body':data,'status':response.status,'etag':response.headers.get('ETag'),'modified':response.headers.get('Last-Modified'),'cacheControl':response.headers.get('Cache-Control')}
    except urllib.error.HTTPError as exc:
        if exc.code==304:return {'status':304,'cacheControl':exc.headers.get('Cache-Control')}
        raise

def canonical_url(url):
    parsed=urllib.parse.urlsplit(html.unescape(url.strip()))
    query=[(k,v) for k,v in urllib.parse.parse_qsl(parsed.query,keep_blank_values=True) if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid','cmpid','ocid')]
    return urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urllib.parse.urlencode(query),''))

def parse_feed(data):
    root=ET.fromstring(data)
    if root.tag.split('}')[-1].lower() not in ('rss','feed','rdf'):raise ValueError('Response is not RSS, Atom, or RDF')
    entries=[]
    for item in (n for n in root.iter() if n.tag.split('}')[-1] in ('item','entry')):
        fields={};links=[]
        for child in item:
            key=child.tag.split('}')[-1]
            if key=='link':
                if child.attrib.get('rel','alternate')=='alternate':links.append(child.attrib.get('href',child.text or ''))
            else:fields[key]=''.join(child.itertext()).strip()
        publication=fields.get('pubDate',fields.get('published',fields.get('date','')))
        alert={key:plain(fields[key])[:1200] for key in ('event','severity','urgency','certainty','effective','expires','areaDesc') if fields.get(key)}
        entries.append({'title':fields.get('title',''),'description':fields.get('description',fields.get('summary','')),'link':next(iter(links),''),'published':publication or fields.get('updated',''),'timestampKind':'published' if publication else 'updated','updated':fields.get('updated',''),**({'alert':alert} if alert else {})})
        if len(entries)>=200:break
    return entries

def feed_interval(data,configured):
    """Respect a publisher's RSS cache TTL; never poll faster than our setting."""
    root=ET.fromstring(data)
    for node in root.iter():
        if node.tag.split('}')[-1]=='ttl':
            try:return max(configured,min(1440,int(node.text)))
            except (TypeError,ValueError):pass
    return configured

def cache_interval(value):
    match=re.search(r'(?:^|,)\s*max-age\s*=\s*"?(\d+)',value or '',re.I)
    return min(1440,int(match[1])/60) if match else None

def date_value(text):
    if not text:return None
    try:value=parsedate_to_datetime(text)
    except (ValueError,TypeError):
        try:value=datetime.fromisoformat(text.replace('Z','+00:00'))
        except ValueError:return None
    return value.replace(tzinfo=timezone.utc) if not value.tzinfo else value.astimezone(timezone.utc)

def exact_publication_time(text):
    """A date or a timezone-less timestamp is insufficient for minute-age claims."""
    if not text or not re.search(r'\d{1,2}:\d{2}',text):return None
    try:value=parsedate_to_datetime(text)
    except (ValueError,TypeError):
        try:value=datetime.fromisoformat(text.replace('Z','+00:00'))
        except ValueError:return None
    return value.astimezone(timezone.utc).isoformat() if value.tzinfo else None

def candidate(entry,feed,now=None):
    now=now or datetime.now(timezone.utc)
    title=plain(entry.get('title',''));description=plain(entry.get('description',''))
    url=canonical_url(entry.get('link',''));published=date_value(entry.get('published',''))
    reasons=[]
    try:validate_url(url,set(feed['hosts']))
    except ValueError:reasons.append('source_not_allowed')
    if not published:reasons.append('missing_publication_date')
    elif published>now+timedelta(minutes=15) or published<now-timedelta(days=feed.get('maxAgeDays',7)):reasons.append('outside_freshness_window')
    if entry.get('timestampKind')=='updated':reasons.append('updated_timestamp_only')
    if not 15<=len(title)<=180:reasons.append('title_length')
    # A complete source excerpt is used, never an invented or truncated sentence.
    if not 20<=len(description.split())<=110:reasons.append('needs_a_complete_short_excerpt')
    if description and (description[-1] not in '.!?' or description.endswith(('...','…'))):reasons.append('incomplete_excerpt')
    if description.casefold()==title.casefold():reasons.append('headline_only')
    if feed.get('mode')!='automatic':reasons.append('source_requires_review')
    if feed.get('discoveryOnly'):reasons.append('discovery_only')
    if feed['topic'] in ('health','business','world','local'):reasons.append('editorial_review_required')
    if REVIEW_TERMS.search(title+' '+description):reasons.append('editorial_review_required')
    if re.search(r'construction safety|collapse|disaster|the presentations highlighted',title+' '+description,re.I):reasons.append('needs_full_source_context')
    if re.search(r'https?://|click here|subscribe|read more|the post .* appeared',description,re.I):reasons.append('feed_boilerplate')
    if any(p in (title+' '+description).lower() for p in ['ignore previous','system prompt','assistant:']):reasons.append('unexpected_source_text')
    topic='business' if editorial.MONEY.search(title) else feed['topic'];identifier='auto-'+hashlib.sha256(url.encode()).hexdigest()[:14]
    return {'id':identifier,'topic':topic,'topicLabel':TOPICS[topic],'title':title,'dek':f'A source briefing from {feed["name"]}.',
        'publishedAt':published.date().isoformat() if published else None,'publishedTime':exact_publication_time(entry.get('published','')),'expiresAt':(published+timedelta(days=feed.get('maxAgeDays',7))).isoformat() if published else None,'dateLabel':published.strftime('%d %b %Y') if published else 'Date unavailable',
        'source':{'name':feed['name'],'title':title,'url':url},'script':f'{feed["name"]} reports. {title}. {description}',
        'facts':[], 'storyKind':'sourceBrief',
        'editorialNote':'Automatically prepared from the attributed publisher’s title and feed description. The source text is not independently verified; story artwork is illustrative.',
        'editorial':editorial.assess({'title':title,'topic':topic},feed),'sourceId':feed['id'],'publisherGroup':feed['publisherGroup'],'reviewStatus':'source_excerpt' if not reasons else 'needs_review','holdReasons':sorted(set(reasons)),
        'sourceExcerpt':description,'retrievedAt':now.isoformat(),'sourceTimeKind':entry.get('timestampKind','published'),'sourceUpdatedAt':exact_publication_time(entry.get('updated','')),
        'local':feed.get('local',feed.get('topic')=='local'),'market':feed.get('market'),'originalReporting':feed.get('originalReporting',False),'owner':feed.get('owner',feed['publisherGroup']),'alert':entry.get('alert'),'filing':entry.get('filing'),'discoveryOnly':bool(feed.get('discoveryOnly')),
        'contentHash':hashlib.sha256((title+'\n'+description).encode()).hexdigest()}

def collect(force=False):
    with intake_lock():return _collect(force)

def _collect(force=False):
    now=datetime.now(timezone.utc);result={'retrievedAt':now.isoformat(),'candidates':[],'sources':[]};seen=set()
    cache_path=WORK/'runs'/'feed-cache.json'
    try:cache=json.loads(cache_path.read_text(encoding='utf-8'))
    except (OSError,ValueError):cache={}
    def read_source(feed):
        checked=datetime.now(timezone.utc)
        previous=cache.get(feed['id'],{});state=copy.deepcopy(previous)
        if state.get('url')!=feed['url']:state={}
        source={'id':feed['id'],'name':feed['name'],'topic':feed['topic'],'mode':feed['mode'],'url':feed['url'],'pollMinutes':feed['pollMinutes'],'attempted':False,'initialDiscovery':not bool(state.get('lastSuccess')) or state.get('discoveryVersion')!=DISCOVERY_VERSION or not date_value(state.get('discoveryBaselineAt')),'previousSuccess':state.get('lastSuccess'),'discoveryBaselineAt':state.get('discoveryBaselineAt'),'domestic':feed.get('domestic'),'local':feed.get('local',feed.get('topic')=='local'),'sourceRole':feed.get('sourceRole')}
        due=date_value(state.get('nextCheckAt'));entries=state.get('entries',[])
        last_success=date_value(state.get('lastSuccess'))
        if due and last_success and not state.get('failures'):
            due=min(due,last_success+timedelta(minutes=max(feed['pollMinutes'],state.get('intervalMinutes',0),state.get('cacheMinutes',0))))
            state['nextCheckAt']=due.isoformat()
        try:
            if not force and due and checked<due:
                if state.get('failures'):raise RuntimeError('Waiting before retry after source failure')
                source['status']='cached'
            else:
                source['attempted']=True;state['lastAttemptAt']=checked.isoformat();started=time.monotonic()
                headers={k:v for k,v in [('If-None-Match',state.get('etag')),('If-Modified-Since',state.get('modified'))] if v}
                response=fetch(feed['url'],headers)
                if response['status']==304:
                    if 'entries' not in state:raise ValueError('304 received without a retained feed')
                    source['status']='unchanged'
                else:
                    if feed.get('adapter')=='federal-register-inspection':
                        from primary_feeds import parse_inspection
                        entries=parse_inspection(response['body']);interval=feed['pollMinutes']
                    else:entries=parse_feed(response['body']);interval=feed_interval(response['body'],feed['pollMinutes'])
                    state.update(etag=response.get('etag'),modified=response.get('modified'),entries=entries,intervalMinutes=interval)
                    source['status']='ok'
                cache_minutes=cache_interval(response.get('cacheControl'))
                if cache_minutes is not None:state['cacheMinutes']=cache_minutes
                elif response['status']!=304:state.pop('cacheMinutes',None)
                completed=datetime.now(timezone.utc)
                if source['initialDiscovery']:state['discoveryBaselineAt']=completed.isoformat()
                source['discoveryBaselineAt']=state['discoveryBaselineAt']
                state.update(url=feed['url'],failures=0,discoveryVersion=DISCOVERY_VERSION,lastSuccess=completed.isoformat(),lastDurationMs=round((time.monotonic()-started)*1000),nextCheckAt=(completed+timedelta(minutes=max(feed['pollMinutes'],state.get('intervalMinutes',0),state.get('cacheMinutes',0)))).isoformat())
                state.pop('lastError',None)
            candidates=[candidate(entry,feed,now) for entry in entries]
            dates=[date_value(entry.get('published')) for entry in entries if entry.get('timestampKind','published')=='published'];dates=[date for date in dates if date and date<=now+timedelta(minutes=15)]
            precise=[date_value(exact_publication_time(entry.get('published',''))) for entry in entries if entry.get('timestampKind','published')=='published'];precise=[date for date in precise if date and date<=now+timedelta(minutes=15)]
            updated=[date_value(exact_publication_time(entry.get('updated',''))) for entry in entries];updated=[date for date in updated if date and date<=now+timedelta(minutes=15)]
            source.update(entryCount=len(entries),lastAttemptAt=state.get('lastAttemptAt'),lastDurationMs=state.get('lastDurationMs'),lastSuccess=state.get('lastSuccess'),nextCheckAt=state.get('nextCheckAt'),effectivePollMinutes=max(feed['pollMinutes'],state.get('intervalMinutes',0),state.get('cacheMinutes',0)),publisherTtlMinutes=state.get('intervalMinutes'),httpCacheMinutes=state.get('cacheMinutes'),latestPublishedAt=max(precise).isoformat() if precise else None,latestPublishedDate=max(dates).date().isoformat() if dates else None,latestUpdatedAt=max(updated).isoformat() if updated else None)
            source['fresh']=bool(dates and max(dates)>=now-timedelta(days=feed['maxAgeDays']))
            return feed['id'],source,state,candidates
        except Exception as exc:
            if source['attempted']:
                completed=datetime.now(timezone.utc);failures=state.get('failures',0)+1
                state.update(url=feed['url'],failures=failures,lastDurationMs=round((time.monotonic()-started)*1000),lastError=str(exc)[:200],nextCheckAt=(completed+timedelta(minutes=min(360,feed['pollMinutes']*2**min(failures-1,4)))).isoformat())
            source.update(status='unavailable',fresh=False,reason=state.get('lastError',str(exc)[:200]),lastAttemptAt=state.get('lastAttemptAt'),lastDurationMs=state.get('lastDurationMs'),lastSuccess=state.get('lastSuccess'),nextCheckAt=state.get('nextCheckAt'),effectivePollMinutes=max(feed['pollMinutes'],state.get('intervalMinutes',0),state.get('cacheMinutes',0)))
            # Retain dated links during a partial outage, with their source explicitly marked unavailable.
            retained=[candidate(entry,feed,now) for entry in entries] if state.get('lastSuccess') else []
            return feed['id'],source,state,retained
    with ThreadPoolExecutor(max_workers=4) as pool:
        for identifier,source,state,items in pool.map(read_source,FEEDS):
            cache[identifier]=state;result['sources'].append(source)
            for item in items:
                if item['id'] not in seen:result['candidates'].append(item);seen.add(item['id'])
    record_discovery(result)
    write_json(cache_path,cache)
    # Fast scheduling should not archive identical feed bodies every minute.
    fingerprint=hashlib.sha256(json.dumps({'items':[(s['id'],s['contentHash'],s.get('publishedTime'),s['holdReasons']) for s in result['candidates']],'sources':[(s['id'],s['status']=='unavailable') for s in result['sources']]},sort_keys=True).encode()).hexdigest()
    intake_index=WORK/'runs'/'intake-version.json'
    try:previous_fingerprint=json.loads(intake_index.read_text(encoding='utf-8'))['fingerprint']
    except (OSError,ValueError,KeyError):previous_fingerprint=None
    if fingerprint!=previous_fingerprint:
        run=WORK/'runs'/now.strftime('%Y%m%dT%H%M%S%fZ')
        write_json(run/'intake.json',result);write_json(intake_index,{'fingerprint':fingerprint,'recordedAt':now.isoformat()})
    write_json(WORK/'candidates'/'latest.json',result)
    healthy=sum(source['status']!='unavailable' for source in result['sources'])
    health={'checkedAt':result['retrievedAt'],'completedAt':stamp(),'healthy':healthy,'total':len(FEEDS),'attempted':sum(source['attempted'] for source in result['sources']),'sources':result['sources']}
    for field,source_key,choose in [('lastAttemptAt','lastAttemptAt',max),('lastSuccess','lastSuccess',max),('nextDueAt','nextCheckAt',min)]:
        dates=[date_value(source.get(source_key)) for source in result['sources']];dates=[value for value in dates if value]
        health[field]=choose(dates).isoformat() if dates else None
    delays=sorted(item['publicationLagSeconds'] for item in result['candidates'] if item.get('publicationLagSeconds') is not None)
    health['discoveryLatency']={'sampleCount':len(delays),'medianSeconds':delays[len(delays)//2] if delays else None,'basis':'Time from publisher publication timestamp to first observed arrival since the fixed source baseline. Initial or migrated backlog, pre-baseline backfill, updated-only timestamps and future dates are excluded. Delayed publisher indexing is included; this is not event-to-discovery or competitor latency.'}
    write_json(DIST/'source-status.json',health)
    print(json.dumps({'candidates':len(result['candidates']),'eligible':sum(x['reviewStatus']=='source_excerpt' for x in result['candidates']),'healthySources':healthy,'totalSources':len(FEEDS)}))
    readable=[item for item in result['candidates'] if not set(item['holdReasons']) & {'source_not_allowed','missing_publication_date','outside_freshness_window','title_length','unexpected_source_text'}]
    # Only attributed titles and links enter the reader. Publisher excerpts stay local.
    reporting=write_reporting(readable,result['sources'],result['retrievedAt'])
    # Desk consumers read this single atomic record, never a half-published
    # candidate/report pair. Legacy viewer files remain independently atomic.
    write_json(WORK/'runs'/'intake-snapshot.json',{'schema':1,'checkedAt':result['retrievedAt'],'candidates':result,'reporting':reporting,'sourceHealth':health})
    if not healthy:raise RuntimeError('All approved sources are unavailable; the current edition is retained')
    import scriptdesk
    scriptdesk.prepare_queue(readable,reporting['items'],WORK/'runs')
    return result

def record_discovery(result):
    """Retain discovery clocks across feed rotation; bootstrap is not latency."""
    path=WORK/'runs'/'report-discovery.json'
    try:ledger=json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:ledger={}
    if not isinstance(ledger,dict):raise ValueError('Discovery ledger is unreadable; preserve its history')
    try:prior={item['id']:item for item in json.loads((DIST/'reporting.json').read_text(encoding='utf-8'))['items']}
    except (OSError,ValueError,KeyError):prior={}
    health={source['id']:source for source in result['sources']}
    for item in result['candidates']:
        source=health[item['sourceId']];old=ledger.get(item['id']);previous=prior.get(item['id'],{})
        observed=source.get('lastSuccess') if source.get('attempted') and source['status'] in ('ok','unchanged') else result['retrievedAt']
        if old is None:
            baseline_at=date_value(source.get('discoveryBaselineAt'))
            baseline=source.get('initialDiscovery') or bool(previous) or not source.get('attempted') or not baseline_at
            published=date_value(item.get('publishedTime'))
            backfill=bool(published and baseline_at and published<baseline_at)
            old={'firstSeenAt':previous.get('firstSeenAt') or observed,'firstRevisionSeenAt':previous.get('lastChangedAt') or previous.get('firstSeenAt') or observed,'contentHash':item['contentHash'],'discoveryKind':'baseline' if baseline else 'backfill' if backfill else 'arrival','discoveryVersion':DISCOVERY_VERSION,'firstPublishedTime':item.get('publishedTime'),'firstSourceTimeKind':item.get('sourceTimeKind')}
        else:
            # Older collectors did not know whether an existing feed/cache was
            # already baselined. Preserve their clocks, not unprovable latency.
            if old.get('discoveryVersion')!=DISCOVERY_VERSION:
                old={**old,'discoveryVersion':DISCOVERY_VERSION,'discoveryKind':'baseline','firstPublishedTime':item.get('publishedTime'),'firstSourceTimeKind':item.get('sourceTimeKind')}
            if old.get('contentHash')!=item['contentHash']:
                old={**old,'contentHash':item['contentHash'],'firstRevisionSeenAt':observed}
        item.update({key:old[key] for key in ('firstSeenAt','firstRevisionSeenAt','discoveryKind')})
        published=date_value(old.get('firstPublishedTime'));discovered=date_value(old['firstSeenAt'])
        item['publicationLagSeconds']=round((discovered-published).total_seconds(),1) if published and discovered and published<=discovered and old['discoveryKind']=='arrival' and old.get('firstSourceTimeKind')=='published' else None
        ledger[item['id']]=old
    write_json(path,ledger)

def retained_intake():
    path=WORK/'runs'/'intake-snapshot.json'
    if not path.exists():raise RuntimeError('No completed intake check is available yet')
    snapshot=json.loads(path.read_text(encoding='utf-8'))
    if snapshot.get('schema')!=1 or not isinstance(snapshot.get('candidates',{}).get('candidates'),list):raise ValueError('The intake snapshot is invalid')
    if not snapshot.get('sourceHealth',{}).get('healthy'):raise RuntimeError('No healthy sources in the completed intake check')
    checked=date_value(snapshot.get('checkedAt'))
    if not checked or not 0<=(datetime.now(timezone.utc)-checked).total_seconds()<300:raise RuntimeError('The completed intake check is stale; media production waits for source gathering')
    return snapshot['candidates']

def write_reporting(readable,sources,checked_at):
    path=DIST/'reporting.json'
    try:previous={item['id']:item for item in json.loads(path.read_text(encoding='utf-8'))['items']}
    except (OSError,ValueError,KeyError):previous={}
    health={source['id']:source for source in sources};items=[]
    for item in readable:
        prior=previous.get(item['id'],{});source=health[item['sourceId']]
        report={key:item[key] for key in ('id','topic','topicLabel','title','publishedAt','publishedTime','dateLabel','source','publisherGroup')}
        report['editorial']=item.get('editorial') or editorial.assess(item)
        report.update(version=item['contentHash'],firstSeenAt=item.get('firstSeenAt',prior.get('firstSeenAt',checked_at)),lastChangedAt=prior.get('lastChangedAt'),sourceId=item['sourceId'],sourceLastSuccess=source.get('lastSuccess'),sourceAvailable=source['status']!='unavailable')
        report.update({key:item.get(key) for key in ('firstRevisionSeenAt','discoveryKind','publicationLagSeconds','sourceTimeKind','sourceUpdatedAt','local','market','originalReporting','owner','alert','filing','discoveryOnly')})
        if prior.get('version') and prior['version']!=report['version']:report['lastChangedAt']=checked_at
        items.append(report)
    items,grouping=coverage.group_reports(items,previous)
    items.sort(key=lambda item:item['publishedTime'] or item['publishedAt'],reverse=True)
    version=hashlib.sha256(json.dumps([(s['id'],s['version'],s['publishedTime'],s.get('editorial'),s.get('coverage')) for s in items],ensure_ascii=False).encode()).hexdigest()
    result={'checkedAt':checked_at,'version':version,'editorialPolicy':'us-impact-v2','items':items,'coverageAudit':grouping,'selectionAudit':{'available':len(items),'suppressed':sum(bool(s['editorial']['suppressed']) for s in items),'domesticAvailable':sum(bool(s['editorial']['domestic']) for s in items),'eventGroups':len({s['coverage']['id'] for s in items})}}
    write_json(path,result)
    return result

def balanced_choices(items,existing,limit,seen_urls=()):
    known={canonical_url(story['source']['url']) for story in existing}|set(seen_urls)
    pool=sorted([item for item in items if item['reviewStatus']=='source_excerpt' and canonical_url(item['source']['url']) not in known],key=lambda item:item.get('publishedAt') or '',reverse=True)
    topic_counts={topic:sum(story['topic']==topic for story in existing) for topic in TOPICS};publishers=set();chosen=[]
    while pool and len(chosen)<limit:
        pool.sort(key=lambda item:(item['publisherGroup'] in publishers,topic_counts[item['topic']]))
        item=pool.pop(0);chosen.append(item);publishers.add(item['publisherGroup']);topic_counts[item['topic']]+=1
    return chosen

def published_index():
    path=WORK/'runs'/'published-index.json'
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        known={}
        for archive in (WORK/'runs'/'editions').glob('*.json'):
            try:
                for story in json.loads(archive.read_text(encoding='utf-8'))['stories']:known[canonical_url(story['source']['url'])]=story.get('contentHash')
            except (OSError,ValueError,KeyError):continue
        return known

def retain_rotation(stories):
    retained=[];counts={}
    ordered=sorted(stories,key=lambda story:story.get('publishedAt') or story.get('eventDate') or '',reverse=True)
    for story in ordered:
        topic=story['topic'];counts.setdefault(topic,0)
        if counts[topic]<4:retained.append(story);counts[topic]+=1
    return retained[:24]

def ffmpeg():
    configured=os.environ.get('CURRENT_FFMPEG')
    if configured:return configured
    if shutil.which('ffmpeg'):return shutil.which('ffmpeg')
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:raise RuntimeError('Set CURRENT_FFMPEG to a local FFmpeg executable')

def media_duration(path):
    result=subprocess.run([ffmpeg(),'-hide_banner','-i',str(path)],capture_output=True,text=True)
    match=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',result.stderr)
    if not match:raise ValueError(f'Cannot read media duration: {path.name}')
    h,m,s=map(float,match.groups());return h*3600+m*60+s

def decode(path):
    if not path.is_file() or path.stat().st_size<1000:raise ValueError(f'Missing or empty media: {path.name}')
    result=subprocess.run([ffmpeg(),'-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True,timeout=120)
    if result.returncode or result.stderr.strip():raise ValueError(f'Media decode failed: {path.name}')

def asset(value):
    if not isinstance(value,str) or not value.startswith('assets/'):raise ValueError('Invalid media path')
    path=(DIST/value).resolve()
    if not path.is_relative_to((DIST/'assets').resolve()):raise ValueError('Media path escaped assets')
    return path

def script_hash(story):
    return hashlib.sha256(story['script'].encode('utf-8')).hexdigest()

def visual_registry():
    try:return json.loads((WORK/'visuals.json').read_text(encoding='utf-8'))['visuals']
    except FileNotFoundError:return {}

def check_visual(story):
    visual=story.get('visual',{})
    if visual.get('scope')!='story' or visual.get('storyId')!=story['id'] or not visual.get('reviewedAt'):
        raise ValueError('A reviewed bespoke story visual is required')
    if visual.get('scriptSha256')!=script_hash(story):raise ValueError('Visual does not match current script')
    if not visual.get('alt') or not story.get('visualDisclosure'):raise ValueError('Visual description and disclosure required')
    for kind in ('image','video'):
        path=asset(story.get(kind))
        if visual.get(kind)!=story.get(kind) or not path.is_file() or visual.get(kind+'Sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f'Story {kind} hash mismatch')
    return True

def attach_visual(story,registry=None):
    registry=visual_registry() if registry is None else registry
    visual=registry.get(story['id'])
    if not visual:raise ValueError('Awaiting a reviewed bespoke story visual')
    story.update(image=visual['image'],video=visual['video'],visual=copy.deepcopy(visual),visualDisclosure=visual['disclosure'])
    check_visual(story)

def check_story(story,decode_media=True):
    if story.get('reviewStatus') not in ('verified','source_excerpt'):raise ValueError('Story is not editorially eligible')
    validate_url(story['source']['url'])
    if story.get('reviewStatus')=='source_excerpt':
        source_feed=next((feed for feed in FEEDS if feed['id']==story.get('sourceId')),None)
        if source_feed and source_feed['mode']!='automatic':raise ValueError('Publisher requires review before narration')
        if story.get('holdReasons'):raise ValueError('Held source excerpt')
        if story.get('sourceExcerpt','') not in story['script']:raise ValueError('Source excerpt was altered')
        if not story['script'].startswith(story['source']['name']+' reports. '):raise ValueError('Missing source attribution')
    if not 25<=len(story['script'].split())<=160:raise ValueError('Script length outside segment limits')
    if not story.get('publishedAt') and not story.get('eventDate'):raise ValueError('No story date')
    if not story.get('visualDisclosure'):raise ValueError('No generated-visual disclosure')
    image=asset(story['image'])
    if not image.is_file():raise ValueError('Illustration unavailable')
    video=asset(story['video'])
    if decode_media:decode(video)
    for voice in VOICES:
        track=story['voices'][voice];path=asset(track['audio']);duration=float(track['duration'])
        if track.get('scriptSha256')!=hashlib.sha256(story['script'].encode('utf-8')).hexdigest():raise ValueError('Narration does not match current script')
        if not path.is_file() or track.get('sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('Narration file hash mismatch')
        if not 10<=duration<=100:raise ValueError('Unexpected narration duration')
        timings=track.get('captions',[])
        if not timings:raise ValueError('No timed captions')
        last=0
        for caption in timings:
            if caption['start']<last-.05 or caption['end']<=caption['start'] or caption['end']>duration+1 or not caption['text'].strip():raise ValueError('Invalid caption timing')
            last=caption['end']
        if last<duration*.75:raise ValueError('Caption coverage incomplete')
        if ' '.join(c['text'] for c in timings).split()!=story['script'].split():raise ValueError('Captions do not reproduce the narration script')
        if decode_media:
            decode(path)
            if abs(media_duration(path)-duration)>1:raise ValueError('Narration duration mismatch')
    check_visual(story)
    return True

def publish(edition,decode_media=True):
    if not edition.get('stories'):raise ValueError('Refusing an empty edition')
    identifiers=set();images=set()
    for story in edition['stories']:
        if story['id'] in identifiers:raise ValueError('Duplicate story')
        identifiers.add(story['id']);check_story(story,decode_media);story['status']='withdrawn' if story.get('withdrawnAt') else 'ready'
        digest=story['visual']['imageSha256']
        if digest in images:raise ValueError('Different stories cannot share the same illustration')
        images.add(digest)
    edition['builtAt']=stamp();edition['productionMode']='source-checked edition'
    previous=DIST/'edition.json'
    if previous.exists():
        digest=hashlib.sha256(previous.read_bytes()).hexdigest()[:12]
        archive=WORK/'runs'/'editions'/f'{digest}.json';archive.parent.mkdir(parents=True,exist_ok=True)
        if not archive.exists():shutil.copy2(previous,archive)
    write_json(previous,edition)
    known=published_index()
    for story in edition['stories']:known[canonical_url(story['source']['url'])]=story.get('contentHash')
    write_json(WORK/'runs'/'published-index.json',known)
    print(json.dumps({'published':str(previous),'stories':len(edition['stories']),'builtAt':edition['builtAt']}))

async def narrate(story,voice,run):
    from speech import synthesize
    script_hash=hashlib.sha256(story['script'].encode('utf-8')).hexdigest()[:12]
    filename=f'{story["id"]}-{script_hash}-{voice}.mp3';output=run/filename
    metadata=synthesize(story['script'],voice,output)
    shutil.copy2(output,DIST/'assets'/filename)
    return {key:metadata[key] for key in ['duration','captions','provider','voice','scriptSha256','modelSha256','captionTiming','sha256']} | {'audio':f'assets/{filename}'}

def withdraw_changed(stories,candidates):
    changes=[]
    by_url={canonical_url(item['source']['url']):item for item in candidates}
    for story in stories:
        updated=by_url.get(canonical_url(story['source']['url']))
        if updated and story.get('contentHash') and story['contentHash']!=updated['contentHash'] and not story.get('withdrawnAt'):
            story.update(withdrawnAt=stamp(),withdrawalReason='Source text changed; a reviewed replacement is required.');changes.append(story['id'])
    return changes

async def automatic(limit,skip_collect=False):
    intake=retained_intake() if skip_collect else collect();existing=json.loads((DIST/'edition.json').read_text(encoding='utf-8'))
    changes=withdraw_changed(existing['stories'],intake['candidates'])
    candidates=balanced_choices(intake['candidates'],existing['stories'],len(intake['candidates']),published_index())
    registry=visual_registry();ready=[];requests=[]
    for item in candidates:
        try:attach_visual(item,registry);ready.append(item)
        except ValueError as exc:
            requests.append({key:item[key] for key in ('id','topic','title','script','source')} | {'scriptSha256':script_hash(item),'reason':str(exc)})
    write_json(WORK/'runs'/'visual-requests.json',{'checkedAt':stamp(),'pending':requests})
    choices=ready[:limit]
    if not choices:
        if changes:
            publish(existing);write_json(WORK/'runs'/'source-changes.json',{'checkedAt':stamp(),'withdrawn':changes})
            print('Changed source segments were withdrawn pending review.')
        else:print(f'No complete new segments; {len(requests)} candidates await bespoke artwork. The existing edition is unchanged.')
        return
    run=WORK/'runs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');run.mkdir(parents=True,exist_ok=True)
    completed=[];held=[]
    for item in choices:
        try:
            item['voices']={}
            for voice in VOICES:item['voices'][voice]=await narrate(item,voice,run)
            check_story(item);item['status']='ready';completed.append(item)
        except Exception as exc:held.append({'id':item['id'],'reason':str(exc)} )
    write_json(run/'production-report.json',{'completed':[s['id'] for s in completed],'held':held})
    if completed:
        # Retain recent coverage across topics; one busy feed cannot evict every topic.
        publish({'edition':datetime.now(timezone.utc).date().isoformat(),'stories':retain_rotation(existing['stories']+completed)})
    elif changes:publish(existing)
    else:raise RuntimeError('No complete new segments. The existing edition is retained; see the production report.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['collect','check','publish','auto']);parser.add_argument('--input',type=Path);parser.add_argument('--limit',type=int,default=2);parser.add_argument('--skip-collect',action='store_true');args=parser.parse_args()
    if args.command=='collect':
        collect()
    elif args.command=='auto':
        with production_lock():asyncio.run(automatic(max(1,min(args.limit,6)),skip_collect=args.skip_collect))
    elif args.command=='publish':
        if not args.input:parser.error('publish requires --input')
        with production_lock():publish(json.loads(args.input.read_text(encoding='utf-8')))
    else:
        edition=json.loads((DIST/'edition.json').read_text(encoding='utf-8'))
        for story in edition['stories']:check_story(story)
        print(json.dumps({'valid':True,'stories':len(edition['stories'])}))

if __name__=='__main__':main()
