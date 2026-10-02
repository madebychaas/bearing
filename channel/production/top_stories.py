"""Three distinct, consequential current leads from the national assignment desk.

This is an editorial shortlist of available reporting, not a claim of complete
coverage or verified production approval. Importance is a bounded rubric of
scope and consequence; publication recency only breaks ties within that rubric.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from assignment import ZONE, moment

MAX_AGE = timedelta(hours=24)
SOURCE_MAX_AGE = timedelta(hours=2)
REVIEW_MAX_AGE = timedelta(hours=4)
STOP = set('the a an and or to of in on for as with at by from is are was were has have its new us says report reports'.split())
EXCLUDE = re.compile(r'\b(?:opinion|commentary|sponsored|newsletter|news quiz|coupon|shopping deals|slams?|feud|hits back|responds?|reacts?|trades barbs|approval rating|polls?|movie night|forecast discussion)\b', re.I)
PREVIEW = re.compile(r'\b(?:will|could|may|expected to|set to|weighs|threatens?|warns of|plans? to|to send|to release|proposal|proposed)\b', re.I)
RESULT = re.compile(r'\b(?:added|rose|rises?|fell|falls?|dropped|cuts?|cut|signed|enacted|ruled|overturned|blocked|recalled|closed|killed|struck|reopened|announced|approved|issued|launched|declared)\b', re.I)
US = re.compile(r'\b(?-i:US)\b|\bU\.S\.|\b(?:United States|Americans?|nationwide|federal|Congress|Supreme Court|Medicare|Medicaid|Social Security)\b', re.I)


def evidence_hash(report):
    """Bind authored display copy to the exact source claims, identity and clock."""
    keys = ('id', 'sourceId', 'title', 'excerpt', 'url', 'publishedAt', 'sourceTimeKind')
    payload = {key: report.get(key) for key in keys}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _has(pattern, text):
    return bool(re.search(pattern, text, re.I))


def _impact(report):
    """Return a single consequence class, never cumulative keyword points."""
    title = report.get('title', '')
    text = title + ' ' + report.get('excerpt', '')
    national = bool(US.search(text))
    # One national institution in a local case does not establish wide impact.
    if _has(r'\b(?:enforcement action|indictment|charged with|fundraising campaign|single bank|photo|image article)\b', text):
        return None
    if _has(r'\b(?:nationwide|millions|multi-state|multiple states)\b', text) and _has(r'\b(?:emergency|evacuat\w*|power outage|water contamination|recall|outbreak)\b', text):
        return 6, 'national-safety', 'A current hazard or disruption is reported at national scale.'
    if _has(r'\b(?:jobs report|nonfarm payrolls|unemployment rate|employers added|U\.S\. added|labor market|job market)\b', text) and _has(r'\b(?:jobs?|payrolls?|unemployment|hiring)\b', title):
        return 5, 'us-jobs', 'New national labor-market figures help explain the outlook for work and income.'
    if _has(r'\b(?:inflation|consumer price index|PCE|gross domestic product|GDP)\b', title) and (national or _has(r'\b(?:BEA|BLS|Commerce Department|Bureau of)\b', text)):
        return 5, 'us-prices' if _has(r'inflation|price index|PCE', title) else 'us-growth', 'New national economic figures affect the household and economic outlook.'
    if _has(r'\b(?:Federal Reserve|Fed)\b', title) and _has(r'\b(?:interest rates?|rate cut|rate hike|raises rates|cuts rates)\b', title):
        return 5, 'us-interest-rates', 'A monetary-policy decision has broad consequences for borrowing and the economy.'
    if _has(r'\b(?:mortgage|home loan)\b', title) and (national or _has(r'\b(?:Freddie Mac|30.year|thirty.year)\b', text)) and _has(r'\b(?:rates?|average|highest|lowest|hits?|climbs?|rises?|falls?)\b', text):
        return 4, 'us-mortgages', 'The latest national mortgage benchmark helps explain the cost of buying a home.'
    if national and _has(r'\b(?:shutdown|Social Security|Medicare|Medicaid|student loans?|tax credit|taxes|voting rights|citizenship|tariffs?|Supreme Court)\b', title):
        return 4, 'national-policy', 'The reported decision concerns a national programme, right or household cost.'
    if _has(r'\b(?:oil|diesel|crude|gasoline|fuel)\b', title) and _has(r'\b(?:prices?|suppl\w*|reserves?|stocks|exports?|Brent)\b', text):
        # A UK pump-price story alone is not an American national lead.
        if _has(r'\b(?:UK|Britain|British|litre|pound)\b|£', title) and not US.search(report.get('excerpt', '')):
            return None
        return 4, 'energy-supply', 'A fuel-supply or price development has broad economic consequences; retail effects still need verification.'
    if national and _has(r'\b(?:troops|aircraft carrier|carrier group|missile|military|ceasefire|strikes)\b', title):
        return 4, 'us-security', 'A reported U.S. security development has consequences beyond a single location.'
    if _has(r'\b(?:inspector general|watchdog|oversight|federal housing)\b', text) and _has(r'\b(?:cuts?|slash\w*|abolish\w*|fired|removed|dismantl\w*)\b', title):
        return 3, 'public-oversight', 'A concrete change to national oversight affects public accountability.'
    # Do not fill scarce hero slots with institution-name recognition, a routine
    # mission launch or an isolated case when national consequence is unclear.
    return None


def _usable(report, now, max_age=MAX_AGE):
    at = moment(report.get('publishedAt'))
    checked = moment(report.get('sourceLastSuccess'))
    return bool(report.get('available') and not report.get('revisionMismatch') and
                not report.get('suppressed') and not report.get('local') and not report.get('foreignLocal') and
                report.get('sourceTimeKind', 'published') not in ('filed', 'updated') and
                at and timedelta(0) <= now-at <= max_age and checked and timedelta(0) <= now-checked <= SOURCE_MAX_AGE)


def _sentence(excerpt):
    """Return a complete short source sentence, or no summary; never truncate."""
    clean = ' '.join(str(excerpt or '').split())
    if not clean or '…' in clean or '[…]' in clean:
        return ''
    if len(clean) <= 210 and re.search(r'[.!?][”"\']?$', clean):
        return clean
    # Require a capitalized next sentence. Do not split U.S., initials or decimals.
    for match in re.finditer(r'[.!?][”"\']?(?=\s+[A-Z“"]|$)', clean):
        end = match.end()
        if not 25 <= end <= 210:
            continue
        prefix = clean[:end]
        if re.search(r'(?:\b[A-Z]\.){2,}$|\b(?:Mr|Mrs|Ms|Dr|Sen|Rep|St)\.$', prefix):
            continue
        return prefix
    return ''


def _tokens(value):
    return set(re.findall(r'[a-z0-9]+', value.lower()))-STOP


def _duplicates(one, two):
    if one['family'] == two['family'] and one['family'] in ('us-jobs', 'us-prices', 'us-growth', 'us-interest-rates', 'us-mortgages', 'energy-supply'):
        return True
    # Other policy/security reports need actual shared subject words; a broad
    # category is not enough to collapse distinct national developments.
    left, right = _tokens(one['report']['title']), _tokens(two['report']['title'])
    return bool(left and right and len(left & right) / min(len(left), len(right)) >= .72)


def _authored(event, report, authored, now):
    items = authored.get('items', []) if isinstance(authored, dict) else []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or item.get('eventId') != event['id'] or item.get('sourceId') != report['id']:
            continue
        reviewed, expires = moment(item.get('reviewedAt')), moment(item.get('expiresAt'))
        if not reviewed or not expires or not reviewed <= now < expires or expires-reviewed > REVIEW_MAX_AGE:
            continue
        if item.get('evidenceHash') != evidence_hash(report):
            continue
        headline, summary = item.get('headline'), item.get('summary', '')
        if not isinstance(headline, str) or not 8 <= len(headline.strip()) <= 160 or not isinstance(summary, str) or len(summary) > 240:
            continue
        result = {'headline': headline.strip(), 'summary': summary.strip(), 'copyKind': 'editorial',
                  'reviewedAt': item['reviewedAt'], 'expiresAt': item['expiresAt']}
        supporting = []
        sources = item.get('supportingEvidence', [])
        for source in sources if isinstance(sources, list) else []:
            if not isinstance(source, dict):
                continue
            checked = moment(source.get('checkedAt'))
            try:
                url = urlsplit(str(source.get('url', '')))
            except ValueError:
                continue
            if (url.scheme == 'https' and url.hostname and url.hostname not in ('localhost', '127.0.0.1', '::1') and
                    not url.username and not url.password and checked and timedelta(0) <= reviewed-checked <= timedelta(hours=1) and
                    isinstance(source.get('excerpt'), str) and 20 <= len(source['excerpt']) <= 2000 and
                    isinstance(source.get('publisher'), str) and source['publisher'].strip()):
                supporting.append({key: source.get(key) for key in ('url', 'publisher', 'title', 'checkedAt', 'excerpt')})
        peg = item.get('verifiedPeg') or {}
        peg = peg if isinstance(peg, dict) else {}
        at = moment(peg.get('at'))
        if (supporting and isinstance(item.get('whyNow'), str) and 15 <= len(item['whyNow']) <= 500 and
                peg.get('kind') in ('confirmed-development', 'continuing-impact') and at and
                peg.get('clockKind') in (None, 'published', 'observed', 'report-published') and
                timedelta(0) <= now-at <= timedelta(hours=48) and isinstance(peg.get('reason'), str) and len(peg['reason']) >= 15):
            result.update(supportingEvidence=supporting, verifiedPeg={key: peg[key] for key in ('kind', 'at', 'reason')}, whyNow=item['whyNow'])
            if peg.get('clockKind'):
                result['verifiedPeg']['clockKind'] = peg['clockKind']
            if item.get('editorialPriority') in (1, 2, 3) and not isinstance(item['editorialPriority'], bool):
                result['editorialPriority'] = item['editorialPriority']
            result['carryForward'] = item.get('carryForward') is True
        art = item.get('art') or item.get('image') or {}
        art = art if isinstance(art, dict) else {}
        try:
            path = urlsplit(str(art.get('url', '')))
        except ValueError:
            path = urlsplit('')
        if (not path.scheme and not path.netloc and not path.query and not path.fragment and
                re.fullmatch(r'/assets/top-stories/[a-zA-Z0-9_-]+\.(?:png|jpg|jpeg|webp)', path.path) and
                art.get('kind') == 'illustration' and isinstance(art.get('alt'), str) and art['alt'].strip()):
            result['art'] = {'url': path.path, 'alt': art['alt'].strip()[:240], 'label': 'AI illustration'}
        return result
    return {}


def select(snapshot, authored=None, now=None):
    """Return a source-bound hero payload; never mutate approval or desk state."""
    now = moment(now) or datetime.now(timezone.utc)
    as_of = snapshot.get('asOf') or (snapshot.get('sourceHealth') or {}).get('checkedAt')
    collected = moment(as_of)
    base = {'items': [], 'asOf': as_of, 'selectedAt': now.isoformat().replace('+00:00', 'Z'),
            'status': 'empty', 'selectionMethod': 'National consequence, current development and distinct coverage',
            'disclosure': 'Ranked from current reporting available to Bearing. Selection does not confer production approval.'}
    if not collected or not timedelta(0) <= now-collected <= SOURCE_MAX_AGE or snapshot.get('sourceHealth', {}).get('stale'):
        return {**base, 'status': 'stale', 'message': 'Refreshing the national picture. Current source evidence is not yet available.'}
    candidates = []
    for event in snapshot.get('events', []):
        desk = event.get('assignment') or {}
        peg = desk.get('todayPeg') or {}
        if (desk.get('scope') not in ('national', 'world-impact') or desk.get('lane') not in ('today', 'developing', 'watch') or
                peg.get('kind') in ('source-updated', 'evidence-check', 'public-inspection', 'missing-changed-evidence') or
                event.get('decision', {}).get('action') in ('dismiss', 'watch')):
            continue
        report = next((r for r in event.get('evidence', []) if r.get('id') == peg.get('sourceId')), None)
        if not report:
            continue
        display = _authored(event, report, authored, now)
        reviewed_peg = bool(display.get('supportingEvidence'))
        carry = reviewed_peg and display.get('carryForward') is True and display['verifiedPeg']['kind'] == 'continuing-impact'
        confirmed = reviewed_peg and display['verifiedPeg']['kind'] == 'confirmed-development'
        if desk.get('lane') == 'watch' and not (carry or confirmed):
            continue
        if peg.get('status') != 'candidate' and not (carry or (confirmed and peg.get('status') == 'needs-verification')):
            continue
        if not _usable(report, now, timedelta(hours=48) if carry else MAX_AGE):
            continue
        title, excerpt = report.get('title', ''), report.get('excerpt', '')
        if EXCLUDE.search(title) or (PREVIEW.search(title) and not RESULT.search(title) and not reviewed_peg):
            continue
        # Fail closed on a still-forecast excerpt paired with a released-number headline.
        if re.search(r'\d', title) and _has(r'\b(?:were expected to|was expected to|is expected to|are expected to|ahead of the release|economists expect)\b', excerpt):
            continue
        impact = _impact(report)
        if not impact:
            continue
        tier, family, reason = impact
        at = moment(report['publishedAt'])
        domestic = report.get('domestic') is not False
        # Fine recency is not a substitute for consequence. Today and broad age
        # bands only order otherwise comparable leads, avoiding constant churn.
        key = (tier, 4-display.get('editorialPriority', 4), at.astimezone(ZONE).date() == now.astimezone(ZONE).date(), domestic,
               bool(_sentence(excerpt)), -int((now-at).total_seconds()//10800))
        candidates.append({'event': event, 'report': report, 'tier': tier, 'family': family, 'reason': reason, 'key': key, 'display': display})
    candidates.sort(key=lambda c: tuple(-int(value) for value in c['key'])+(c['event']['id'],))
    distinct = []
    for candidate in candidates:
        if any(_duplicates(candidate, retained) for retained in distinct):
            continue
        distinct.append(candidate)
        if len(distinct) == 3:
            break
    for rank, row in enumerate(distinct, 1):
        report, event = row['report'], row['event']
        item = {'eventId': event['id'], 'rank': rank, 'headline': report['title'], 'summary': _sentence(report.get('excerpt')),
                'sourceId': report['id'], 'publisher': report.get('publisher', ''), 'sourceUrl': report.get('url', ''),
                'publishedAt': report['publishedAt'], 'evidenceHash': evidence_hash(report), 'reason': row['reason'],
                'family': row['family'], 'impactTier': row['tier'], 'copyKind': 'source', 'evidenceIds': [report['id']]}
        item.update(row['display'])
        base['items'].append(item)
    if base['items']:
        base['status'] = 'current'
    if len(base['items']) < 3:
        base['message'] = 'Gathering more distinct national developments with a current, supported news peg.'
    return base
