"""National assignment leads over sourced reporting, never automatic verification.

Publication, first discovery, observed changes and event time are different clocks.
The desk exposes an inspectable news-peg candidate and the question still to answer.
"""
from __future__ import annotations

import copy
import math
import re
from statistics import median
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('America/Chicago')
BEATS = (
    ('economy', 'Economy & work', r'jobs?|payrolls?|wages?|employment|unemployment|inflation|GDP|economy|economic|Federal Reserve|interest rates?|Treasury|layoffs?|trade deficit', 24),
    ('consumer', 'Household & consumer', r'prices?|costs?|mortgages?|rent|housing|insurance|groceries|borrowers?|student loans?|subscriptions?|recalls?|consumer|Social Security|retirement|scams?|fees?', 22),
    ('policy', 'Government & rights', r'Congress|Senate|Supreme Court|federal|White House|President|Trump|voting|election|Medicaid|Medicare|immigration|citizenship|tariffs?|shutdown|regulation|civil rights', 18),
    ('health', 'Health', r'health|FDA|CDC|disease|outbreak|vaccine|drug|hospital|medical|flu|measles', 20),
    ('safety', 'Safety & major weather', r'hurricane|tsunami|earthquake|tornado|wildfire|flood|storm|public safety|terror|cyberattack|outage|aviation|crash', 22),
    ('world', 'World consequences', r'war|ceasefire|Ukraine|Russia|Iran|Israel|Gaza|NATO|China|Middle East|shipping|supply chain|global|oil|energy', 15),
    ('technology', 'Science & technology', r'NASA|space|technology|AI|artificial intelligence|cybersecurity|research|science|Google|Microsoft|Apple|Meta', 12),
)
NATIONAL = re.compile(r'\b(?-i:US)\b|\bU\.S\.(?=\W|$)|\b(?:United States|American\w*|nationwide|national|federal|Congress|Senate|Supreme Court|White House|President|Trump|Federal Reserve|Treasury|Medicare|Medicaid|Social Security|FDA|CDC|SEC|BLS|BEA|NASA|NATO)\b', re.I)
LOCAL = re.compile(r'\b(?:city council|school board|county|sheriff|mayor|local residents|Dallas|Houston|Plano|Austin|Fort Worth|New York City|Chicago|Los Angeles|California|Texas|Florida|Tennessee|Kentucky)\b', re.I)
FOREIGN = re.compile(r'\b(?:Britain|British|UK|NHS|France|French|Germany|German|Australia|India|Pakistan|Brazil|Canada|China|Russia|Ukraine|Israel|Gaza|Iran|Lebanon|Middle East|South Korea|Japan|Europe)\b', re.I)
WORLD_IMPACT = re.compile(r'\b(?:war|ceasefire|nuclear|NATO|global|oil|energy supplies|supply chains?|shipping|tariffs?|trade deal|U\.S\.|United States|Americans?)\b', re.I)
ECONOMIC_SCOPE = re.compile(r'\b(?:inflation|GDP|payrolls?|unemployment|Federal Reserve|Treasury yields|mortgage rates?|Social Security|Medicare|Medicaid|national economy|consumer confidence|jobs report|Nike|Boeing|General Motors|Amazon|Walmart|Apple|Microsoft|Google|Meta)\b', re.I)
DEVELOPMENT = re.compile(r'\b(?:announc\w*|launch\w*|releas\w*|report\w*|approv\w*|block\w*|signs?|signed|passes?|passed|orders?|ordered|rules?|ruled|rulings?|recalls?|recalled|bans?|banned|strikes?|struck|kills?|killed|resigns?|resigned|fires?|fired|cuts?|cut|raises?|raised|rises?|rose|falls?|fell|drops?|dropped|adds?|added|surges?|jump\w*|halts?|halted|shutdown|outage|takes effect|starts?|begins?|ends?|reopens?)\b', re.I)
WATCH = re.compile(r'\b(?:will|expected|scheduled|due|deadline|hearing|proposal|proposed|draft|what to expect|set to|prepares?|plans?|could|may)\b', re.I)
NOISE = re.compile(r'\b(?:newsletter|news quiz|shopping deals|coupon|sponsored|opinion|commentary|Cramer|stocks? to buy|how to play the stock|midterm predictions|polls?|approval rating|trades barbs|slams?|feud|claps back|hits back)\b', re.I)
EXPLAINER = re.compile(r'\b(?:how|tips|what to know|what we know|here.s why|explained|explainer|look back|anniversary|years? ago|in 20(?:0\d|1\d|2[0-5]))\b', re.I)
PAST_DAY = re.compile(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|yesterday|last week|last month)\b', re.I)


