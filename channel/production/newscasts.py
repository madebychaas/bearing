"""Durable personal newscasts over the existing, revision-bound production path.

This store neither invents reporting nor approves a script. Its executor must
return complete selected films; a progress animation cannot make a job ready.
Only the local server owns a store and its single worker.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import math
import os
import re
import subprocess
import threading
import uuid
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

import producer

STAGES = ('sourcing', 'writing', 'editing', 'voicing', 'directing',
          'creating_visuals', 'scoring', 'assembling', 'checking')
ACTIVE = {'queued', 'working'}
RETRYABLE = {'needs_attention', 'failed', 'interrupted'}
PREFERENCES = {'voice': ('warm', 'measured'), 'pace': ('natural', 'unhurried'),
               'music': ('quiet', 'off')}
DEFAULTS = {'voice': 'warm', 'pace': 'natural', 'music': 'quiet'}
CONNECTION_MESSAGE = 'Your stories are saved. Connect the creative production workflow to make this newscast.'


class Conflict(ValueError):
    pass


class NeedsAttention(RuntimeError):
    pass


class Cancelled(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def source_revision(evidence):
    # Fetch clocks and recommendations are not reporting revisions. Dates,
    # exact excerpts, attribution and negation remain part of the binding.
    return digest([{key: item.get(key) for key in
                    ('id', 'publisher', 'url', 'publishedAt', 'title', 'excerpt', 'sourceId')}
                   for item in sorted(evidence, key=lambda item: item['id'])])


class NewscastStore:
    def __init__(self, desk, *, handoff=None, executor=None, capabilities=None,
                 autostart=True, retry_seconds=2):
        self.desk = desk
        self.root = Path(desk.root)
        self.folder = self.root / 'production' / 'runs' / 'newscasts'
        self.handoff = handoff
        self.executor = executor
        self.capability_provider = capabilities
        self.autostart = autostart
        self.retry_seconds = retry_seconds
        self.lock = threading.RLock()
        self.wake = threading.Event()
        self.stopping = threading.Event()
        self.worker = None
        self.folder.mkdir(parents=True, exist_ok=True)
        self._recover()

    def _now(self):
        return producer._time(self.desk.clock()) or datetime.now(timezone.utc)

    def _stamp(self):
        return producer._stamp(self._now())

    def _path(self, identifier):
        if not isinstance(identifier, str) or not re.fullmatch(r'newscast-[a-f0-9]{32}', identifier):
            raise ValueError('Choose an existing newscast.')
        return self.folder / (identifier + '.json')

    def _read(self, identifier):
        path = self._path(identifier)
        if not path.exists():
            raise KeyError(identifier)
        try:
            job = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(job, dict) or job.get('id') != identifier:
                raise ValueError('Invalid job record')
            return job
        except (ValueError, UnicodeError) as exc:
            raise RuntimeError('This newscast could not be read; its retained record was preserved.') from exc

    def _save(self, job):
        job['updatedAt'] = self._stamp()
        path = self._path(job['id'])
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, path)
        return job

    def _jobs(self):
        return [self._read(path.stem) for path in sorted(self.folder.glob('newscast-*.json'))]

    def _recover(self):
        with self.lock:
            for job in self._jobs():
                if job.get('status') in ACTIVE:
                    job.update(status='interrupted', message='Production stopped when Bearing restarted. Your story choices and completed work are saved.',
                               error='Production was interrupted; retry when ready.')
                    self._save(job)

    @staticmethod
    def _public(job):
        value = copy.deepcopy(job)
        for key in ('requestId', 'requestHash', 'schema'):
            value.pop(key, None)
        for story in value.get('stories', []):
            story.pop('evidence', None)
        return value

    def capabilities(self):
        if self.capability_provider:
            result = self.capability_provider(self.root)
        elif self.executor:
            result = {'generationReady': True, 'summary': 'Production is connected.'}
        else:
            try:
                module = importlib.import_module('newscast_production')
            except ModuleNotFoundError as exc:
                if exc.name != 'newscast_production':
                    raise
                return {'generationReady': False, 'summary': CONNECTION_MESSAGE}
            provider = getattr(module, 'capabilities', None)
            result = provider(self.root) if provider else {'generationReady': False, 'summary': CONNECTION_MESSAGE}
        if not isinstance(result, dict) or type(result.get('generationReady')) is not bool or not isinstance(result.get('summary'), str):
            raise RuntimeError('Production capability information is unavailable.')
        return copy.deepcopy(result)

    def _catalog(self):
        # ProducerStore reads reporting, candidates and health once, under its
        # own lock, and flags publication/candidate revision mismatches.
        snapshot = self.desk.snapshot('live')
        now = self._now()
        configuration = json.loads((self.root / 'production' / 'sources.json').read_text(encoding='utf-8'))
        trusted = {item['id']: item for item in configuration.get('sources', [])
                   if item.get('enabled') is True and item.get('domestic') is True}
        stories = []
        for event in snapshot.get('events', []):
            evidence = []
            for report in event.get('evidence', []):
                feed = trusted.get(report.get('sourceId'))
                when = producer._time(report.get('publishedAt'))
                if not feed or not when or not now - timedelta(hours=24) <= when <= now:
                    continue
                if not report.get('available') or report.get('revisionMismatch') or report.get('suppressed') or report.get('foreignLocal'):
                    continue
                try:
                    url = urlsplit(report.get('url', ''))
                    if url.scheme != 'https' or url.hostname not in feed.get('hosts', []) or url.username or url.password or url.port not in (None, 443):
                        continue
                except ValueError:
                    continue
                if not report.get('title') or not report.get('id'):
                    continue
                evidence.append(copy.deepcopy(report))
            if not evidence:
                continue
            evidence.sort(key=lambda item: (producer._time(item['publishedAt']), item['id']), reverse=True)
            lead = evidence[0]
            publishers = {item['publisher'] for item in evidence}
            stories.append({'id': event['id'], 'revision': source_revision(evidence), 'title': lead['title'],
                            'publisher': lead['publisher'], 'publishedAt': lead['publishedAt'],
                            'sourceUrl': lead['url'], 'topic': lead.get('topic', event.get('topic', 'general')),
                            'topicLabel': {'business': 'Business & economy', 'world': 'Policy & society',
                                           'technology': 'Technology', 'space': 'Space & discovery',
                                           'nature': 'Nature', 'local': 'Local', 'health': 'Health',
                                           'culture': 'Culture', 'sport': 'Sport'}.get(lead.get('topic'), 'News'),
                            'sourceCount': len(publishers), 'evidence': evidence})
        stories.sort(key=lambda story: (producer._time(story['publishedAt']), story['id']), reverse=True)
        # An event is one selectable item even if several feeds carry it.
        unique = {}
        for story in stories:
            unique.setdefault(story['id'], story)
        return list(unique.values())

    def catalog(self):
        stories = [{key: value for key, value in story.items() if key != 'evidence'}
                   for story in self._catalog()[:48]]
        return {'stories': stories, 'generatedAt': self._stamp(), 'capabilities': self.capabilities()}

    @staticmethod
    def _request(payload):
        if not isinstance(payload, dict):
            raise ValueError('Send a newscast request.')
        choices = payload.get('stories')
        if not isinstance(choices, list) or not 2 <= len(choices) <= 3:
            raise ValueError('Choose two or three stories for your newscast.')
        for choice in choices:
            if not isinstance(choice, dict) or not isinstance(choice.get('id'), str) or not 1 <= len(choice['id']) <= 160 or not re.fullmatch(r'[a-f0-9]{64}', str(choice.get('revision', ''))):
                raise ValueError('Choose stories with their current reporting revisions.')
        if len({item['id'] for item in choices}) != len(choices):
            raise ValueError('Choose different stories for your newscast.')
        preferences = payload.get('preferences', {})
        if not isinstance(preferences, dict) or set(preferences) - set(PREFERENCES):
            raise ValueError('Choose valid newscast preferences.')
        preferences = {**DEFAULTS, **preferences}
        if any(value not in PREFERENCES[key] for key, value in preferences.items()):
            raise ValueError('Choose valid newscast preferences.')
        try:
            request_id = str(uuid.UUID(payload.get('requestId', '')))
        except (ValueError, AttributeError, TypeError):
            raise ValueError('A UUID request ID is required.') from None
        choices = [{key: choice[key] for key in ('id', 'revision')} for choice in choices]
        return choices, preferences, request_id

    def create(self, payload):
        choices, preferences, request_id = self._request(payload)
        request_hash = digest([choices, preferences])
        # Check idempotency before freshness so retrying a confirmed request
        # returns that same record even after its source subsequently changes.
        with self.lock:
            for job in self._jobs():
                if job.get('requestId') == request_id:
                    if job.get('requestHash') != request_hash:
                        raise Conflict('This request ID already belongs to different story choices.')
                    return {'job': self._public(job)}
        catalog = {item['id']: item for item in self._catalog()}
        selected = []
        for choice in choices:
            current = catalog.get(choice['id'])
            if not current or current['revision'] != choice['revision']:
                raise Conflict('Selected reporting changed or is no longer current. Refresh the stories before creating your newscast.')
            selected.append({**copy.deepcopy(current), 'status': 'queued'})
        with self.lock:
            for existing in self._jobs():
                if existing.get('requestId') == request_id:
                    if existing.get('requestHash') != request_hash:
                        raise Conflict('This request ID already belongs to different story choices.')
                    return {'job': self._public(existing)}
            job = {'schema': 1, 'id': 'newscast-' + uuid.uuid4().hex, 'requestId': request_id,
                   'requestHash': request_hash, 'status': 'queued', 'stage': 'sourcing',
                   'message': 'Your stories are queued for production.', 'stories': selected,
                   'completed': 0, 'total': len(selected), 'preferences': preferences,
                   'createdAt': self._stamp(), 'updatedAt': self._stamp()}
            self._save(job)
            response = {'job': self._public(job)}
            self._start_worker()
            return response

    def get(self, identifier):
        with self.lock:
            return {'job': self._public(self._read(identifier))}

    def cancel(self, identifier):
        with self.lock:
            job = self._read(identifier)
            if job['status'] == 'ready':
                raise Conflict('This newscast is already ready. Its finished media has been preserved.')
            if job['status'] != 'cancelled':
                job.update(status='cancelled', message='Newscast cancelled. Your choices and completed work are saved.')
                job.pop('error', None)
                for story in job['stories']:
                    if story.get('status') != 'complete':
                        story['status'] = 'cancelled'
                self._save(job)
            self.wake.set()
            return {'job': self._public(job)}

    def retry(self, identifier):
        with self.lock:
            job = self._read(identifier)
            if job['status'] not in RETRYABLE:
                raise Conflict('Only a paused, failed or interrupted newscast can be retried.')
        self.guard(identifier, allow_retry=True)
        with self.lock:
            job = self._read(identifier)
            if job['status'] not in RETRYABLE:
                raise Conflict('This newscast changed while retrying. Refresh its status.')
            job.setdefault('attempts', []).append({'status': job['status'], 'completed': job['completed'],
                                                   'updatedAt': job['updatedAt']})
            job.update(status='queued', stage='sourcing', completed=0,
                       message='Your saved stories are queued for production. Completed media will be checked and reused.')
            for story in job['stories']:
                story['status'] = 'queued'
                story.pop('stage', None)
            job.pop('error', None)
            self._save(job)
            response = {'job': self._public(job)}
            self._start_worker()
            return response

    def guard(self, identifier, *, allow_retry=False):
        with self.lock:
            job = self._read(identifier)
            if job['status'] == 'cancelled' or self.stopping.is_set():
                raise Cancelled('Newscast production was cancelled or stopped.')
            if job['status'] not in ACTIVE and not (allow_retry and job['status'] in RETRYABLE):
                raise NeedsAttention('This newscast is no longer awaiting production.')
        catalog = {story['id']: story for story in self._catalog()}
        for selected in job['stories']:
            current = catalog.get(selected['id'])
            if not current or current['revision'] != selected['revision']:
                raise NeedsAttention('Reporting for one of your stories changed or is no longer current. Choose the latest version before producing it.')
        with self.lock:
            if self._read(identifier)['status'] == 'cancelled':
                raise Cancelled('Newscast production was cancelled.')
        return copy.deepcopy(job)

    def _report(self, identifier, stage, message, completed=None, storyId=None):
        if stage not in STAGES or not isinstance(message, str) or not 1 <= len(message) <= 500:
            raise ValueError('A real production stage and short status message are required.')
        self.guard(identifier)
        with self.lock:
            job = self._read(identifier)
            if job['status'] == 'cancelled':
                raise Cancelled('Newscast production was cancelled.')
            if completed is not None:
                if type(completed) is not int or not job['completed'] <= completed <= job['total']:
                    raise ValueError('Completed story count must match actual production progress.')
                job['completed'] = completed
                for story in job['stories'][:completed]:
                    story['status'] = 'complete'
            if storyId:
                selected = next((story for story in job['stories'] if story['id'] == storyId), None)
                if selected is None:
                    raise ValueError('Progress refers to an unselected story.')
                if selected['status'] != 'complete':
                    selected.update(status='working', stage=stage)
            job.update(status='working', stage=stage, message=message)
            self._save(job)

    def _start_worker(self):
        self.wake.set()
        if self.autostart and (not self.worker or not self.worker.is_alive()):
            self.worker = threading.Thread(target=self.run_pending, name='bearing-newscasts', daemon=True)
            self.worker.start()

    def _executor(self):
        if self.executor:
            return self.executor
        try:
            module = importlib.import_module('newscast_production')
        except ModuleNotFoundError as exc:
            if exc.name != 'newscast_production':
                raise
            raise NeedsAttention(CONNECTION_MESSAGE) from None
        execute = getattr(module, 'run_job', None)
        if not callable(execute):
            raise NeedsAttention(CONNECTION_MESSAGE)
        return execute

    def _production_lock(self):
        import pipeline
        return pipeline.production_lock()

    def run_pending(self):
        while not self.stopping.is_set():
            with self.lock:
                queued = sorted((job for job in self._jobs() if job['status'] == 'queued'), key=lambda job: job['createdAt'])
                if not queued:
                    # Clear ownership while holding the same lock as create;
                    # a newly queued request cannot miss the exiting worker.
                    if self.worker is threading.current_thread():
                        self.worker = None
                    return
                identifier = queued[0]['id']
            try:
                execute = self._executor()
                self.guard(identifier)
                acquired = False
                try:
                    with self._production_lock():
                        acquired = True
                        job = self.guard(identifier)
                        self._report(identifier, 'sourcing', 'Checking the current reporting behind your stories.')
                        result = execute(job, lambda *args, **kwargs: self._report(identifier, *args, **kwargs),
                                         lambda: self.guard(identifier), self.root, handoff=self.handoff)
                        self._report(identifier, 'checking', 'Checking picture, sound and the complete playlist.')
                        self._validate_result(job, result)
                        self.guard(identifier)
                        # Decoding can take time. Recheck the exact production
                        # authority afterward and hold its lock through ready.
                        with self.handoff.lock if self.handoff is not None else nullcontext():
                            validator = (getattr(self.executor, 'validate_ready', None) if self.executor else
                                         getattr(importlib.import_module('newscast_production'), 'validate_ready', None))
                            if validator:
                                validator(job, result, lambda: self.guard(identifier), self.root, handoff=self.handoff)
                            self._validate_authority(job, result)
                            with self.lock:
                                current = self._read(identifier)
                                if current['status'] == 'cancelled' or self.stopping.is_set():
                                    raise Cancelled('Newscast production was cancelled.')
                                current.update(status='ready', stage='checking', message='Your newscast is ready.',
                                               result=result, completed=current['total'])
                                current.pop('error', None)
                                for story in current['stories']:
                                    story['status'] = 'complete'
                                self._save(current)
                except RuntimeError as exc:
                    if not acquired and 'Another Bearing production run is active' in str(exc):
                        with self.lock:
                            waiting = self._read(identifier)
                            if waiting['status'] == 'queued':
                                waiting['message'] = 'Your newscast is queued while the current production finishes.'
                                self._save(waiting)
                        self.wake.wait(self.retry_seconds)
                        self.wake.clear()
                        continue
                    raise
            except Cancelled:
                # Cancellation is already persisted; shutdown is recovered as
                # interrupted on the next launch, retaining all staged assets.
                continue
            except Exception as exc:
                with self.lock:
                    job = self._read(identifier)
                    if job['status'] == 'cancelled':
                        continue
                    held = isinstance(exc, (NeedsAttention, Conflict)) or getattr(exc, 'needs_attention', False) is True
                    message = str(exc)[:500] if held else 'This newscast could not finish. Your choices and completed work are saved; you can retry.'
                    job.update(status='needs_attention' if held else 'failed', message=message,
                               error=message)
                    self._save(job)

    def _asset(self, value, expected_hash):
        if not isinstance(value, str) or not re.fullmatch(r'assets/[a-zA-Z0-9_./-]+', value) or '..' in value or not re.fullmatch(r'[a-f0-9]{64}', str(expected_hash)):
            raise ValueError('Finished media needs a local asset and its verified hash.')
        assets = (self.root / 'dist' / 'assets').resolve()
        path = (self.root / 'dist' / value).resolve()
        if not path.is_relative_to(assets) or not path.is_file() or file_hash(path) != expected_hash:
            raise ValueError('Finished media is missing or differs from its recorded hash.')
        return path

    def _decode_asset(self, path):
        settings = json.loads((self.root / 'production' / 'runtime.json').read_text(encoding='utf-8'))
        subprocess.run([settings['ffmpeg'], '-hide_banner', '-nostdin', '-v', 'error', '-xerror',
                        '-i', str(path), '-f', 'null', '-'], check=True, capture_output=True, timeout=180)

    def _validate_authority(self, job, result):
        for selected, story in zip(job['stories'], result['stories']):
            expires = producer._time(story.get('expiresAt'))
            if not expires or expires <= self._now():
                raise NeedsAttention('A selected story expired during the final checks. Its reporting needs a fresh review.')
            if self.handoff is None:
                if self.executor is None:
                    raise NeedsAttention('Production review is unavailable. Your finished media has been preserved.')
                continue
            lineage = story['production']['selection']
            try:
                record = self.handoff._guard(selected['id'], lineage.get('mode', 'live'), lineage['approval']['id'])
                if record.get('approval') != lineage['approval'] or record.get('scriptHash') != hashlib.sha256(story['script'].encode()).hexdigest():
                    raise ValueError('The finished script no longer matches its current production approval.')
            except (ValueError, KeyError, RuntimeError) as exc:
                raise NeedsAttention('Production review changed during the final checks. The finished media is saved and needs review before playback.') from exc

    def _validate_result(self, job, result):
        if not isinstance(result, dict) or not isinstance(result.get('stories'), list) or len(result['stories']) != job['total']:
            raise ValueError('Every selected story needs a complete finished film.')
        teaser = result.get('teaser')
        if not isinstance(teaser, str) or not 12 <= len(teaser.strip()) <= 360 or '\n' in teaser:
            raise ValueError('The completed newscast needs one concise, source-grounded introduction.')
        seconds = 0
        story_ids, source_urls = set(), set()
        for selected, story in zip(job['stories'], result['stories']):
            if not isinstance(story, dict):
                raise ValueError('Finished stories must be complete records.')
            identifier = story.get('id')
            source_url = story.get('source', {}).get('url', '')
            try:
                url = urlsplit(source_url)
                valid_url = url.scheme == 'https' and bool(url.hostname) and not url.username and not url.password and url.port in (None, 443)
            except ValueError:
                valid_url = False
            if not isinstance(identifier, str) or not identifier or identifier in story_ids or source_url in source_urls or not valid_url or not isinstance(story.get('title'), str) or not story['title'].strip():
                raise ValueError('Finished newscasts require distinct playable stories and supporting source URLs.')
            story_ids.add(identifier)
            source_urls.add(source_url)
            production = story.get('production', {})
            lineage = production.get('newscast', {})
            source = production.get('selection', {})
            if lineage != {'jobId': job['id'], 'eventId': selected['id'], 'sourceRevision': selected['revision']} or source.get('eventId') != selected['id'] or not source.get('approval'):
                raise ValueError('Finished films must belong to these selected reporting revisions and editorial approvals.')
            if story.get('status') != 'ready' or story.get('format') != 'studio-programme' or production.get('pipeline') != 'finished-film-v1' or story.get('programme', {}).get('visualTreatment') != 'finished-film':
                raise ValueError('Only complete produced films can enter this newscast.')
            script = story.get('script')
            if not isinstance(script, str) or not script.strip():
                raise ValueError('A finished film needs its exact narration script.')
            script_hash = hashlib.sha256(script.encode()).hexdigest()
            expires = producer._time(story.get('expiresAt'))
            if not expires or expires <= self._now():
                raise ValueError('A finished story has expired before delivery.')
            for voice in ('warm', 'measured'):
                track = story.get('voices', {}).get(voice, {})
                duration = track.get('duration')
                if type(duration) not in (int, float) or not math.isfinite(duration) or not 1 < duration <= 45.12 or track.get('fullDecodePassed') is not True or track.get('scriptSha256') != script_hash:
                    raise ValueError('Both voice tracks need checked duration, exact script and decode provenance.')
                captions = track.get('captions', [])
                if not captions or ' '.join(item.get('text', '') for item in captions).split() != script.split():
                    raise ValueError('Finished captions must reproduce the spoken script exactly.')
                for key, hash_key in (('video', 'videoSha256'), ('audio', 'sha256')):
                    self._decode_asset(self._asset(track.get(key), track.get(hash_key)))
            visual = story.get('visual', {})
            if visual.get('scope') != 'story' or visual.get('storyId') != identifier or story.get('video') not in {track['video'] for track in story['voices'].values()}:
                raise ValueError('Finished story visuals must belong to the selected film.')
            self._asset(story.get('image'), visual.get('imageSha256'))
            self._asset(story.get('video'), visual.get('videoSha256'))
            seconds += story['voices'][job['preferences']['voice']]['duration']
        # One native 1.5-second handoff separates adjacent finished stories.
        pace = .92 if job['preferences']['pace'] == 'unhurried' else 1
        expected = seconds / pace + 1.5 * (job['total'] - 1)
        duration = result.get('duration')
        if type(duration) not in (int, float) or not math.isfinite(duration) or abs(duration - expected) > .15:
            raise ValueError('Newscast duration must include its actual selected voice tracks and handoffs.')

    def close(self):
        self.stopping.set()
        self.wake.set()
