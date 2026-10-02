"""Durable 15-minute desk editions and source-bound background tile preparation.

This store never calls a model or generates images inside a reporting request.
The local editorial worker claims a job, prepares and inspects its art outside
the server, then submits an exact-evidence result. Only complete tiles publish.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from assignment import moment
import top_stories

INTERVAL = timedelta(minutes=15)
LEASE = timedelta(minutes=12)


def stamp(at):
    return at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def identity(item):
    return hashlib.sha256((item['eventId'] + ':' + item['evidenceHash']).encode()).hexdigest()[:24]


def hero_items(edition):
    return [item for item in edition.get('items', []) if item['rank'] <= 3]


class Conflict(ValueError):
    pass


class EditionStore:
    """All calls are serialized by the owning ProducerStore's RLock."""

    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / 'production/runs/top-stories-editions.json'
        self.asset_cache = {}
        self.seed_art = {}
        for manifest in (self.root / 'production').glob('top-stories-art-*.json'):
            try:
                record = json.loads(manifest.read_text(encoding='utf-8'))
                if record.get('generator') != 'built-in image_gen' or not record.get('review'):
                    continue
                for item in record.get('items', []):
                    if item.get('kind') == 'illustration' and re.fullmatch(r'[0-9a-f]{64}', str(item.get('sha256', ''))):
                        self.seed_art[item.get('url')] = item['sha256']
            except (OSError, ValueError, AttributeError, TypeError):
                continue

    def _read(self):
        if not self.path.exists():
            return {'schema': 1, 'edition': None, 'staged': None, 'nextRefreshAt': None, 'jobs': {}, 'tiles': {}}
        try:
            state = json.loads(self.path.read_text(encoding='utf-8'))
            if state.get('schema') != 1 or not all(isinstance(state.get(k), dict) for k in ('jobs', 'tiles')):
                raise ValueError('Invalid edition state')
            return state
        except (OSError, ValueError, AttributeError) as exc:
            raise RuntimeError('Saved Top stories state needs attention; it was not replaced.') from exc

    def _save(self, state):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix('.json.tmp')
        temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, self.path)

    def _art(self, art, expected_hash=None):
        url = art.get('url', '') if isinstance(art, dict) else ''
        if not re.fullmatch(r'/assets/top-stories/[a-zA-Z0-9_-]+\.(?:png|jpg|jpeg|webp)', url):
            return None
        path = (self.root / 'dist' / url.lstrip('/')).resolve()
        directory = (self.root / 'dist/assets/top-stories').resolve()
        if path.parent != directory or not path.is_file():
            return None
        try:
            stat = path.stat()
            if not 1024 <= stat.st_size <= 20 * 1024 * 1024:
                return None
            key = (str(path), stat.st_mtime_ns, stat.st_size)
            proof = self.asset_cache.get(key)
            if not proof:
                from PIL import Image
                with Image.open(path) as picture:
                    width, height = picture.size
                    picture.verify()
                if width < 960 or height < 540 or not 1.4 <= width / height <= 2.1:
                    return None
                proof = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'width': width, 'height': height}
                self.asset_cache = {k: v for k, v in self.asset_cache.items() if k[0] != str(path)}
                self.asset_cache[key] = proof
            if expected_hash and proof['sha256'] != expected_hash:
                return None
            return proof
        except (OSError, ValueError, SyntaxError):
            return None

    def _ready(self, item, state):
        record = state['tiles'].get(identity(item), {})
        expected = record.get('artReview', {}).get('sha256') or self.seed_art.get(item.get('art', {}).get('url'))
        return (item.get('copyKind') == 'editorial' and bool(item.get('supportingEvidence')) and
                bool(item.get('summary')) and bool(expected) and bool(self._art(item.get('art'), expected)))

    def _rank(self, snapshot, authored, state, now):
        # Runtime completions never alter the checked-in editorial/source record.
        records = list(state['tiles'].values()) + list((authored or {}).get('items', []))
        return top_stories.rank(snapshot, {'items': records}, now)

    def _queue(self, state, target, now):
        wanted = {identity(i) for i in hero_items(target)}
        for key, job in state['jobs'].items():
            if key not in wanted and job['state'] in ('queued', 'working', 'needs_attention'):
                job.update(state='superseded', finishedAt=stamp(now))
                job.pop('leaseToken', None)
        for item in hero_items(target):
            key = identity(item)
            if self._ready(item, state):
                if key in state['jobs'] and state['jobs'][key]['state'] in ('queued', 'working', 'needs_attention'):
                    state['jobs'][key].update(state='ready', finishedAt=stamp(now))
                    state['jobs'][key].pop('leaseToken', None)
                continue
            old = state['jobs'].get(key)
            if old and old['state'] == 'working' and (moment(old.get('leaseUntil')) or now) > now:
                continue
            if old and old['state'] == 'needs_attention' and (moment(old.get('retryAt')) or now) > now:
                continue
            if not old or old['state'] != 'queued':
                state['jobs'][key] = {'id': key, 'eventId': item['eventId'], 'evidenceHash': item['evidenceHash'],
                    'sourceId': item['sourceId'], 'state': 'queued', 'createdAt': old.get('createdAt', stamp(now)) if old else stamp(now),
                    'attempts': old.get('attempts', 0) if old else 0, 'headline': item['headline']}
        # Bounded operational history, with active work always retained.
        finished = sorted((k for k, j in state['jobs'].items() if j['state'] in ('ready', 'superseded')),
                          key=lambda k: state['jobs'][k].get('finishedAt', ''), reverse=True)
        for key in finished[40:]:
            state['jobs'].pop(key, None)

    def snapshot(self, snapshot, authored, now=None):
        now = moment(now) or datetime.now(timezone.utc)
        state = self._read()
        current = self._rank(snapshot, authored, state, now)
        lookup = {identity(i): i for i in current['items']}
        due = not moment(state.get('nextRefreshAt')) or now >= moment(state['nextRefreshAt'])
        if due:
            state['staged'] = {'items': current['items'], 'asOf': current['asOf'], 'evaluatedAt': stamp(now)}
            state['nextRefreshAt'] = stamp(now + INTERVAL)
            state['lastEvaluatedAt'] = stamp(now)
        staged = state.get('staged')
        if staged:
            # Revalidate, but do not invent a new editorial order on a UI poll.
            staged['items'] = [{**lookup[identity(i)], 'rank': i['rank']} for i in staged['items'] if identity(i) in lookup]
            self._queue(state, staged, now)
            if hero_items(staged) and all(self._ready(i, state) for i in hero_items(staged)):
                state['edition'] = {**copy.deepcopy(staged), 'preparedAt': stamp(now)}
                state['staged'] = None
            elif state.get('edition') is None:
                # Initial list is useful immediately; reserved hero positions are
                # withheld until the first three illustrated cards are ready.
                state['edition'] = {**copy.deepcopy(staged), 'preparedAt': None}
        edition = state.get('edition') or {'items': [], 'asOf': current['asOf'], 'preparedAt': None}
        valid = [{**lookup[identity(i)], 'rank': i['rank']} for i in edition['items'] if identity(i) in lookup]
        # Removed/changed evidence disappears immediately, not on the next timer.
        # Preserve the edition's ranking gaps until the next scheduled assessment.
        hero_positions = [i for i in valid if i['rank'] <= 3]
        ready = [i for i in hero_positions if self._ready(i, state)] if edition.get('preparedAt') else []
        if state.get('staged'):
            self._queue(state, state['staged'], now)
        pending = [j for j in state['jobs'].values() if j['state'] in ('queued', 'working', 'needs_attention')]
        self._save(state)
        base = {k: current[k] for k in ('status', 'selectionMethod', 'disclosure')}
        overdue = any(now - (moment(j.get('startedAt') or j.get('createdAt')) or now) > timedelta(minutes=30) for j in pending)
        result = {**base, 'items': ready, 'asOf': edition.get('asOf'), 'preparedAt': edition.get('preparedAt'),
                  'lastEvaluatedAt': state.get('lastEvaluatedAt'), 'nextRefreshAt': state['nextRefreshAt'],
                  'refreshMinutes': 15, 'preparingCount': len(pending),
                  'preparationState': 'needs_attention' if overdue or any(j['state'] == 'needs_attention' for j in pending) else 'preparing' if pending else 'idle',
                  'reservedEventIds': [i['eventId'] for i in hero_positions]}
        if not ready:
            result['status'] = 'stale' if current['status'] == 'stale' else 'empty'
        return result, {**base, 'items': valid, 'asOf': edition.get('asOf'), 'evaluatedAt': edition.get('evaluatedAt')}

    def jobs(self, snapshot, now=None):
        now = moment(now) or datetime.now(timezone.utc)
        state = self._read()
        events = {e['id']: e for e in snapshot['events']}
        output = []
        for job in state['jobs'].values():
            if job['state'] not in ('queued', 'working', 'needs_attention'):
                continue
            safe = {k: v for k, v in job.items() if k != 'leaseToken'}
            safe['evidence'] = events.get(job['eventId'], {}).get('evidence', [])
            prior = [t for t in state['tiles'].values() if t['eventId'] == job['eventId']]
            if prior:
                safe['previousTile'] = max(prior, key=lambda t: t.get('reviewedAt', ''))
            output.append(safe)
        return {'jobs': output, 'nextRefreshAt': state.get('nextRefreshAt'), 'lastEvaluatedAt': state.get('lastEvaluatedAt'),
                'instruction': 'Claim before work. Verify primary evidence, prepare and inspect an original illustration, then complete against the claimed evidence hash. Never produce or approve a video.'}

    def claim(self, job_id, now=None):
        now = moment(now) or datetime.now(timezone.utc)
        state = self._read()
        job = state['jobs'].get(job_id)
        if not job or job['state'] not in ('queued', 'needs_attention'):
            raise Conflict('This tile is not available to claim.')
        if job['state'] == 'needs_attention' and (moment(job.get('retryAt')) or now) > now:
            raise Conflict('This tile is waiting for its next retry.')
        job.update(state='working', leaseToken=secrets.token_hex(16), leaseUntil=stamp(now + LEASE),
                   startedAt=stamp(now), attempts=job.get('attempts', 0) + 1)
        self._save(state)
        return copy.deepcopy(job)

    def finish(self, payload, snapshot, authored, now=None):
        now = moment(now) or datetime.now(timezone.utc)
        state = self._read()
        job = state['jobs'].get(payload.get('jobId'))
        if not job or job['state'] != 'working' or not secrets.compare_digest(str(job.get('leaseToken', '')), str(payload.get('leaseToken', ''))):
            raise Conflict('This preparation lease is not current.')
        if (moment(job.get('leaseUntil')) or now) <= now:
            raise Conflict('The preparation lease expired; claim the current work again.')
        if payload.get('action') == 'hold':
            reason = payload.get('reason')
            if not isinstance(reason, str) or not 8 <= len(reason) <= 600:
                raise ValueError('Provide a brief explanation for the held tile.')
            job.update(state='needs_attention', detail=reason, retryAt=stamp(now + INTERVAL))
            job.pop('leaseToken', None)
            self._save(state)
            return {'state': 'needs_attention', 'jobId': job['id']}
        item = payload.get('item')
        if not isinstance(item, dict) or any(item.get(k) != job[k] for k in ('eventId', 'sourceId', 'evidenceHash')):
            raise Conflict('Prepared tile does not match the claimed source evidence.')
        staged = state.get('staged') or {}
        if job['id'] not in {identity(i) for i in hero_items(staged)}:
            raise Conflict('This story is no longer awaiting a top-three tile.')
        check = top_stories.rank(snapshot, {'items': [item]}, now)
        verified = next((i for i in check['items'] if identity(i) == job['id']), None)
        if not verified or not verified.get('summary') or not verified.get('supportingEvidence') or verified.get('copyKind') != 'editorial':
            raise Conflict('Current reporting or the primary-evidence review no longer supports this tile.')
        review = item.get('artReview') or {}
        if (not isinstance(review, dict) or review.get('verdict') != 'accepted' or
                not isinstance(review.get('prompt'), str) or len(review['prompt']) < 50 or
                review.get('generator') != 'built-in image_gen' or
                not re.fullmatch(r'[0-9a-f]{64}', str(review.get('sha256', ''))) or
                not self._art(item.get('art'), review.get('sha256'))):
            raise ValueError('An inspected original image, generation prompt and matching file hash are required.')
        reviewed = moment(review.get('reviewedAt'))
        if not reviewed or not timedelta(0) <= now - reviewed <= timedelta(minutes=30):
            raise ValueError('The image inspection must be current.')
        state['tiles'][job['id']] = copy.deepcopy(item)
        job.update(state='ready', finishedAt=stamp(now))
        job.pop('leaseToken', None)
        self._save(state)
        return {'state': 'ready', 'jobId': job['id']}