def moment(value):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else None
    if not isinstance(value, str) or 'T' not in value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def beat_for(text):
    scores = [(len(re.findall(r'\b(?:'+pattern+r')\b', text, re.I)), weight, key, label)
              for key, label, pattern, weight in BEATS]
    count, weight, key, label = max(scores)
    return (key, label, weight) if count else ('general', 'General reporting', 0)


def report_scope(report, feed):
    title = report.get('title', '')
    text = title + ' ' + ' '.join(report.get('excerpt', '').split()[:60])
    explicit = NATIONAL.search(text)
    if feed.get('id', '').startswith('nhc-'):
        # The agency's Miami dateline and name do not establish U.S. impact.
        body = re.sub(r'NWS\s+National Hurricane Center\s+Miami\s+FL', '', title+' '+report.get('excerpt', ''), flags=re.I)
        impact = re.search(r'(?:hurricane warning|storm surge warning|life-threatening|landfall|evacuat\w*)', body, re.I)
        domestic = re.search(r'\b(?:United States|U\.S\.|Florida|Texas|Louisiana|Mississippi|Alabama|Georgia|Carolinas?|Hawaii|Puerto Rico|Virgin Islands)\b', body, re.I)
        if impact and domestic:
            return 'national', 'A hazard bulletin names a possible U.S. threat; verify the warning area and scale.'
        return 'unestablished', 'Routine tropical monitoring. The agency location is not the storm location; establish a consequential U.S. threat before elevation.'
    alert = report.get('alert') or {}
    if alert:
        if alert.get('severity') == 'Extreme' and re.search(r'hurricane|tsunami', alert.get('event', ''), re.I):
            return 'national', 'An extreme coastal hazard alert warrants assessment of national scale and continuing impact.'
        return 'local', 'A geographically limited alert; retain for verification without filling the national desk with local warnings.'
    local = report.get('local') or feed.get('deskScope') == 'local' or '/local/' in report.get('url', '') or LOCAL.search(title)
    foreign = FOREIGN.search(text) or feed.get('domestic') is False
    if foreign and WORLD_IMPACT.search(text):
        return 'world-impact', 'Cross-border consequences are indicated in the reporting; establish the U.S. relevance.'
    if explicit and not (local and not NATIONAL.search(title)):
        return 'national', 'The headline or lead names a national institution, programme or consequence.'
    if local:
        return 'local', 'Local or state scope; a wider national consequence has not been established.'
    if foreign:
        return 'unestablished', 'International coverage without an established national or cross-border consequence.'
    if feed.get('deskRole') == 'primary' and feed.get('deskScope') == 'national':
        return 'national', 'A national primary-source release; its significance still needs editorial review.'
    if ECONOMIC_SCOPE.search(text):
        return 'national', 'The reporting names a nationwide economic measure, programme or major employer.'
    return 'unestablished', 'A U.S. publisher alone does not establish national significance.'


