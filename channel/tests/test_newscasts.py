"""Personal production jobs must stay source-bound and cannot fake readiness."""
import copy
import hashlib
import http.client
import json
import sys
import tempfile
import threading
import unittest
import uuid
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'production'))
import newscasts
import server


class Desk:
    def __init__(self, root):
        self.root = root
        self.now = datetime(2026, 10, 1, 20, tzinfo=timezone.utc)
        self.clock = lambda: self.now
        self.lock = threading.RLock()
        self.events = []

    def snapshot(self, mode='live'):
        with self.lock:
            return {'events': copy.deepcopy(self.events), 'generatedAt': self.now.isoformat()}


class NewscastTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'production').mkdir()
        (self.root / 'dist' / 'assets').mkdir(parents=True)
        feeds = [{'id': 'us', 'enabled': True, 'domestic': True, 'hosts': ['news.example']},
                 {'id': 'foreign', 'enabled': True, 'domestic': False, 'hosts': ['foreign.example']},
                 {'id': 'off', 'enabled': False, 'domestic': True, 'hosts': ['news.example']}]
        (self.root / 'production' / 'sources.json').write_text(json.dumps({'sources': feeds}), encoding='utf-8')
        self.desk = Desk(self.root)
        self.desk.events = [self.event('one'), self.event('two', age=30), self.event('three', age=60)]
        self.store = self.make_store()

    def make_store(self, **kwargs):
        store = newscasts.NewscastStore(self.desk, autostart=False, retry_seconds=.001, **kwargs)
        store._production_lock = lambda: nullcontext()
        self.addCleanup(store.close)
        return store

    def event(self, name, age=0, **changes):
        report = {'id': 'report-' + name, 'sourceId': 'us', 'publisher': 'Trusted News',
                  'title': 'A consequential development ' + name, 'excerpt': 'Supported current reporting with practical implications.',
                  'url': 'https://news.example/' + name,
                  'publishedAt': (self.desk.now - timedelta(minutes=age)).isoformat(),
                  'topic': 'business', 'available': True, 'domestic': True,
                  'revisionMismatch': False, 'suppressed': False, 'foreignLocal': False}
        report.update(changes)
        return {'id': 'event-' + name, 'topic': 'business', 'evidence': [report]}

    def payload(self, count=2, **prefs):
        items = self.store.catalog()['stories'][:count]
        return {'stories': [{key: item[key] for key in ('id', 'revision')} for item in items],
                'preferences': prefs, 'requestId': str(uuid.uuid4())}

    def create(self, **prefs):
        return self.store.create(self.payload(**prefs))['job']

    def result(self, job):
        stories = []
        for index, selected in enumerate(job['stories']):
            identifier = 'finished-' + selected['id']
            script = 'A new report explains the practical impact for households. The source describes what has changed and who is affected. The next step is to check the details that apply to you.'
            script_hash = hashlib.sha256(script.encode()).hexdigest()
            tracks = {}
            for voice in ('warm', 'measured'):
                paths = {}
                for kind in ('mp3', 'mp4'):
                    path = self.root / 'dist' / 'assets' / f'{identifier}-{voice}.{kind}'
                    path.write_bytes(f'Checked media fixture {identifier} {voice} {kind}'.encode())
                    paths[kind] = (path.relative_to(self.root / 'dist').as_posix(), newscasts.file_hash(path))
                tracks[voice] = {'audio': paths['mp3'][0], 'sha256': paths['mp3'][1],
                                 'video': paths['mp4'][0], 'videoSha256': paths['mp4'][1],
                                 'duration': 30 + index, 'scriptSha256': script_hash,
                                 'fullDecodePassed': True,
                                 'captions': [{'text': script, 'start': .1, 'end': 29}]}
            poster = self.root / 'dist' / 'assets' / f'{identifier}.png'
            poster.write_bytes(b'Checked image fixture')
            stories.append({'id': identifier, 'title': selected['title'], 'script': script,
                            'status': 'ready', 'format': 'studio-programme',
                            'source': {'url': selected['sourceUrl']},
                            'expiresAt': (self.desk.now + timedelta(hours=2)).isoformat(),
                            'programme': {'visualTreatment': 'finished-film'}, 'voices': tracks,
                            'image': poster.relative_to(self.root / 'dist').as_posix(),
                            'video': tracks['measured']['video'],
                            'visual': {'scope': 'story', 'storyId': identifier,
                                       'imageSha256': newscasts.file_hash(poster),
                                       'videoSha256': tracks['measured']['videoSha256']},
                            'production': {'pipeline': 'finished-film-v1',
                                           'newscast': {'jobId': job['id'], 'eventId': selected['id'], 'sourceRevision': selected['revision']},
                                           'selection': {'eventId': selected['id'], 'mode': 'live',
                                                         'approval': {'id': 'approval-' + selected['id']}}}})
        pace = .92 if job['preferences']['pace'] == 'unhurried' else 1
        return {'stories': stories, 'teaser': 'Understand the latest changes affecting household decisions.',
                'duration': sum(story['voices'][job['preferences']['voice']]['duration'] for story in stories) / pace + 1.5 * (len(stories) - 1)}

    def working_executor(self, job, report, guard, root, *, handoff):
        guard()
        report('writing', 'Shaping the selected stories.', completed=0, storyId=job['stories'][0]['id'])
        return self.result(job)

    def test_catalog_requires_real_recent_allowed_domestic_reporting(self):
        self.desk.events += [self.event('stale', age=1441), self.event('future', age=-1),
                            self.event('suppressed', suppressed=True), self.event('foreign-local', foreignLocal=True),
                            self.event('unavailable', available=False), self.event('revision', revisionMismatch=True),
                            self.event('foreign', sourceId='foreign', url='https://foreign.example/news'),
                            self.event('disabled', sourceId='off'), self.event('rebound', url='https://news.example.evil/a'),
                            self.event('credentials', url='https://name:password@news.example/a')]
        catalog = self.store.catalog()
        self.assertEqual([s['id'] for s in catalog['stories']], ['event-one', 'event-two', 'event-three'])
        self.assertFalse(any('evidence' in story for story in catalog['stories']))
        self.assertEqual(catalog['stories'][0]['topicLabel'], 'Business & economy')

    def test_catalog_deduplicates_events_limits_48_and_revision_ignores_fetch_clock(self):
        self.desk.events = [self.event(str(index), age=index) for index in range(55)]
        self.desk.events.append(copy.deepcopy(self.desk.events[0]))
        first = self.store.catalog()['stories']
        self.assertEqual(len(first), 48)
        self.desk.events[0]['evidence'][0]['sourceLastSuccess'] = self.desk.now.isoformat()
        self.assertEqual(first[0]['revision'], self.store.catalog()['stories'][0]['revision'])
        self.desk.events[0]['evidence'][0]['excerpt'] += ' A material correction.'
        self.assertNotEqual(first[0]['revision'], self.store.catalog()['stories'][0]['revision'])

    def test_two_or_three_distinct_choices_and_valid_preferences_are_required(self):
        for count in (0, 1):
            with self.assertRaises(ValueError):
                self.store.create(self.payload(count))
        payload = self.payload()
        payload['stories'][1] = payload['stories'][0]
        with self.assertRaises(ValueError):
            self.store.create(payload)
        for prefs in ({'voice': 'celebrity'}, {'pace': 'fast'}, {'music': 'epic'}, {'token': 'secret'}):
            with self.assertRaises(ValueError):
                self.store.create(self.payload(**prefs))
        self.assertEqual(self.store.create(self.payload(3))['job']['total'], 3)

    def test_create_rejects_changed_sources_and_idempotency_never_duplicates(self):
        payload = self.payload()
        self.desk.events[0]['evidence'][0]['excerpt'] += ' Changed.'
        with self.assertRaises(newscasts.Conflict):
            self.store.create(payload)
        payload = self.payload()
        job = self.store.create(payload)['job']
        self.desk.events[0]['evidence'][0]['available'] = False
        self.assertEqual(self.store.create(payload)['job']['id'], job['id'])
        changed = copy.deepcopy(payload)
        changed['preferences'] = {'music': 'off'}
        with self.assertRaises(newscasts.Conflict):
            self.store.create(changed)
        self.assertEqual(len(list(self.store.folder.glob('newscast-*.json'))), 1)

    def test_unavailable_executor_holds_without_simulated_completion(self):
        job = self.create()
        with patch.object(self.store, '_executor', side_effect=newscasts.NeedsAttention(newscasts.CONNECTION_MESSAGE)):
            self.store.run_pending()
        result = self.store.get(job['id'])['job']
        self.assertEqual(result['status'], 'needs_attention')
        self.assertEqual(result['completed'], 0)
        self.assertNotIn('result', result)
        self.assertIn('Connect', result['message'])

    def test_restart_marks_queued_and_working_jobs_interrupted(self):
        one = self.create()
        two = self.create(music='off')
        self.store._report(two['id'], 'voicing', 'Recording the narration.')
        restarted = self.make_store()
        for job in (one, two):
            current = restarted.get(job['id'])['job']
            self.assertEqual(current['status'], 'interrupted')
            self.assertEqual(current['stories'][0]['revision'], job['stories'][0]['revision'])
        self.assertEqual(len(list(restarted.folder.glob('newscast-*.json'))), 2)

    def test_source_change_during_production_holds_before_ready(self):
        def execute(job, report, guard, root, **kwargs):
            result = self.result(job)
            self.desk.events[0]['evidence'][0]['excerpt'] += ' A correction changed the impact.'
            return result
        self.store.executor = execute
        job = self.create()
        self.store.run_pending()
        current = self.store.get(job['id'])['job']
        self.assertEqual(current['status'], 'needs_attention')
        self.assertNotIn('result', current)

    def test_cancel_is_cooperative_and_never_deletes_media(self):
        def execute(job, report, guard, root, **kwargs):
            self.result(job)
            self.store.cancel(job['id'])
            guard()
            self.fail('Cancellation must stop completion')
        self.store.executor = execute
        job = self.create()
        self.store.run_pending()
        self.assertEqual(self.store.get(job['id'])['job']['status'], 'cancelled')
        self.assertTrue(list((self.root / 'dist' / 'assets').glob('*.mp4')))
        self.assertEqual(self.store.cancel(job['id'])['job']['status'], 'cancelled')
        with self.assertRaises(newscasts.Conflict):
            self.store.retry(job['id'])

    def test_partial_retry_resets_attempt_progress_and_reuses_retained_work(self):
        job = self.create()
        def fail(job, report, guard, root, **kwargs):
            self.result(job)
            report('assembling', 'One story has finished.', completed=1)
            raise RuntimeError('Test interrupted after first story')
        self.store.executor = fail
        self.store.run_pending()
        self.assertEqual(self.store.get(job['id'])['job']['completed'], 1)
        retained = list((self.root / 'dist' / 'assets').glob('*.mp4'))
        self.store.executor = self.working_executor
        retried = self.store.retry(job['id'])['job']
        self.assertEqual(retried['completed'], 0)
        self.assertEqual(retried['attempts'][0]['completed'], 1)
        with patch.object(self.store, '_decode_asset') as decode:
            self.store.run_pending()
        self.assertEqual(self.store.get(job['id'])['job']['status'], 'ready')
        self.assertEqual(decode.call_count, 8)
        self.assertTrue(all(path.exists() for path in retained))

    def test_changed_revision_cannot_be_retried(self):
        job = self.create()
        self.store.executor = lambda *args, **kwargs: (_ for _ in ()).throw(newscasts.NeedsAttention('Connect production.'))
        self.store.run_pending()
        self.desk.events[0]['evidence'][0]['excerpt'] += ' Correction.'
        with self.assertRaises(newscasts.NeedsAttention):
            self.store.retry(job['id'])
        self.assertEqual(self.store.get(job['id'])['job']['status'], 'needs_attention')

    def test_ready_requires_matching_real_media_and_honors_unhurried_duration(self):
        self.store.executor = self.working_executor
        job = self.create(voice='measured', pace='unhurried', music='off')
        with patch.object(self.store, '_decode_asset'):
            self.store.run_pending()
        current = self.store.get(job['id'])['job']
        self.assertEqual(current['status'], 'ready')
        self.assertAlmostEqual(current['result']['duration'], 61 / .92 + 1.5)
        self.assertEqual(current['completed'], 2)
        with self.assertRaises(newscasts.Conflict):
            self.store.cancel(job['id'])

    def test_incomplete_unrelated_duplicate_or_tampered_media_never_becomes_ready(self):
        job = self.create()
        raw = self.store._read(job['id'])
        result = self.result(raw)
        variants = []
        missing = copy.deepcopy(result); missing['stories'].pop(); variants.append(missing)
        unrelated = copy.deepcopy(result); unrelated['stories'][0]['production']['newscast']['eventId'] = 'other'; variants.append(unrelated)
        duplicate = copy.deepcopy(result); duplicate['stories'][1]['id'] = duplicate['stories'][0]['id']; variants.append(duplicate)
        repeated_source = copy.deepcopy(result); repeated_source['stories'][1]['source'] = repeated_source['stories'][0]['source']; variants.append(repeated_source)
        provenance = copy.deepcopy(result); provenance['stories'][0]['voices']['warm']['fullDecodePassed'] = False; variants.append(provenance)
        bad_visual = copy.deepcopy(result); bad_visual['stories'][0]['visual']['storyId'] = 'other'; variants.append(bad_visual)
        with patch.object(self.store, '_decode_asset'):
            for variant in variants:
                with self.subTest(variant=variants.index(variant)), self.assertRaises(ValueError):
                    self.store._validate_result(raw, variant)
            video = self.root / 'dist' / result['stories'][0]['voices']['warm']['video']
            video.write_bytes(b'Changed after render')
            with self.assertRaisesRegex(ValueError, 'hash'):
                self.store._validate_result(raw, result)

    def test_decode_failure_prevents_ready_even_with_valid_hashes(self):
        self.store.executor = self.working_executor
        job = self.create()
        with patch.object(self.store, '_decode_asset', side_effect=RuntimeError('Decode failure')):
            self.store.run_pending()
        self.assertEqual(self.store.get(job['id'])['job']['status'], 'failed')
        self.assertNotIn('result', self.store.get(job['id'])['job'])

    def test_expiry_after_decode_is_rechecked_before_ready(self):
        self.store.executor = self.working_executor
        job = self.create()
        def decode(path):
            if path.name.endswith('event-two-measured.mp3'):
                self.desk.now += timedelta(hours=3)
        with patch.object(self.store, '_decode_asset', side_effect=decode):
            self.store.run_pending()
        self.assertEqual(self.store.get(job['id'])['job']['status'], 'needs_attention')
        self.assertNotIn('result', self.store.get(job['id'])['job'])

    def test_revoked_approval_during_decode_cannot_reach_ready(self):
        handoff = Mock(lock=threading.RLock())
        handoff._guard.side_effect = ValueError('Approval was withdrawn')
        self.store.handoff = handoff
        self.store.executor = self.working_executor
        job = self.create()
        with patch.object(self.store, '_decode_asset'):
            self.store.run_pending()
        self.assertEqual(self.store.get(job['id'])['job']['status'], 'needs_attention')
        self.assertNotIn('result', self.store.get(job['id'])['job'])
        handoff._guard.assert_called()

    def test_existing_production_lock_contention_stays_queued_then_runs(self):
        calls = []
        @contextmanager
        def production_lock():
            calls.append(True)
            if len(calls) == 1:
                raise RuntimeError('Another Bearing production run is active')
            yield
        self.store._production_lock = production_lock
        self.store.executor = self.working_executor
        job = self.create()
        with patch.object(self.store, '_decode_asset'):
            self.store.run_pending()
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.store.get(job['id'])['job']['status'], 'ready')

    def test_single_worker_serializes_distinct_casts(self):
        entered, release = threading.Event(), threading.Event()
        seen, active = [], []
        def execute(job, report, guard, root, **kwargs):
            active.append(job['id'])
            self.assertEqual(len(active), 1)
            seen.append(job['id'])
            entered.set()
            self.assertTrue(release.wait(5))
            active.remove(job['id'])
            raise newscasts.NeedsAttention('Awaiting creative production.')
        self.store.executor = execute
        self.store.autostart = True
        first = self.create()
        self.assertTrue(entered.wait(5))
        worker = self.store.worker
        second = self.create(music='off')
        self.assertIs(self.store.worker, worker)
        release.set()
        worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(seen, [first['id'], second['id']])
        self.assertEqual(self.store.get(second['id'])['job']['status'], 'needs_attention')


