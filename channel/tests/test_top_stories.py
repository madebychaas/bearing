import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'production'))
import top_stories


class TopStoriesTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 2, 14, tzinfo=timezone.utc)

    def event(self, identity='jobs', title='U.S. employers added 29,000 jobs in September', excerpt='The unemployment rate rose to 4.2% in the new national jobs report.', **report_changes):
        report = {'id': 'report-'+identity, 'sourceId': 'feed', 'title': title, 'excerpt': excerpt,
                  'publisher': 'Publisher', 'url': 'https://example.com/'+identity, 'publishedAt': '2026-10-02T12:30:00Z',
                  'sourceLastSuccess': '2026-10-02T13:59:00Z', 'available': True, 'sourceTimeKind': 'published', 'domestic': True}
        report.update(report_changes)
        return {'id': identity, 'evidence': [report], 'decision': {'action': 'none'},
                'assignment': {'scope': 'national', 'lane': 'today', 'todayPeg': {'status': 'candidate', 'kind': 'reported-development', 'sourceId': report['id']}}}

    def snapshot(self, events):
        return {'events': events, 'asOf': '2026-10-02T13:59:00Z', 'sourceHealth': {'stale': False}}

    def select(self, events, authored=None):
        return top_stories.select(self.snapshot(events), authored, self.now)

    def authored(self, event, **changes):
        report = event['evidence'][0]
        item = {'eventId': event['id'], 'sourceId': report['id'], 'evidenceHash': top_stories.evidence_hash(report),
                'headline': 'New jobs report shows hiring slowing', 'summary': 'Unemployment edged higher.',
                'reviewedAt': '2026-10-02T13:30:00Z', 'expiresAt': '2026-10-02T17:30:00Z',
                'whyNow': 'Today’s verified release changes the national economic picture.',
                'verifiedPeg': {'kind': 'confirmed-development', 'at': '2026-10-02T12:30:00Z', 'reason': 'The originating release confirms the new reported development.'},
                'supportingEvidence': [{'url': 'https://agency.gov/release', 'publisher': 'Originating agency', 'title': 'Current release',
                                        'checkedAt': '2026-10-02T13:20:00Z', 'excerpt': 'The originating release reports this current nationwide change.'}]}
        item.update(changes)
        return item

    def test_importance_beats_fresh_institution_name_and_narrow_enforcement(self):
        fed = self.event('fed', 'Federal Reserve issues enforcement action with Ontario Bancorporation',
                         'The Federal Reserve announced an enforcement action concerning a single bank.', publishedAt='2026-10-02T13:59:00Z')
        launch = self.event('space', 'NASA launches a new mission', 'Four astronauts have launched into orbit on a scheduled mission.')
        result = self.select([fed, launch, self.event()])
        self.assertEqual([item['eventId'] for item in result['items']], ['jobs'])
        self.assertIn('more distinct', result['message'])

    def test_duplicate_jobs_and_diesel_coverage_only_take_one_slot_each(self):
        jobs = self.event()
        other_jobs = self.event('jobs-two', 'Labor market slows as payrolls rise 29,000', 'The unemployment rate rose in the latest jobs report.')
        oil = self.event('oil', 'Oil prices fall as fuel reserves grow', 'U.S. oil supplies grew as emergency reserves were released.')
        diesel = self.event('diesel', 'Diesel stocks released as U.S. fuel prices rise', 'Fuel reserves are being released in response to the supply crunch.')
        oversight = self.event('oversight', 'Federal housing official cuts watchdog office', 'The inspector general’s office oversees the federal housing regulator.')
        result = self.select([other_jobs, oil, jobs, diesel, oversight])
        self.assertEqual(len(result['items']), 3)
        self.assertEqual({item['family'] for item in result['items']}, {'us-jobs', 'energy-supply', 'public-oversight'})
        self.assertEqual(result['items'][0]['family'], 'us-jobs')

    def test_distinct_policy_stories_are_not_collapsed_by_broad_category(self):
        taxes = self.event('tax', 'Federal child tax credit expanded', 'Congress approved a larger child tax credit for families nationwide.')
        health = self.event('health', 'Supreme Court blocks Medicaid eligibility rule', 'The court blocked a federal eligibility rule affecting Medicaid recipients.')
        self.assertEqual(len(self.select([taxes, health])['items']), 2)

    def test_held_stale_local_future_and_unavailable_reports_never_fill_slots(self):
        variants = [dict(available=False), dict(revisionMismatch=True), dict(local=True), dict(sourceTimeKind='updated'),
                    dict(sourceTimeKind='filed'), dict(publishedAt='2026-10-01T10:00:00Z'),
                    dict(publishedAt='2026-10-02T15:00:00Z'), dict(sourceLastSuccess='2026-10-02T10:00:00Z')]
        for changes in variants:
            with self.subTest(changes=changes):
                self.assertEqual(self.select([self.event(**changes)])['items'], [])
        for scope, lane in [('local', 'today'), ('national', 'held'), ('national', 'watch')]:
            item = self.event(); item['assignment'].update(scope=scope, lane=lane)
            self.assertEqual(self.select([item])['items'], [])

    def test_stale_collection_does_not_leave_a_current_hero(self):
        snapshot = self.snapshot([self.event()]); snapshot['asOf'] = '2026-10-02T10:00:00Z'
        result = top_stories.select(snapshot, now=self.now)
        self.assertEqual(result['status'], 'stale'); self.assertEqual(result['items'], [])

    def test_forecast_conflict_reaction_and_uk_only_price_story_are_excluded(self):
        cases = [('U.S. payrolls added 29,000 jobs', 'Payrolls were expected to rise by 84,000 before the release.'),
                 ('President responds to new jobs report', 'U.S. payrolls rose 29,000, with unemployment at 4.2%.'),
                 ('UK diesel price hits £2 a litre as US calls for reserves', 'British drivers face rising prices at the pump.')]
        for title, excerpt in cases:
            self.assertEqual(self.select([self.event(title=title, excerpt=excerpt)])['items'], [])

    def test_peg_report_identity_is_used_instead_of_event_title_or_another_report(self):
        event = self.event(); event['title'] = 'Unrelated or newer headline'
        event['evidence'].append({**event['evidence'][0], 'id': 'other', 'title': 'Different source headline'})
        result = self.select([event])['items'][0]
        self.assertEqual(result['headline'], event['evidence'][0]['title']); self.assertEqual(result['sourceId'], 'report-jobs')
        self.assertEqual(result['evidenceIds'], ['report-jobs'])
        event['assignment']['todayPeg']['sourceId'] = 'missing'
        self.assertEqual(self.select([event])['items'], [])

    def test_fallback_copy_is_exact_source_not_invented_or_truncated(self):
        event = self.event(excerpt='This unfinished excerpt without its conclusion')
        result = self.select([event])['items'][0]
        self.assertEqual(result['headline'], event['evidence'][0]['title']); self.assertEqual(result['summary'], '')
        self.assertEqual(result['copyKind'], 'source')
        event['evidence'][0]['excerpt'] = 'The U.S. unemployment rate rose to 4.2%. A second sentence follows with context.'
        self.assertEqual(self.select([event])['items'][0]['summary'], event['evidence'][0]['excerpt'])
        incomplete = 'A report about hiring by the U.S. Government continues ' + 'with important context ' * 12
        self.assertEqual(top_stories._sentence(incomplete), '')

    def test_reviewed_copy_and_illustration_expire_on_exact_source_change(self):
        event = self.event(); item = self.authored(event, art={'url': '/assets/top-stories/jobs.png', 'alt': 'Original conceptual illustration', 'kind': 'illustration'})
        result = self.select([event], {'items': [item]})['items'][0]
        self.assertEqual(result['copyKind'], 'editorial'); self.assertEqual(result['art']['label'], 'AI illustration')
        self.assertEqual(result['supportingEvidence'][0]['url'], 'https://agency.gov/release')
        for key in ('excerpt', 'title', 'publishedAt', 'url'):
            changed = copy.deepcopy(event); changed['evidence'][0][key] += ' changed'
            result = self.select([changed], {'items': [item]})['items']
            if result:
                self.assertEqual(result[0]['copyKind'], 'source'); self.assertNotIn('art', result[0])

    def test_invalid_review_clock_and_missing_hash_fail_closed(self):
        event = self.event()
        for changes in [{'reviewedAt': '2026-10-02T15:00:00Z'}, {'expiresAt': '2026-10-02T13:59:00Z'},
                        {'expiresAt': '2026-10-03T13:30:00Z'}, {'evidenceHash': 'different'}, {'sourceId': 'other'}, {'eventId': 'other'}]:
            result = self.select([event], {'items': [self.authored(event, **changes)]})['items'][0]
            self.assertEqual(result['copyKind'], 'source')

    def test_only_allowed_local_original_art_path_is_returned(self):
        event = self.event()
        for path in ['https://thirdparty.example/photo.jpg', 'http://[', '/assets/top-stories/../other.jpg', '/assets/top-stories/photo.svg', '/assets/top-stories/photo.png?remote=1']:
            item = self.authored(event, art={'url': path, 'kind': 'illustration', 'alt': 'A conceptual illustration'})
            self.assertNotIn('art', self.select([event], {'items': [item]})['items'][0])

    def test_malformed_optional_editorial_records_do_not_break_source_fallback(self):
        event = self.event()
        for record in [None, [], {'items': None}, {'items': [None]}, {'items': [self.authored(event, supportingEvidence=None, verifiedPeg='bad', art=[])]}]:
            self.assertEqual(len(self.select([event], record)['items']), 1)

    def test_reviewed_weekly_benchmark_can_continue_without_claiming_new_publication(self):
        event = self.event('mortgage', 'Average long-term U.S. mortgage hits highest level in nearly three years',
                           'Freddie Mac reports the average 30-year mortgage rate is 7.28%.', publishedAt='2026-10-01T17:00:00Z')
        event['assignment'].update(lane='watch'); event['assignment']['todayPeg'].update(status='needs-verification', kind='unestablished')
        item = self.authored(event, headline='Mortgage rates climb to 7.28%', carryForward=True,
                             verifiedPeg={'kind': 'continuing-impact', 'at': '2026-10-01T17:00:00Z', 'reason': 'Thursday’s weekly benchmark is the latest available national borrowing-cost measure.'})
        result = self.select([event], {'items': [item]})['items'][0]
        self.assertEqual(result['publishedAt'], '2026-10-01T17:00:00Z')
        self.assertEqual(result['verifiedPeg']['kind'], 'continuing-impact')
        self.assertEqual(event['assignment']['lane'], 'watch')
        for changes in [{'supportingEvidence': []}, {'carryForward': False}, {'expiresAt': '2026-10-02T13:59:00Z'}]:
            self.assertEqual(self.select([event], {'items': [{**item, **changes}]})['items'], [])
        event['assignment']['lane'] = 'held'
        self.assertEqual(self.select([event], {'items': [item]})['items'], [])

    def test_review_cannot_override_forecast_conflict_or_source_failure(self):
        event = self.event(); event['assignment']['todayPeg']['kind'] = 'evidence-check'
        item = self.authored(event, carryForward=True)
        self.assertEqual(self.select([event], {'items': [item]})['items'], [])
        event['assignment']['todayPeg']['kind'] = 'reported-development'; event['evidence'][0]['available'] = False
        self.assertEqual(self.select([event], {'items': [item]})['items'], [])

    def test_primary_confirmation_can_elevate_a_planned_action_without_rewriting_source(self):
        event = self.event('g7', 'G7 nations to release diesel stocks', 'Europe is preparing crisis talks about rising fuel costs.')
        self.assertEqual(self.select([event])['items'], [])
        item = self.authored(event, headline='G7 agrees to a fuel reserve release', editorialPriority=2)
        result = self.select([event], {'items': [item]})['items'][0]
        self.assertEqual(result['headline'], item['headline']); self.assertEqual(result['editorialPriority'], 2)
        self.assertEqual(event['evidence'][0]['title'], 'G7 nations to release diesel stocks')

    def test_primary_confirmed_watch_report_can_pass_unconfirmed_heuristic_but_not_conflicts(self):
        event = self.event('g7', 'G7 nations to release diesel stocks', 'Europe is preparing crisis talks about rising fuel costs.')
        event['assignment']['lane'] = 'watch'
        event['assignment']['todayPeg'].update(status='needs-verification', kind='unestablished')
        item = self.authored(event, headline='G7 agrees to a fuel reserve release')
        self.assertEqual(self.select([event])['items'], [])
        self.assertEqual(self.select([event], {'items': [item]})['items'][0]['headline'], item['headline'])
        self.assertEqual(event['assignment']['todayPeg']['status'], 'needs-verification')
        for changes in [{'supportingEvidence': []}, {'evidenceHash': 'changed'}, {'expiresAt': '2026-10-02T13:59:00Z'}]:
            self.assertEqual(self.select([event], {'items': [{**item, **changes}]})['items'], [])
        for kind in ['evidence-check', 'source-updated', 'public-inspection', 'missing-changed-evidence']:
            changed = copy.deepcopy(event); changed['assignment']['todayPeg']['kind'] = kind
            self.assertEqual(self.select([changed], {'items': [item]})['items'], [])
        for modifications in [{'available': False}, {'sourceLastSuccess': '2026-10-02T10:00:00Z'}]:
            changed = copy.deepcopy(event); changed['evidence'][0].update(modifications)
            self.assertEqual(self.select([changed], {'items': [item]})['items'], [])
        event['assignment']['lane'] = 'held'
        self.assertEqual(self.select([event], {'items': [item]})['items'], [])

    def test_primary_check_clock_stays_distinct_from_source_publication(self):
        event = self.event('g7', 'G7 nations to release diesel stocks', 'Europe is preparing crisis talks about rising fuel costs.')
        item = self.authored(event, verifiedPeg={'kind': 'confirmed-development', 'clockKind': 'observed',
            'at': '2026-10-02T13:20:00Z', 'reason': 'Checked the dated primary statement; no exact release time is asserted.'})
        result = self.select([event], {'items': [item]})['items'][0]
        self.assertEqual(result['verifiedPeg']['clockKind'], 'observed')
        self.assertEqual(result['publishedAt'], '2026-10-02T12:30:00Z')
        for checked_at in ['2026-10-02T13:40:00Z', '2026-10-02T11:00:00Z', None]:
            bad = copy.deepcopy(item); bad['supportingEvidence'][0]['checkedAt'] = checked_at
            self.assertEqual(self.select([event], {'items': [bad]})['items'], [])

    def test_reviewed_order_cannot_displace_a_more_consequential_national_emergency(self):
        jobs = self.event(); item = self.authored(jobs, editorialPriority=1)
        emergency = self.event('safety', 'Nationwide power outage declared an emergency', 'Millions of U.S. households face a nationwide power outage.')
        self.assertEqual(self.select([jobs, emergency], {'items': [item]})['items'][0]['eventId'], 'safety')

    def test_shortlist_is_pure_and_does_not_approve_or_mutate_production(self):
        snapshot = self.snapshot([self.event()]); original = copy.deepcopy(snapshot)
        result = top_stories.select(snapshot, now=self.now)
        self.assertEqual(snapshot, original); self.assertIn('does not confer production approval', result['disclosure'])


if __name__ == '__main__':
    unittest.main()
