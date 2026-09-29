"""Transparent U.S. consumer-impact selection; not a fact-verification system."""
import re
from datetime import datetime, timezone

US_PUBLISHERS={'AP','Associated Press','CNN','Axios','CNBC','NPR','PBS NewsHour','KERA','Federal Reserve','FTC','NASA','NOAA','USGS','NIST','NSF'}
LEADS={'AP','Associated Press','CNN','Axios'}
MONEY=re.compile(r'\b(consumer\w*|inflation|prices?|costs?|afford\w*|mortgage\w*|rent\w*|housing|insurance|wages?|jobs?|employment|unemployment|layoffs?|tariffs?|tax\w*|benefits?|social security|medicare|medicaid|student loans?|tuition|electricity|utility|utilities|gasoline|fuel|grocer\w*|debt|credit|interest rates?|federal reserve|fed rate|recession|economy|economic|retirement|pensions?|savings?|recalls?(?! petitions?| elections?)|scams?|fraud|fees?)\b',re.I)
POLICY=re.compile(r'\b(law|legislation|bill|rule|ruling|court|regulat\w*|funding|budget|shutdown|voting|ballots?|rights|infrastructure|trade|immigration|health care|healthcare|education|school\w*|water|energy|standards?|public safety)\b',re.I)
ACTION=re.compile(r'\b(passes?|passed|signs?|signed|enacts?|enacted|approves?|approved|blocks?|blocked|overturns?|overturned|rules?|ruled|takes? effect|effective|cuts?|raises?|raised|rollbacks?|rolls? back|weakens?|expands?|ends?|launches?|changes?|recalls?|bans?|orders?|extends?)\b',re.I)
CHATTER=re.compile(r'\b(slams?|blasts?|feuds?|sparring|claps? back|hits? back|trades? barbs|mudslinging|insults?|taunts?|polls?|polling|approval rating|horse race|fundrais\w*|campaign cash|daddy issues|fearmongering|rips?)\b',re.I)
FOREIGN_LOCAL=re.compile(r'\b(NHS|UK|U\.K\.|Britain|British|Westminster|Albanese|Australia|Australian|Modi|Bundestag|Littler|Grand Prix|Orban|Hungary)\b',re.I)
US_LINK=re.compile(r'\b(U\.S\.|US|American\w*|United States|U\.S\.-|Congress|Senate|Federal Reserve|Washington|Trump|Biden|Medicare|Medicaid|dollar|Wall Street)\b',re.I)

def assess(item,feed=None):
    feed=feed or {};title=item.get('title','');publisher=feed.get('publisherGroup') or item.get('publisherGroup') or item.get('source',{}).get('name','')
    domestic=feed.get('domestic',publisher in US_PUBLISHERS)
    money=bool(MONEY.search(title));policy=bool(POLICY.search(title));action=bool(ACTION.search(title))
    chatter=bool(CHATTER.search(title)) and not (policy and action)
    foreign_local=(bool(FOREIGN_LOCAL.search(title)) or not domestic) and not bool(US_LINK.search(title)) and not bool(re.search(r'\b(oil|global|supply chain|trade deal)\b',title,re.I))
    focus='consumer-economy' if money else 'policy-impact' if policy and action else 'general'
    roundup=bool(re.search(r'\b(newsletter|morning roundup|evening roundup|daily digest|top headlines|news quiz)\b|[.!?]\s+And[, ]',title,re.I))
    dimensions={'domesticSource':35 if domestic else 0,'publisherPriority':18 if publisher in LEADS else 9 if publisher in {'CNBC','NPR','PBS NewsHour'} else 0,'consumerImpact':35 if money else 0,'concretePolicy':25 if policy and action else 0,'roundupPenalty':-80 if roundup else 0}
    score=sum(dimensions.values())
    if item.get('topic') in ('space','nature','culture','sport'):score-=15
    if foreign_local:score-=45
    if chatter:score-=90
    return {'version':'us-impact-v2','dimensions':dimensions,'roundup':roundup,'domestic':bool(domestic),'publisher':publisher,'focus':focus,'score':score,'suppressed':chatter or roundup,'reason':'Multi-story roundup; select individual reports' if roundup else 'Political sparring without a concrete policy action' if chatter else 'Household costs, consumer protection or economic impact' if money else 'A policy decision with practical consequences' if policy and action else 'Supporting coverage','foreignLocal':foreign_local}

def rank(items,maximum=32):
    pool=[{**item,'editorial':item.get('editorial') or assess(item)} for item in items]
    pool=[s for s in pool if not s['editorial']['suppressed'] and not s['editorial']['foreignLocal']]
    unique={};
    for item in sorted(pool,key=lambda s:s['editorial']['score'],reverse=True):unique.setdefault(item.get('coverage',{}).get('id',item['id']),item)
    pool=list(unique.values())
    pool.sort(key=lambda s:(s['editorial']['score'],s.get('publishedTime') or ''),reverse=True)
    # At most one international-publisher item per ten; never fill a shortage with foreign filler.
    domestic=[s for s in pool if s['editorial']['domestic']];foreign=[s for s in pool if not s['editorial']['domestic'] and not s['editorial']['foreignLocal']]
    selected=[];counts={}
    while domestic and len(selected)<maximum:
        # Reduce publisher repetition without forcing low-impact topics into the lead.
        best=max(range(len(domestic)),key=lambda i:domestic[i]['editorial']['score']-counts.get(domestic[i]['editorial']['publisher'],0)*18)
        s=domestic.pop(best);selected.append(s);p=s['editorial']['publisher'];counts[p]=counts.get(p,0)+1
    allowance=min(maximum//10,len(selected)//9,len(foreign))
    if allowance:
        selected=selected[:maximum-allowance]+foreign[:allowance]
    return selected
