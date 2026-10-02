"""Read-only release lookahead, separate from reports of events that occurred.

The BEA calendar is a planning source, not evidence that a release was published.
Only ``refresh`` accesses the network; ``snapshot`` is safe for desk GET requests.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc
CALENDAR_URL = 'https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics'
SOURCE_URL = 'https://www.bea.gov/news/schedule'
SOURCE_NAME = 'Bureau of Economic Analysis'
MAX_BYTES = 1_000_000
MIN_INTERVAL = timedelta(hours=1)
_LOCK = threading.RLock()


def _time(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.astimezone(UTC) if parsed.tzinfo else None
    except ValueError:
        return None


def _now(value):
    return _time(value) or datetime.now(UTC)


def _stamp(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')


def _cache_path(root):
    return Path(root) / 'production' / 'runs' / 'calendar-bea.json'


def _read(root):
    path = _cache_path(root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('url') != CALENDAR_URL or not isinstance(data.get('events'), list):
            raise ValueError('Unexpected calendar cache format')
        return data
    except (OSError, ValueError) as exc:
        return {'events': [], 'error': f'Calendar cache could not be read: {exc}', 'status': 'unavailable'}


def _write(root, value):
    path = _cache_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _unescape(value):
    return re.sub(r'\\([nN,;\\])', lambda match: '\n' if match[1].lower() == 'n' else match[1], value)


def _ical_time(value, params):
    """Never assign an invented time to all-day or timezone-free entries."""
    if params.get('VALUE', '').upper() == 'DATE' or not re.fullmatch(r'\d{8}T\d{6}Z?', value):
        return None
    try:
        if value.endswith('Z'):
            return datetime.strptime(value, '%Y%m%dT%H%M%SZ').replace(tzinfo=UTC)
        name = params.get('TZID')
        if not name:
            return None
        zone = ZoneInfo(name)
        naive = datetime.strptime(value, '%Y%m%dT%H%M%S')
        first = naive.replace(tzinfo=zone, fold=0)
        second = naive.replace(tzinfo=zone, fold=1)
        # A repeated or nonexistent local time needs explicit source resolution.
        if first.utcoffset() != second.utcoffset():
            return None
        if first.astimezone(UTC).astimezone(zone).replace(tzinfo=None) != naive:
            return None
        return first.astimezone(UTC)
    except (ValueError, ZoneInfoNotFoundError):
        return None


def parse_calendar(body):
    """Parse the small, nonrecurring calendar BEA publishes, preserving its UID."""
    if len(body) > MAX_BYTES:
        raise ValueError('Calendar exceeds the size limit')
    content = body.decode('utf-8-sig') if isinstance(body, bytes) else body
    lines = re.sub(r'\r?\n[ \t]', '', content).replace('\r\n', '\n').split('\n')
    lines = [line.rstrip('\r') for line in lines]
    if not lines or lines[0] != 'BEGIN:VCALENDAR' or 'END:VCALENDAR' not in lines:
        raise ValueError('Source did not return a complete iCalendar document')
    records = {}
    current = None
    count = 0
    for line in lines:
        if line == 'BEGIN:VEVENT':
            if current is not None:
                raise ValueError('Nested calendar event')
            current = {}
            continue
        if line == 'END:VEVENT':
            if current is None:
                raise ValueError('Unexpected calendar event ending')
            count += 1
            if count > 5000:
                raise ValueError('Calendar exceeds the event limit')
            uid = current.get('UID', ('', {}))[0].strip()
            title = ' '.join(_unescape(current.get('SUMMARY', ('', {}))[0]).split())
            when = _ical_time(*current.get('DTSTART', ('', {})))
            cancelled = current.get('STATUS', ('', {}))[0].upper() == 'CANCELLED'
            sequence = current.get('SEQUENCE', ('0', {}))[0]
            sequence = int(sequence) if re.fullmatch(r'\d{1,9}', sequence) else 0
            revision = _ical_time(*current.get('DTSTAMP', ('', {}))) or datetime.min.replace(tzinfo=UTC)
            rank = (sequence, revision, cancelled)
            if uid and len(uid) <= 500 and 'RRULE' not in current and 'RECURRENCE-ID' not in current:
                previous = records.get(uid)
                if previous is None or rank >= previous[0]:
                    records[uid] = (rank, None if cancelled or not when or not title else {
                        'id': 'bea-' + hashlib.sha256(uid.encode()).hexdigest()[:20],
                        'title': title[:400],
                        'scheduledAt': _stamp(when),
                        'sourceUrl': SOURCE_URL,
                        'sourceName': SOURCE_NAME,
                    })
            current = None
            continue
        if current is None or ':' not in line:
            continue
        key, value = line.split(':', 1)
        fields = key.split(';')
        params = {}
        for field in fields[1:]:
            if '=' in field:
                name, setting = field.split('=', 1)
                params[name.upper()] = setting.strip('"')
        current[fields[0].upper()] = (value, params)
    if current is not None:
        raise ValueError('Incomplete calendar event')
    return sorted((item[1] for item in records.values() if item[1]), key=lambda item: (item['scheduledAt'], item['id']))


class _CalendarRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != 'https' or target.hostname != 'www.bea.gov':
            raise ValueError('Calendar redirected outside the approved source')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(headers=None):
    request = urllib.request.Request(CALENDAR_URL, headers={
        'User-Agent': 'BearingAssignmentDesk/1.0 (source-linked local research)',
        'Accept': 'text/calendar',
        **(headers or {}),
    })
    opener = urllib.request.build_opener(_CalendarRedirect())
    try:
        with opener.open(request, timeout=15) as response:
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError('Calendar exceeds the size limit')
            return {'status': response.status, 'body': data,
                    'etag': response.headers.get('ETag'),
                    'modified': response.headers.get('Last-Modified'),
                    'cacheControl': response.headers.get('Cache-Control')}
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return {'status': 304, 'cacheControl': exc.headers.get('Cache-Control')}
        raise


def _delay(response):
    control = response.get('cacheControl') or ''
    match = re.search(r'(?:^|,)\s*max-age\s*=\s*"?(\d+)', control, re.I)
    return max(MIN_INTERVAL, timedelta(seconds=min(int(match[1]), 31_536_000))) if match else MIN_INTERVAL


def _retry_delay(exc, now, failures):
    delay = timedelta(hours=min(24, 2 ** min(failures - 1, 5)))
    headers = getattr(exc, 'headers', None)
    retry = headers.get('Retry-After') if headers else None
    if retry:
        try:
            duration = timedelta(seconds=int(retry)) if retry.isdigit() else parsedate_to_datetime(retry).astimezone(UTC) - now
            delay = max(delay, duration)
        except (ValueError, TypeError, OverflowError):
            pass
    return max(MIN_INTERVAL, delay)


def snapshot(root, now=None):
    now = _now(now)
    state = _read(root)
    success = _time(state.get('lastSuccess'))
    stale = bool(state.get('error')) or success is None or now - success > timedelta(hours=2)
    health = {key: state.get(key) for key in ('lastSuccess', 'lastAttemptAt', 'nextCheckAt', 'error')}
    health.update({'status': state.get('status', 'not-checked'), 'stale': stale,
                   'sourceName': SOURCE_NAME, 'sourceUrl': SOURCE_URL, 'calendarUrl': CALENDAR_URL})
    events = []
    for item in state.get('events', []):
        if not isinstance(item, dict):
            continue
        when = _time(item.get('scheduledAt'))
        if when is None or not now - timedelta(hours=6) <= when <= now + timedelta(days=7):
            continue
        if not all(isinstance(item.get(key), str) and item[key] for key in ('id', 'title')):
            continue
        events.append({key: item[key] for key in ('id', 'title', 'scheduledAt')})
        events[-1].update({'sourceUrl': SOURCE_URL, 'sourceName': SOURCE_NAME,
                           'status': 'due' if when <= now else 'scheduled',
                           'note': ('Retained calendar may be stale. ' if stale else '') +
                                   'Scheduled release; publication has not been confirmed.'})
    events.sort(key=lambda item: (item['scheduledAt'], item['id']))
    return {'events': events[:12], 'health': health}


def refresh(root, now=None):
    now = _now(now)
    with _LOCK:
        state = _read(root)
        next_check = _time(state.get('nextCheckAt'))
        if next_check and now < next_check:
            return snapshot(root, now)
        state.update({'url': CALENDAR_URL, 'lastAttemptAt': _stamp(now)})
        headers = {}
        if state.get('etag'):
            headers['If-None-Match'] = state['etag']
        if state.get('modified'):
            headers['If-Modified-Since'] = state['modified']
        try:
            response = fetch(headers)
            if response['status'] == 304:
                if not state.get('lastSuccess') or not isinstance(state.get('events'), list):
                    raise ValueError('Source returned unchanged without a retained calendar')
            elif response['status'] == 200:
                state['events'] = parse_calendar(response['body'])
                state['etag'] = response.get('etag')
                state['modified'] = response.get('modified')
            else:
                raise ValueError(f"Unexpected calendar response {response['status']}")
            state.update({'lastSuccess': _stamp(now), 'error': None, 'failures': 0,
                          'status': 'unchanged' if response['status'] == 304 else 'ok',
                          'nextCheckAt': _stamp(now + _delay(response))})
        except (OSError, ValueError, UnicodeError, KeyError) as exc:
            failures = int(state.get('failures') or 0) + 1
            state.update({'events': state.get('events', []), 'status': 'unavailable',
                          'error': str(exc)[:500], 'failures': failures,
                          'nextCheckAt': _stamp(now + _retry_delay(exc, now, failures))})
        try:
            _write(root, state)
        except OSError as exc:
            result = snapshot(root, now)
            result['health'].update({'status': 'unavailable', 'stale': True,
                                     'error': f'Calendar cache could not be saved: {exc}'})
            return result
        return snapshot(root, now)
