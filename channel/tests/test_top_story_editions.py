"""Edition publication contracts over isolated evidence and original test images."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'production'))
import top_stories
from top_story_editions import Conflict, EditionStore, stamp


class TopStoryEditionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 10, 2, 14, tzinfo=timezone.utc)
        self.events = [
            self.event('jobs', 'U.S. employers added 29,000 jobs in September',
                       'The national jobs report puts the unemployment rate at 4.2%.'),
            self.event('rights', 'Supreme Court blocked nationwide voting restriction',
                       'The Supreme Court decision changes voting rights nationwide.'),
            self.event('fuel', 'G7 agrees to release fuel reserves',
                       'The U.S. and its partners agreed to release oil stocks in response to fuel supply pressures.'),
        ]
        self.authored = {'items': [self.tile(e, priority=i + 1) for i, e in enumerate(self.events)]}
        self.seed_manifest(self.root, self.authored['items'])
        self.store = EditionStore(self.root)

    def seed_manifest(self, root, items):
        path = root / 'production/top-stories-art-test.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {'schema': 1, 'generator': 'built-in image_gen',
                  'review': 'Isolated synthetic image fixtures inspected for test use only.',
                  'items': [{'url': item['art']['url'], 'kind': 'illustration',
                             'sha256': item['artReview']['sha256']} for item in items]}
        path.write_text(json.dumps(record), encoding='utf-8')

    def event(self, key, title, excerpt):
        report = {'id': 'report-' + key, 'sourceId': 'feed-' + key, 'title': title,
                  'excerpt': excerpt, 'url': 'https://example.org/' + key,
                  'publisher': 'Synthetic source', 'publishedAt': stamp(self.now - timedelta(hours=1)),
                  'sourceLastSuccess': stamp(self.now), 'available': True,
                  'sourceTimeKind': 'published', 'domestic': True}
        return {'id': key, 'title': title, 'evidence': [report], 'decision': {'action': 'none'},
                'assignment': {'scope': 'national', 'lane': 'today',
                               'todayPeg': {'sourceId': report['id'], 'status': 'candidate',
                                            'kind': 'reported-development'}}}

    def emergency(self, key='outage'):
        return self.event(key, 'Nationwide power outage declared an emergency',
                          'Millions of U.S. households face a nationwide power outage.')

    def snapshot(self, events=None, now=None):
        now = now or self.now
        return {'events': copy.deepcopy(self.events if events is None else events),
                'asOf': stamp(now), 'sourceHealth': {'stale': False}}

    def image(self, key):
        path = self.root / 'dist/assets/top-stories' / (key + '.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (1024, 576), (21, 62, 71)).save(path)
        return {'url': '/assets/top-stories/' + path.name, 'kind': 'illustration',
                'alt': 'Synthetic test illustration'}, hashlib.sha256(path.read_bytes()).hexdigest()

    def tile(self, event, now=None, priority=None):
        now = now or self.now
        report = event['evidence'][0]
        art, digest = self.image(event['id'])
        result = {'eventId': event['id'], 'sourceId': report['id'],
                  'evidenceHash': top_stories.evidence_hash(report), 'headline': report['title'],
                  'summary': report['excerpt'], 'reviewedAt': stamp(now),
                  'expiresAt': stamp(now + timedelta(hours=4)),
                  'whyNow': 'The originating source confirms a consequential national development today.',
                  'verifiedPeg': {'kind': 'confirmed-development', 'at': report['publishedAt'],
                                  'clockKind': 'published', 'reason': 'The current originating release confirms the reported development.'},
                  'supportingEvidence': [{'url': 'https://agency.example/' + event['id'],
                                          'publisher': 'Synthetic primary source',
                                          'title': 'Synthetic primary release', 'checkedAt': stamp(now),
                                          'excerpt': report['excerpt']}],
                  'art': art,
                  'artReview': {'verdict': 'accepted', 'generator': 'built-in image_gen',
                                'prompt': 'An isolated synthetic fixture used only to test editorial image publication safeguards.',
                                'sha256': digest, 'reviewedAt': stamp(now)}}
        if priority is not None:
            result['editorialPriority'] = priority
        return result

    def view(self, events=None, now=None, authored=None):
        return self.store.snapshot(self.snapshot(events, now), self.authored if authored is None else authored,
                                   now or self.now)

    def queue(self, event=None):
        event = event or self.emergency()
        snap = self.snapshot([event])
        hero, _ = self.store.snapshot(snap, {'items': []}, self.now)
        self.assertEqual(hero['items'], [])
        jobs = self.store.jobs(snap, self.now)['jobs']
        self.assertEqual(len(jobs), 1)
        return event, snap, jobs[0]

    def payload(self, claim, tile):
        return {'jobId': claim['id'], 'leaseToken': claim['leaseToken'], 'item': tile}

    def test_order_and_refresh_clock_stay_stable_for_fifteen_minutes(self):
        initial, _ = self.view()
        self.assertEqual(len(initial['items']), 3)
        changed = [self.emergency(), *self.events]
        before, rest = self.view(changed, self.now + timedelta(minutes=14, seconds=59))
        self.assertEqual([i['eventId'] for i in before['items']], [i['eventId'] for i in initial['items']])
        self.assertEqual(before['lastEvaluatedAt'], initial['lastEvaluatedAt'])
        self.assertEqual(before['nextRefreshAt'], stamp(self.now + timedelta(minutes=15)))
        self.assertNotIn('outage', [i['eventId'] for i in rest['items']])
        due, _ = self.view(changed, self.now + timedelta(minutes=15))
        self.assertEqual(due['lastEvaluatedAt'], stamp(self.now + timedelta(minutes=15)))
        self.assertEqual(due['nextRefreshAt'], stamp(self.now + timedelta(minutes=30)))
        self.assertEqual(due['preparationState'], 'preparing')
        self.assertEqual([i['eventId'] for i in due['items']], [i['eventId'] for i in initial['items']])

    def test_unready_new_entry_is_hidden_until_complete_atomic_publication(self):
        initial, _ = self.view()
        event = self.emergency()
        now = self.now + timedelta(minutes=15)
        snap = self.snapshot([event, *self.events], now)
        pending, _ = self.store.snapshot(snap, self.authored, now)
        self.assertEqual([i['eventId'] for i in pending['items']], [i['eventId'] for i in initial['items']])
        job = self.store.jobs(snap, now)['jobs'][0]
        claim = self.store.claim(job['id'], now)
        result = self.store.finish(self.payload(claim, self.tile(event, now)), snap, self.authored, now)
        self.assertEqual(result['state'], 'ready')
        # A finished job alone does not partially overwrite the visible edition.
        state = self.store._read()
        self.assertNotIn('outage', [i['eventId'] for i in state['edition']['items'][:3]])
        ready, _ = self.store.snapshot(snap, self.authored, now)
        self.assertEqual(ready['items'][0]['eventId'], 'outage')
        self.assertEqual(len(ready['items']), 3)
        self.assertEqual(ready['preparationState'], 'idle')

    def test_initial_edition_does_not_reveal_a_partially_prepared_hero(self):
        hero, _ = self.view(authored={'items': []})
        self.assertEqual(hero['items'], [])
        snap = self.snapshot()
        jobs = self.store.jobs(snap)['jobs']
        event = next(e for e in self.events if e['id'] == jobs[0]['eventId'])
        claim = self.store.claim(jobs[0]['id'], self.now)
        self.store.finish(self.payload(claim, self.tile(event)), snap, {'items': []}, self.now)
        partial, _ = self.view(authored={'items': []})
        self.assertEqual(partial['items'], [], 'The initial hero should publish as a complete edition, not one card at a time.')

    def test_two_replacements_do_not_publish_until_both_are_ready(self):
        initial, _ = self.view()
        outage = self.emergency()
        water = self.event('water', 'Multi-state emergency declared after water contamination',
                           'Multiple states report life-threatening water contamination affecting U.S. households.')
        now = self.now + timedelta(minutes=15)
        snap = self.snapshot([outage, water, *self.events], now)
        self.store.snapshot(snap, self.authored, now)
        jobs = self.store.jobs(snap, now)['jobs']
        self.assertEqual(len(jobs), 2)
        for index, job in enumerate(jobs):
            event = next(e for e in (outage, water) if e['id'] == job['eventId'])
            claim = self.store.claim(job['id'], now)
            self.store.finish(self.payload(claim, self.tile(event, now)), snap, self.authored, now)
            visible, _ = self.store.snapshot(snap, self.authored, now)
            if index == 0:
                self.assertEqual([i['eventId'] for i in visible['items']], [i['eventId'] for i in initial['items']])
        self.assertEqual({i['eventId'] for i in visible['items'][:2]}, {'outage', 'water'})
        self.assertEqual(len(visible['items']), 3)

    def test_changed_held_unavailable_or_stale_evidence_is_withheld_immediately(self):
        for mutation in ('changed', 'held', 'unavailable', 'stale'):
            with self.subTest(mutation=mutation):
                changed_root = self.root / mutation
                # Install existing test art in this independent store root.
                for item in self.authored['items']:
                    dest = changed_root / 'dist' / item['art']['url'].lstrip('/')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes((self.root / 'dist' / item['art']['url'].lstrip('/')).read_bytes())
                self.seed_manifest(changed_root, self.authored['items'])
                self.store = EditionStore(changed_root)
                initial, _ = self.view()
                target = initial['items'][0]['eventId']
                events = copy.deepcopy(self.events)
                event = next(e for e in events if e['id'] == target)
                if mutation == 'changed':
                    event['evidence'][0]['excerpt'] += ' A correction changes the result.'
                elif mutation == 'held':
                    event['assignment']['lane'] = 'held'
                elif mutation == 'unavailable':
                    event['evidence'][0]['available'] = False
                else:
                    event['evidence'][0]['sourceLastSuccess'] = stamp(self.now - timedelta(hours=3))
                hero, order = self.view(events, self.now + timedelta(minutes=1))
                self.assertNotIn(target, [i['eventId'] for i in hero['items']])
                self.assertNotIn(target, [i['eventId'] for i in order['items']])
                self.assertEqual(hero['lastEvaluatedAt'], initial['lastEvaluatedAt'])

    def test_stale_collection_withholds_retained_current_cards(self):
        self.view()
        snap = self.snapshot()
        snap['sourceHealth']['stale'] = True
        hero, order = self.store.snapshot(snap, self.authored, self.now + timedelta(minutes=1))
        self.assertEqual(hero['items'], [])
        self.assertEqual(order['items'], [])
        self.assertEqual(hero['status'], 'stale')

    def test_claim_is_exclusive_secret_is_not_in_job_listing_and_restart_is_durable(self):
        event, snap, job = self.queue()
        claim = self.store.claim(job['id'], self.now)
        self.assertTrue(claim['leaseToken'])
        self.assertEqual(claim['attempts'], 1)
        with self.assertRaises(Conflict):
            self.store.claim(job['id'], self.now)
        self.store = EditionStore(self.root)
        listed = self.store.jobs(snap, self.now)['jobs'][0]
        self.assertEqual(listed['state'], 'working')
        self.assertNotIn('leaseToken', listed)
        self.assertEqual(self.store.finish(self.payload(claim, self.tile(event)), snap, {'items': []}, self.now)['state'], 'ready')

    def test_expired_lease_is_requeued_and_old_completion_is_rejected(self):
        event, snap, job = self.queue()
        old = self.store.claim(job['id'], self.now)
        later = self.now + timedelta(minutes=12, seconds=1)
        self.store = EditionStore(self.root)
        self.store.snapshot(self.snapshot([event], later), {'items': []}, later)
        current = self.store.claim(job['id'], later)
        self.assertEqual(current['attempts'], 2)
        self.assertNotEqual(current['leaseToken'], old['leaseToken'])
        with self.assertRaises(Conflict):
            self.store.finish(self.payload(old, self.tile(event, later)), snap, {'items': []}, later)

    def test_hold_retries_only_when_due_and_retains_attempt_history(self):
        event, snap, job = self.queue()
        claim = self.store.claim(job['id'], self.now)
        result = self.store.finish({'jobId': job['id'], 'leaseToken': claim['leaseToken'],
                                    'action': 'hold', 'reason': 'The source still needs a primary evidence check.'}, snap, {}, self.now)
        self.assertEqual(result['state'], 'needs_attention')
        with self.assertRaises(Conflict):
            self.store.claim(job['id'], self.now + timedelta(minutes=14))
        later = self.now + timedelta(minutes=15)
        self.store.snapshot(self.snapshot([event], later), {}, later)
        retry = self.store.claim(job['id'], later)
        self.assertEqual(retry['attempts'], 2)

    def test_source_hash_drift_rejects_completion_without_publishing(self):
        event, snap, job = self.queue()
        claim = self.store.claim(job['id'], self.now)
        old_tile = self.tile(event)
        snap['events'][0]['evidence'][0]['excerpt'] += ' New reporting changes the affected scale.'
        with self.assertRaises(Conflict):
            self.store.finish(self.payload(claim, old_tile), snap, {}, self.now)
        self.assertEqual(self.store._read()['tiles'], {})

    def test_superseded_job_cannot_complete_under_an_unexpired_old_lease(self):
        event, snap, job = self.queue(self.events[2])
        claim = self.store.claim(job['id'], self.now + timedelta(minutes=14))
        now = self.now + timedelta(minutes=15)
        new_snapshot = self.snapshot([self.emergency(), *self.events], now)
        self.store.snapshot(new_snapshot, {'items': []}, now)
        self.assertEqual(self.store._read()['jobs'][job['id']]['state'], 'superseded')
        with self.assertRaises(Conflict):
            self.store.finish(self.payload(claim, self.tile(event, now)), new_snapshot, {}, now)

    def test_wrong_source_or_lease_cannot_complete_a_claim(self):
        event, snap, job = self.queue()
        claim = self.store.claim(job['id'], self.now)
        valid = self.tile(event)
        payload = self.payload(claim, valid)
        payload['leaseToken'] = 'not-the-current-token'
        with self.assertRaises(Conflict):
            self.store.finish(payload, snap, {}, self.now)
        for field in ('eventId', 'sourceId', 'evidenceHash'):
            changed = copy.deepcopy(valid)
            changed[field] = 'wrong'
            with self.subTest(field=field), self.assertRaises(Conflict):
                self.store.finish(self.payload(claim, changed), snap, {}, self.now)

    def test_inspected_checked_in_art_cannot_silently_change(self):
        initial, _ = self.view()
        target = initial['items'][0]
        path = self.root / 'dist' / target['art']['url'].lstrip('/')
        Image.new('RGB', (1024, 576), 'red').save(path)
        hero, _ = self.view(now=self.now + timedelta(minutes=1))
        self.assertNotIn(target['eventId'], [i['eventId'] for i in hero['items']],
                         'A changed seed image no longer matches its recorded inspection hash.')

    def test_ready_authored_tile_resolves_an_earlier_pending_job(self):
        event, snap, job = self.queue(self.events[0])
        hero, _ = self.store.snapshot(snap, {'items': [self.tile(event)]}, self.now)
        self.assertEqual(len(hero['items']), 1)
        self.assertEqual(hero['preparingCount'], 0,
                         'A complete ready tile should not retain a phantom queued preparation job.')

    def test_removal_does_not_promote_rank_four_before_next_edition(self):
        fourth = self.event('loans', 'Congress approved federal student loan repayment rule',
                            'The federal student loan rule changes repayment eligibility for American borrowers.')
        self.events.append(fourth)
        self.authored['items'].append(self.tile(fourth))
        self.seed_manifest(self.root, self.authored['items'])
        self.store = EditionStore(self.root)
        initial, order = self.view()
        self.assertEqual(len(initial['items']), 3)
        self.assertEqual(len(order['items']), 4)
        fourth_id = order['items'][3]['eventId']
        removed = initial['items'][0]['eventId']
        changed = copy.deepcopy(self.events)
        next(e for e in changed if e['id'] == removed)['assignment']['lane'] = 'held'
        hero, remaining = self.view(changed, self.now + timedelta(minutes=1))
        self.assertNotIn(fourth_id, hero['reservedEventIds'])
        self.assertNotIn(fourth_id, [i['eventId'] for i in hero['items']])
        self.assertEqual(next(i['rank'] for i in remaining['items'] if i['eventId'] == fourth_id), 4)
        self.assertEqual(hero['preparingCount'], 0)

    def test_invalid_hash_path_or_art_review_rejects_completion(self):
        event, snap, job = self.queue()
        claim = self.store.claim(job['id'], self.now)
        valid = self.tile(event)
        variants = []
        for url in ('/assets/top-stories/../outside.png', 'https://example.org/picture.png',
                    '/assets/top-stories/test.svg', '/assets/top-stories/test.png?remote=1'):
            changed = copy.deepcopy(valid); changed['art']['url'] = url; variants.append(changed)
        for field, value in (('sha256', '0' * 64), ('verdict', 'pending'), ('generator', 'unknown'),
                             ('reviewedAt', stamp(self.now - timedelta(minutes=31)))):
            changed = copy.deepcopy(valid); changed['artReview'][field] = value; variants.append(changed)
        for tile in variants:
            with self.subTest(tile=tile['art']['url'], review=tile['artReview']):
                with self.assertRaises(ValueError):
                    self.store.finish(self.payload(claim, tile), snap, {}, self.now)
                self.assertEqual(self.store._read()['tiles'], {})

    def test_missing_small_malformed_and_replaced_images_are_not_ready(self):
        event, snap, job = self.queue()
        claim = self.store.claim(job['id'], self.now)
        tile = self.tile(event)
        path = self.root / 'dist' / tile['art']['url'].lstrip('/')
        original = path.read_bytes()
        path.unlink()
        self.assertIsNone(self.store._art(tile['art']))
        path.write_bytes(b'not an image' * 100)
        self.assertIsNone(self.store._art(tile['art']))
        Image.new('RGB', (160, 90), 'red').save(path)
        self.assertIsNone(self.store._art(tile['art']))
        Image.new('RGB', (1024, 1024), 'red').save(path)
        self.assertIsNone(self.store._art(tile['art']))
        path.write_bytes(original)
        self.store.finish(self.payload(claim, tile), snap, {}, self.now)
        self.store.snapshot(snap, {}, self.now)
        Image.new('RGB', (1024, 576), 'red').save(path)
        self.assertEqual(self.store.snapshot(snap, {}, self.now)[0]['items'], [])

    def test_inputs_and_production_authority_are_never_mutated(self):
        sentinel = self.root / 'production/runs/producer-state.json'
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text('{"approval":"untouched"}', encoding='utf-8')
        snap, authored = self.snapshot(), copy.deepcopy(self.authored)
        original = copy.deepcopy((snap, authored))
        self.store.snapshot(snap, authored, self.now)
        self.assertEqual((snap, authored), original)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), '{"approval":"untouched"}')
        self.assertFalse((self.root / 'dist/films.json').exists())

    def test_corrupt_saved_state_is_not_silently_reset(self):
        self.view()
        self.store.path.write_text('{broken', encoding='utf-8')
        with self.assertRaises(RuntimeError):
            self.view()
        self.assertEqual(self.store.path.read_text(encoding='utf-8'), '{broken')


if __name__ == '__main__':
    unittest.main()
