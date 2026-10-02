"""Exercise tile-preparation HTTP boundaries with isolated editorial state."""
import http.client
import json
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'production'))
import server
from top_story_editions import Conflict


class QuietHandler(server.Handler):
    def log_message(self, *args):
        pass


class TrackedLock:
    """Assert HTTP handlers keep snapshot and preparation operations together."""
    def __init__(self):
        self.depth = 0
        self.lock = threading.RLock()

    def __enter__(self):
        self.lock.acquire()
        self.depth += 1

    def __exit__(self, *args):
        self.depth -= 1
        self.lock.release()


class FakeEditions:
    def __init__(self, desk):
        self.desk = desk
        self.calls = []

    def _check_lock(self):
        if self.desk.lock.depth < 1:
            raise AssertionError('Preparation must share the producer snapshot lock.')

    def jobs(self, snapshot):
        self._check_lock()
        self.calls.append(('jobs', snapshot))
        return {'jobs': [{'id': 'tile-one', 'status': 'queued'}], 'sourceRevision': snapshot['revision']}

    def claim(self, job_id):
        self._check_lock()
        if not self.desk.snapshots:
            raise AssertionError('Claim must observe current reporting first.')
        self.calls.append(('claim', job_id))
        if job_id != 'tile-one':
            raise Conflict('This tile is not available to claim.')
        return {'job': {'id': job_id, 'status': 'preparing', 'lease': 'lease-one'}}

    def finish(self, payload, snapshot, authored):
        self._check_lock()
        self.calls.append(('finish', payload, snapshot, authored))
        if payload.get('jobId') != 'tile-one' or payload.get('lease') != 'lease-one':
            raise Conflict('This preparation lease is not current.')
        if payload.get('evidenceRevision') != snapshot['revision']:
            raise Conflict('Current reporting no longer supports this tile.')
        return {'job': {'id': 'tile-one', 'status': 'held' if payload['action'] == 'hold' else 'ready'}}


class FakeProducer:
    def __init__(self, work):
        self.work = work
        self.lock = TrackedLock()
        self.revision = 1
        self.snapshots = []
        self.edition_store = FakeEditions(self)

    def snapshot(self):
        if self.lock.depth < 1:
            raise AssertionError('Snapshot must be read under the producer lock.')
        snapshot = {'revision': self.revision, 'events': [], 'sequence': len(self.snapshots) + 1}
        self.snapshots.append(snapshot)
        return snapshot


class TopStoryHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.static = tempfile.TemporaryDirectory()
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=cls.static.name))
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        cls.static.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.authored = {'items': [{'eventId': 'reviewed-source-record'}]}
        (Path(self.work.name) / 'top-stories-editorial.json').write_text(json.dumps(self.authored), encoding='utf-8')
        self.desk = FakeProducer(Path(self.work.name))
        self.producer = self.patch('get_producer', return_value=self.desk)
        self.handoff = self.patch('get_handoff', side_effect=AssertionError('Tile preparation must not approve a production handoff.'))
        self.newscasts = self.patch('get_newscasts', side_effect=AssertionError('Tile preparation must not launch a newscast.'))
        self.production = patch.object(server.subprocess, 'run', side_effect=AssertionError('The HTTP request must not start media production.'))
        self.production_mock = self.production.start()
        self.addCleanup(self.production.stop)

    def patch(self, name, **kwargs):
        patcher = patch.object(server, name, **kwargs)
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def request(self, path='/api/top-stories/jobs', method='GET', payload=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.http.server_port, timeout=5)
        body = json.dumps(payload) if isinstance(payload, (dict, list)) else payload
        request_headers = {'Content-Type': 'application/json'} if payload is not None else {}
        connection.request(method, path, body=body, headers={**request_headers, **(headers or {})})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), json.loads(response.read())
        connection.close()
        return result

    def assert_no_production(self):
        self.handoff.assert_not_called()
        self.newscasts.assert_not_called()
        self.production_mock.assert_not_called()

    def test_jobs_reads_fresh_snapshot_and_is_not_cacheable(self):
        self.desk.revision = 7
        status, headers, data = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(data['sourceRevision'], 7)
        self.assertIs(self.desk.edition_store.calls[0][1], self.desk.snapshots[0])
        self.assertEqual(len(self.desk.snapshots), 1)
        self.assert_no_production()

    def test_foreign_origins_and_rebound_hosts_cannot_read_or_prepare(self):
        port = self.http.server_port
        for headers in [{'Origin': 'https://foreign.example'}, {'Origin': 'null'},
                        {'Host': f'foreign.example:{port}'}, {'Host': 'localhost:1'}]:
            self.assertEqual(self.request(headers=headers)[0], 403)
            self.assertEqual(self.request('/api/top-stories/prepare', 'POST', {'action': 'claim', 'jobId': 'tile-one'}, headers)[0], 403)
        self.producer.assert_not_called()
        self.assertEqual(self.desk.edition_store.calls, [])
        self.assert_no_production()

    def test_unknown_actions_and_invalid_json_fail_without_preparation(self):
        for body in [{'action': 'publish', 'jobId': 'tile-one'}, {}, [], '{bad json']:
            self.assertEqual(self.request('/api/top-stories/prepare', 'POST', body)[0], 400)
        self.assertEqual(self.request('/api/top-stories/prepare', 'POST', '{}', {'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.desk.edition_store.calls, [])
        self.assert_no_production()

    def test_unknown_job_or_invalid_lease_is_a_conflict_not_success(self):
        for payload in [{'action': 'claim'}, {'action': 'claim', 'jobId': 'missing'},
                        {'action': 'complete', 'jobId': 'tile-one', 'lease': 'wrong', 'evidenceRevision': 1}]:
            status, _, body = self.request('/api/top-stories/prepare', 'POST', payload)
            self.assertEqual(status, 409)
            self.assertIn('error', body)
        self.assert_no_production()

    def test_valid_claim_observes_current_snapshot_without_production(self):
        self.desk.revision = 4
        origin = f'http://127.0.0.1:{self.http.server_port}'
        status, _, body = self.request('/api/top-stories/prepare', 'POST', {'action': 'claim', 'jobId': 'tile-one'}, {'Origin': origin})
        self.assertEqual(status, 200)
        self.assertEqual(body['job']['status'], 'preparing')
        self.assertEqual(self.desk.snapshots, [{'revision': 4, 'events': [], 'sequence': 1}])
        self.assertEqual(self.desk.edition_store.calls, [('claim', 'tile-one')])
        self.assert_no_production()

    def test_completion_revalidates_server_snapshot_and_refreshes_after_acceptance(self):
        self.desk.revision = 3
        payload = {'action': 'complete', 'jobId': 'tile-one', 'lease': 'lease-one', 'evidenceRevision': 3,
                   'snapshot': {'revision': 999, 'events': ['client-supplied']}}
        status, _, body = self.request('/api/top-stories/prepare', 'POST', payload)
        self.assertEqual(status, 200)
        self.assertEqual(body['job']['status'], 'ready')
        call = self.desk.edition_store.calls[0]
        self.assertEqual(call[0], 'finish')
        self.assertIs(call[2], self.desk.snapshots[0])
        self.assertEqual(call[2]['revision'], 3)
        self.assertEqual(call[3], self.authored)
        self.assertEqual(len(self.desk.snapshots), 2)
        self.assert_no_production()

    def test_changed_reporting_cannot_complete_against_claim_time_revision(self):
        self.assertEqual(self.request('/api/top-stories/prepare', 'POST', {'action': 'claim', 'jobId': 'tile-one'})[0], 200)
        self.desk.revision = 2
        payload = {'action': 'complete', 'jobId': 'tile-one', 'lease': 'lease-one', 'evidenceRevision': 1}
        status, _, body = self.request('/api/top-stories/prepare', 'POST', payload)
        self.assertEqual(status, 409)
        self.assertIn('Current reporting', body['error'])
        self.assertEqual(self.desk.edition_store.calls[-1][2]['revision'], 2)
        self.assertEqual(len(self.desk.snapshots), 2)
        self.assert_no_production()

    def test_hold_and_unavailable_state_preserve_explicit_failure_contract(self):
        status, _, body = self.request('/api/top-stories/prepare', 'POST', {'action': 'hold', 'jobId': 'tile-one', 'lease': 'lease-one', 'evidenceRevision': 1})
        self.assertEqual(status, 200)
        self.assertEqual(body['job']['status'], 'held')
        with patch.object(self.desk, 'snapshot', side_effect=RuntimeError('Unreadable saved state')):
            self.assertEqual(self.request()[0], 503)
            self.assertEqual(self.request('/api/top-stories/prepare', 'POST', {'action': 'claim', 'jobId': 'tile-one'})[0], 503)
        self.assertEqual(len(self.desk.edition_store.calls), 1)
        self.assert_no_production()


if __name__ == '__main__':
    unittest.main()
