"""Exercise the producer boundary through HTTP without production or networking."""
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


class FakeProducer:
    def __init__(self):
        self.decisions = []

    def snapshot(self, mode='live'):
        return {'mode': mode, 'events': [], 'decisionCount': len(self.decisions)}

    def decide(self, event_id, action, note='', mode='live'):
        if event_id == 'missing':
            raise KeyError(event_id)
        self.decisions.append((event_id, action, note, mode))
        return self.snapshot(mode)

    def demo(self, action):
        return {**self.snapshot('demo'), 'action': action}


class FakeHandoff:
    def __init__(self):self.calls=[]
    def get(self,event_id,mode='live'):
        if not event_id or mode not in ('live','demo'):raise ValueError('Choose a valid opportunity and news mode')
        self.calls.append(('get',event_id,mode));return {'selection':None}
    def mutate(self,payload):
        from selection import Conflict
        if payload.get('expectedRevision')==1:raise Conflict('The selection changed; refresh before approving')
        self.calls.append(('mutate',payload));return {'selection':{'eventId':payload.get('eventId'),'state':'selected','revision':1}}


class QuietHandler(server.Handler):
    def log_message(self, *args):
        pass


class ProducerServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        (Path(cls.folder.name) / 'index.html').write_text('Bearing viewer stays available', encoding='utf-8')
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=cls.folder.name))
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        cls.folder.cleanup()

    def setUp(self):
        self.producer = FakeProducer()
        self.mock = patch.object(server, 'get_producer', return_value=self.producer)
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def request(self, path='/api/producer', method='GET', body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.http.server_port, timeout=5)
        payload = json.dumps(body) if isinstance(body, (dict, list)) else body
        defaults = {'Content-Type': 'application/json'} if body is not None else {}
        connection.request(method, path, body=payload, headers={**defaults, **(headers or {})})
        response = connection.getresponse()
        data = response.read()
        result = (response.status, dict(response.getheaders()), data)
        connection.close()
        return result

    def test_read_modes_do_not_make_editorial_decisions(self):
        for mode in ('live', 'demo'):
            status, headers, body = self.request('/api/producer?mode=' + mode)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)['mode'], mode)
            self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(self.producer.decisions, [])
        self.assertEqual(self.request('/api/producer?mode=unknown')[0], 400)
        self.assertEqual(self.request('/')[2], b'Bearing viewer stays available')

    def test_local_json_decision_and_demo_are_separate(self):
        port = self.http.server_port
        decision = {'eventId': 'event-one', 'action': 'watch', 'note': 'Wait for the effective date.', 'mode': 'live'}
        status, _, body = self.request('/api/producer/decision', 'POST', decision, {'Origin': f'http://127.0.0.1:{port}'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['decisionCount'], 1)
        self.assertEqual(self.producer.decisions[0], ('event-one', 'watch', 'Wait for the effective date.', 'live'))
        status, _, body = self.request('/api/producer/demo', 'POST', {'action': 'advance'})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['mode'], 'demo')
        self.assertEqual(len(self.producer.decisions), 1)

    def test_cross_origin_and_rebound_hosts_cannot_read_or_change_notes(self):
        for headers in ({'Origin': 'https://foreign.example'}, {'Origin': 'null'}, {'Host': f'foreign.example:{self.http.server_port}'}):
            self.assertEqual(self.request(headers=headers)[0], 403)
            self.assertEqual(self.request('/api/producer/decision', 'POST', {'eventId': 'one', 'action': 'dismiss'}, headers)[0], 403)
        self.assertFalse(self.producer.decisions)

    def test_bad_requests_fail_without_editorial_side_effects(self):
        path = '/api/producer/decision'
        for body in ({'eventId': 'one', 'action': 'publish'}, {'eventId': '../one', 'action': 'watch', 'mode': 'arbitrary'}, {'eventId': 'one', 'action': 'watch', 'note': 'x' * 501}, [], '{bad json'):
            self.assertEqual(self.request(path, 'POST', body)[0], 400)
        self.assertEqual(self.request(path, 'POST', 'x' * 8193)[0], 413)
        self.assertEqual(self.request(path, 'POST', '{}', {'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request(path, 'POST', {'eventId': 'missing', 'action': 'watch'})[0], 404)
        self.assertEqual(self.request('/api/producer/demo', 'POST', {'action': 'publish'})[0], 400)
        self.assertFalse(self.producer.decisions)

    def test_handoff_keeps_its_review_record_separate_from_curation(self):
        handoff=FakeHandoff()
        with patch.object(server,'get_handoff',return_value=handoff):
            status,headers,body=self.request('/api/producer/handoff?eventId=event-one&mode=live')
            self.assertEqual(status,200);self.assertEqual(json.loads(body),{'selection':None})
            self.assertEqual(headers['Cache-Control'],'no-store')
            payload={'action':'select','eventId':'event-one','mode':'live','productId':'focus','whyNow':'A current consequential development.'}
            status,_,body=self.request('/api/producer/handoff','POST',payload)
            self.assertEqual(status,200);self.assertEqual(json.loads(body)['selection']['state'],'selected')
            self.assertEqual(self.producer.decisions,[])
            self.assertEqual(handoff.calls[-1],('mutate',payload))

    def test_handoff_conflicts_and_larger_bounded_review_payload(self):
        handoff=FakeHandoff()
        with patch.object(server,'get_handoff',return_value=handoff):
            status,_,body=self.request('/api/producer/handoff','POST',{'action':'review','eventId':'event-one','expectedRevision':1})
            self.assertEqual(status,409);self.assertIn('refresh',json.loads(body)['error'])
            self.assertFalse(handoff.calls)
            self.assertEqual(self.request('/api/producer/handoff','POST',{'action':'save','eventId':'event-one','draft':{'notes':'x'*9000}})[0],200)
            before=len(handoff.calls)
            self.assertEqual(self.request('/api/producer/handoff','POST','x'*131073)[0],413)
            self.assertEqual(self.request('/api/producer/handoff','POST',{'action':'select'},{'Origin':'https://foreign.example'})[0],403)
            self.assertEqual(self.request('/api/producer/handoff?eventId=event-one',headers={'Origin':'null'})[0],403)
            self.assertEqual(len(handoff.calls),before)

    def test_handoff_bad_json_and_missing_selection_fail_cleanly(self):
        with patch.object(server,'get_handoff',return_value=FakeHandoff()):
            self.assertEqual(self.request('/api/producer/handoff')[0],400)
            self.assertEqual(self.request('/api/producer/handoff?eventId=one&mode=unknown')[0],400)
            for body in ('{bad',[]):self.assertEqual(self.request('/api/producer/handoff','POST',body)[0],400)


if __name__ == '__main__':
    unittest.main()