class QuietHandler(server.Handler):
    def log_message(self, *args):
        pass


class NewscastServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=cls.temp.name))
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close(); cls.thread.join(); cls.temp.cleanup()

    def request(self, path, method='GET', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.http.server_port, timeout=5)
        payload = json.dumps(body) if body is not None else None
        conn.request(method, path, body=payload, headers={**({'Content-Type': 'application/json'} if body is not None else {}), **(headers or {})})
        response = conn.getresponse(); data = json.loads(response.read()); status = response.status
        conn.close(); return status, data

    def test_catalog_create_status_cancel_and_retry_keep_contract(self):
        store = Mock()
        store.catalog.return_value = {'stories': [], 'generatedAt': '2026-10-01T20:00:00Z', 'capabilities': {'generationReady': False, 'summary': 'Connect production.'}}
        for name in ('create', 'get', 'cancel', 'retry'):
            getattr(store, name).return_value = {'job': {'id': 'newscast-test', 'status': 'queued'}}
        with patch.object(server, 'get_newscasts', return_value=store):
            self.assertEqual(self.request('/api/newscast/catalog')[0], 200)
            self.assertEqual(self.request('/api/newscasts', 'POST', {'stories': []})[1]['job']['status'], 'queued')
            self.assertEqual(self.request('/api/newscasts/newscast-test')[0], 200)
            self.assertEqual(self.request('/api/newscasts/newscast-test/cancel', 'POST', {})[0], 200)
            self.assertEqual(self.request('/api/newscasts/newscast-test/retry', 'POST', {})[0], 200)
            store.cancel.assert_called_once_with('newscast-test')
            store.retry.assert_called_once_with('newscast-test')

    def test_foreign_origins_and_conflicts_do_not_mutate_jobs(self):
        store = Mock()
        with patch.object(server, 'get_newscasts', return_value=store):
            for path, method, body in [('/api/newscast/catalog', 'GET', None), ('/api/newscasts/one', 'GET', None),
                                       ('/api/newscasts', 'POST', {}), ('/api/newscasts/one/retry', 'POST', {})]:
                self.assertEqual(self.request(path, method, body, {'Origin': 'https://foreign.example'})[0], 403)
            store.create.assert_not_called()
            store.create.side_effect = newscasts.Conflict('Reporting changed; refresh.')
            self.assertEqual(self.request('/api/newscasts', 'POST', {})[0], 409)
            store.retry.side_effect = newscasts.NeedsAttention('Fresh reporting needs review.')
            self.assertEqual(self.request('/api/newscasts/one/retry', 'POST', {})[0], 409)
            store.get.side_effect = KeyError('missing')
            self.assertEqual(self.request('/api/newscasts/missing')[0], 404)
            self.assertEqual(self.request('/api/newscasts', 'POST', [])[0], 400)


if __name__ == '__main__':
    unittest.main()