def assess(event, feeds, now):
    reports = event.get('evidence', [])
    today = now.astimezone(ZONE).date()
    change = event.get('change') or {}
    changed = moment(change.get('at'))
    change_today = bool(change.get('material') and changed and changed.astimezone(ZONE).date() == today and changed <= now)
    candidates = []
    for report in reports:
        feed = feeds.get(report.get('sourceId'), {})
        scope, reason = report_scope(report, feed)
        at = moment(report.get('publishedAt'))
        candidates.append((scope in ('national', 'world-impact'), at or datetime.min.replace(tzinfo=timezone.utc), report, feed, scope, reason))
    changed_candidates = [row for row in candidates if row[2].get('id') in change.get('evidenceIds', [])] if change_today else []
    pool = changed_candidates or candidates
    _, at, lead, feed, scope, scope_reason = max(pool, key=lambda row: row[:2]) if pool else (False, None, {}, {}, 'unestablished', 'No retained source evidence.')
    at = moment(lead.get('publishedAt'))
    text = lead.get('title', '') + ' ' + ' '.join(lead.get('excerpt', '').split()[:85])
    title = lead.get('title', '')
    beat, label, weight = beat_for(text)
    recent = bool(at and timedelta(0) <= now-at <= timedelta(hours=24))
    dated_today = bool(at and at.astimezone(ZONE).date() == today)
    primary = feed.get('deskRole') == 'primary'
    available = bool(lead.get('available')) and not lead.get('revisionMismatch')
    checked = moment(lead.get('sourceLastSuccess'))
    if not checked or (now-checked).total_seconds() > max(7200, feed.get('pollMinutes', 15)*120):
        available = False
    quote = lead.get('excerpt') or title
    peg = {'status': 'missing', 'kind': 'unestablished', 'label': 'Today peg needed',
           'reason': 'A new fetch or headline timestamp does not establish a new event.',
           'at': lead.get('publishedAt'), 'sourceId': lead.get('id'), 'quote': quote}
    questions = ['What changed today, who is affected, and what is the primary evidence?']
    lane = 'held'
    score = weight
    material = change_today and bool(changed_candidates)
    action = DEVELOPMENT.search(title)
    watch = WATCH.search(title)
    past = PAST_DAY.search(title)
    dated_past = bool(past and past.group().lower() != now.astimezone(ZONE).strftime('%A').lower())
    if lead.get('sourceTimeKind') == 'filed' and recent:
        lane = 'watch'; score += 18
        peg.update(status='candidate', kind='public-inspection', label='New public-inspection filing',
                   reason='A federal document became available for inspection. Filing, publication and legal effect are separate; inspect the actual document before characterizing the action.')
        questions = ['Is this a proposed rule, final rule or notice, and who is affected?', 'Verify the publication and effective dates in the official document.']
    elif material:
        lane = 'developing'; score += 40
        peg.update(status='candidate', kind='changed-reporting', label='Reporting changed today', at=change.get('at'),
                   reason='A retained source adds a possible consequential change. Compare the before/after evidence; observation time is not event time.')
        questions = ['Does the retained change alter the outcome, scale, status or advice?', 'Confirm the change with primary evidence and independent reporting.']
    elif recent and watch:
        lane = 'watch'; score += 10
        peg.update(status='candidate', kind='anticipated', label='Watch for the next development',
                   reason='Current reporting points to a proposed or upcoming action. Do not report the expected result as an accomplished fact.')
        questions = ['What exact event, release or decision are we waiting for?', 'Verify its time and watch the originating institution.']
    elif recent and not dated_past and not EXPLAINER.search(title) and (action or (primary and feed.get('deskScope') == 'national')):
        lane = 'today'; score += 30
        peg.update(status='candidate', kind='primary-release' if primary else 'reported-development',
                   label='Primary release today' if primary and dated_today else 'Reported today' if dated_today else 'Reported in the past 24 hours',
                   reason='The source reports a concrete development. Confirm event timing and continuing consequence before assignment; publication time alone is not proof.')
        questions = ['Confirm when the development happened and why it matters today.', 'Check the original release or decision; distinguish new facts from reaction.']
    elif recent:
        lane = 'watch'; score += 3
        peg.update(status='needs-verification', label='Current reporting; peg unconfirmed',
                   reason='The report is recent, but its headline does not establish a new national development. Find the new fact or continuing impact.')
    if not available:
        lane = 'held'; questions.insert(0, 'The source is unavailable, stale or between revisions. Recheck the reporting.')
    if change_today and not changed_candidates:
        lane = 'held'
        peg.update(status='missing', kind='missing-changed-evidence', label='Changed source evidence unavailable', sourceId=None, quote='',
                   reason='The retained change does not resolve to a current source report. Another report cannot stand in for its evidence.')
    if at is None or at > now:
        lane = 'held'; peg.update(status='missing', label='Publication time unverified', reason='No usable non-future publication timestamp. Retrieval time cannot replace it.')
    if lead.get('sourceTimeKind') == 'updated':
        lane = 'watch' if available and recent else 'held'
        peg.update(status='needs-verification', kind='source-updated', label='Source updated; event time unconfirmed',
                   reason='The feed supplies an update clock, not an original publication or new-event time. Inspect what changed before assignment.')
    excerpt = lead.get('excerpt', '')
    if action and re.search(r'\b(?:were expected to|was expected to|is expected to|are expected to|economists expect|ahead of the release)\b', excerpt, re.I) and re.search(r'\d', title) and not watch:
        lane = 'watch' if available and recent else 'held'
        peg.update(status='needs-verification', kind='evidence-check', label='Headline and excerpt need reconciliation',
                   reason='The headline reports figures or an outcome while the excerpt retains forecast language. Read the full update; the excerpt does not establish the reported result.')
        questions.insert(0, 'Separate the reported result from the earlier forecast and confirm both against the primary release.')
    alert = lead.get('alert') or {}
    expires = moment(alert.get('expires'))
    effective = moment(alert.get('effective'))
    if alert and ((expires and expires <= now) or (effective and effective > now)):
        lane = 'held'
        peg.update(status='missing', label='Alert is not currently in effect', reason='The retained alert has expired or its effective time is still ahead. Check the active official alert before assignment.')
    if scope not in ('national', 'world-impact'):
        lane = 'held'
    if NOISE.search(title) or lead.get('suppressed') or re.search(r'\b(?:movie night|\d+ things)\b', title, re.I):
        lane = 'held'; questions.insert(0, 'Find a reported decision or consequence behind the commentary, promotion or political positioning.')
    if beat == 'general':
        lane = 'held'; questions.insert(0, 'Establish the national consequence before elevating this report.')
    if primary:
        questions.append('An institution describes its own action; seek independent scrutiny where relevant.')
    if lead.get('level') != 'excerpt':
        questions.append('Only headline evidence is retained. Read the full original before assignment.')
    if recent:
        score += max(0, 12-(now-at).total_seconds()/3600)
    return {'scope': scope, 'scopeReason': scope_reason, 'beat': beat, 'beatLabel': label,
            'lane': lane, 'priority': round(score, 1), 'todayPeg': peg, 'questions': questions}


