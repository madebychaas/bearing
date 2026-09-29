"""Conservative event grouping. Similarity is discovery metadata, never verification."""
import hashlib,re,unicodedata
from datetime import datetime
from urllib.parse import urlsplit,parse_qsl,urlencode

STOP=set('a an and are as at be been by for from has have how in into is it its of on or over that the their this to was were what when which who why will with new says said reports report means'.split())
ALIASES={'rejects':'reject','rejected':'reject','fails':'fail','failed':'fail','increases':'increase','decreases':'decrease','raised':'raises','weakens':'rollback','weaken':'rollback','rollbacks':'rollback','rolling':'roll','standards':'standard','drivers':'vehicle','cars':'vehicle','vehicles':'vehicle','passes':'pass','passed':'pass','approves':'approve','approved':'approve','rules':'rule','prices':'price','cuts':'cut','taxes':'tax'}

def url_key(value):
    u=urlsplit(value);query=[(k,v) for k,v in parse_qsl(u.query) if not k.lower().startswith('utm_') and k.lower() not in ('ref','source','fbclid','gclid')]
    return f'{u.hostname or ""}{u.path.rstrip("/")}?{urlencode(sorted(query))}'

def words(value):
    value=unicodedata.normalize('NFKC',value).lower().replace('’',"'")
    value=re.sub(r'fuel (?:economy|efficiency)','vehicleefficiency',value)
    return {ALIASES.get(w,w) for w in re.findall(r'[a-z0-9]+',re.sub(r"\b([a-z]+)'s\b",r'\1',value)) if w not in STOP and len(w)>1}

def timestamp(item):
    try:return datetime.fromisoformat(item.get('publishedTime','').replace('Z','+00:00')).timestamp()
    except (ValueError,TypeError,AttributeError):return None

def same_event(a,b):
    if url_key(a['source']['url'])==url_key(b['source']['url']):return 'same canonical source URL'
    ta,tb=timestamp(a),timestamp(b)
    if ta is None or tb is None or abs(ta-tb)>36*3600:return None
    left,right=words(a['title']),words(b['title'])
    if not left or not right:return None
    # Opposing actions and differing figures may be a distinct development, not duplicate coverage.
    for positive,negative in [('approve','reject'),('pass','fail'),('increase','decrease'),('raises','cut')]:
        if (positive in left and negative in right) or (negative in left and positive in right):return None
    numbers=lambda v:{w for w in v if w.isdigit()}
    if numbers(left)!=numbers(right):return None
    if (left&{'not','no','never','without'})!=(right&{'not','no','never','without'}):return None
    shared=len(left&right);union=len(left|right)
    if left==right:return 'equivalent headline tokens'
    if shared>=4 and shared/union>=.62 and shared/min(len(left),len(right))>=.8:return 'strong headline overlap within 36 hours'
    return None

def group_reports(items,previous=None):
    previous=previous or {};groups=[];audit=[]
    # Match a single representative, not transitive chains that merge unrelated angles.
    for item in sorted(items,key=lambda s:(-(s.get('editorial',{}).get('score',0)),s['id'])):
        for group in groups:
            reason=same_event(group[0],item)
            if reason:
                group.append(item);audit.append({'kept':group[0]['id'],'grouped':item['id'],'reason':reason});break
        else:groups.append([item])
    output=[];claimed=set()
    for group in groups:
        retained=sorted({previous.get(s['id'],{}).get('coverage',{}).get('id') for s in group}-{None}-claimed)
        identity=retained[0] if retained else 'event-'+hashlib.sha256(min(url_key(s['source']['url']) for s in group).encode()).hexdigest()[:14]
        if identity in claimed:identity='event-'+hashlib.sha256(json_identity(group).encode()).hexdigest()[:14]
        claimed.add(identity)
        sources={url_key(s['source']['url']):{**s['source'],'reportId':s['id'],'publishedTime':s.get('publishedTime')} for s in group}
        coverage={'id':identity,'representativeId':group[0]['id'],'sourceCount':len({s.get('publisherGroup') or s['source']['name'] for s in group}),'sources':list(sources.values()),'method':'Conservative headline grouping; not independent corroboration'}
        output.extend({**s,'coverage':coverage} for s in group)
    return output,audit


def json_identity(group):return '|'.join(sorted(s['id']+':'+s['title'] for s in group))