def enrich(snapshot, source_config, now=None):
    """Pure annotation: retain all leads and editorial history, separate held items."""
    now = moment(now) or datetime.now(timezone.utc)
    result = copy.deepcopy(snapshot)
    feeds = {source['id']: source for source in source_config.get('sources', []) if source.get('enabled')}
    for event in result['events']:
        event['assignment'] = assess(event, feeds, now)
    coverage = []
    for key, label, _, _ in BEATS:
        events = [event for event in result['events'] if event['assignment']['beat'] == key and event['assignment']['scope'] in ('national', 'world-impact')]
        reports = {report['id']: report for event in events for report in event.get('evidence', [])}
        current = [event for event in events if event['assignment']['lane'] in ('today', 'developing')]
        publishers = sorted({report['publisher'] for report in reports.values() if feeds.get(report.get('sourceId'), {}).get('deskRole') != 'primary'})
        primary = sorted({source['name'] for source in feeds.values() if source.get('deskRole') == 'primary' and key in source.get('deskBeats', [])})
        gap = 'No current national lead with a possible today peg.' if not current else None
        if not primary:
            gap = (gap+' ' if gap else '')+'No direct primary-source feed connected for this beat.'
        if not publishers:
            gap = (gap+' ' if gap else '')+'No independent publisher reporting in the current retained coverage.'
        coverage.append({'id': key, 'label': label, 'reportCount': len(reports), 'currentCount': len(current), 'publishers': publishers, 'primarySources': primary, 'gap': gap})
    lags = []
    for event in result['events']:
        for report in event.get('evidence', []):
            lag = report.get('publicationLagSeconds')
            if report.get('discoveryKind') == 'arrival' and isinstance(lag, (int, float)) and math.isfinite(lag) and lag >= 0:
                lags.append(lag/60)
    lags.sort()
    health = result.get('sourceHealth') or {}
    result['assignment'] = {'date': now.astimezone(ZONE).date().isoformat(), 'timezone': ZONE.key,
        'scope': 'U.S. national + consequential world',
        'counts': {lane: sum(event['assignment']['lane'] == lane for event in result['events']) for lane in ('today','developing','watch','held')},
        'coverage': coverage,
        'health': {'sourceCount': health.get('total', len(feeds)), 'healthySources': health.get('healthy', 0),
                   'lastCollectedAt': health.get('checkedAt'), 'medianDiscoveryMinutes': round(median(lags), 1) if lags else None,
                   'p90DiscoveryMinutes': round(lags[min(len(lags)-1, math.ceil(len(lags)*.9)-1)], 1) if lags else None,
                   'latencySamples': len(lags), 'limitations': ['Publisher-to-first-discovery lag is a proxy, not event-to-detection latency. Initial backlog is excluded.', 'No competitor timing benchmark has been measured.']},
        'watchpoints': [], 'sourceGaps': copy.deepcopy(source_config.get('deskGaps', [])),
        'limitations': ['Assignment cues are explainable heuristics and may miss or misclassify stories. They are not verified facts.',
                       'Today uses America/Chicago. A source timestamp or first discovery alone is not a today peg.',
                       'Available feeds are not comprehensive coverage; source outages and missing primary beats remain visible.']}
    return result
