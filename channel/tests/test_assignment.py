import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import assignment
import primary_feeds
import producer


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,10,2,14,tzinfo=timezone.utc)
        self.feed={'id':'test','name':'Independent','enabled':True,'deskRole':'publisher','domestic':True,'pollMinutes':5}

    def event(self,title='U.S. payrolls rise in a new jobs report',**extra):
        report={'id':'report','title':title,'excerpt':'The release reports a new change in payrolls across the United States. Verify its impact and underlying evidence.',
                'publishedAt':'2026-10-02T12:30:00Z','sourceLastSuccess':'2026-10-02T13:58:00Z','available':True,'sourceId':'test','url':'https://example.org/story','level':'excerpt','publisher':'Independent'}
        report.update(extra)
        return {'id':'event','title':title,'evidence':[report],'change':{}}

    def assess(self,event,feed=None):
        return assignment.assess(event,{'test':feed or self.feed},self.now)

    def test_concrete_today_development_remains_candidate_with_source_and_question(self):
        value=self.assess(self.event())
        self.assertEqual(value['lane'],'today');self.assertEqual(value['scope'],'national')
        self.assertEqual(value['todayPeg']['status'],'candidate')
        self.assertEqual(value['todayPeg']['sourceId'],'report');self.assertTrue(value['questions'])

    def test_publication_alone_does_not_make_an_evergreen_current(self):
        for title in ['How to manage U.S. student loans','What NASA taught us in 2024','Federal benefits anniversary explained','Ready to Blow His Stack: How Biden Nearly Cut Off Netanyahu Over Gaza']:
            self.assertNotEqual(self.assess(self.event(title))['lane'],'today')
        value=self.assess(self.event('U.S. inflation falls Wednesday'))
        self.assertEqual(value['lane'],'watch')

    def test_future_missing_old_or_updated_only_clock_is_not_new_news(self):
        for date in [None,'2026-10-02','2026-10-03T12:00:00Z','2026-09-29T12:00:00Z']:
            self.assertNotEqual(self.assess(self.event(publishedAt=date))['lane'],'today')
        value=self.assess(self.event(sourceTimeKind='updated'))
        self.assertEqual(value['lane'],'watch');self.assertEqual(value['todayPeg']['kind'],'source-updated')

    def test_first_discovery_does_not_create_material_update(self):
        value=self.event();value['change']={'kind':'new','material':False,'at':'2026-10-02T13:55:00Z'}
        self.assertEqual(self.assess(value)['lane'],'today')
        value['evidence'][0]['publishedAt']='2026-09-20T12:00:00Z'
        self.assertEqual(self.assess(value)['lane'],'held')

    def test_real_observed_change_has_its_own_clock_and_caveat(self):
        value=self.event(publishedAt='2026-10-01T12:00:00Z')
        value['change']={'material':True,'at':'2026-10-02T13:55:00Z','evidenceIds':['report']}
        result=self.assess(value)
        self.assertEqual(result['lane'],'developing');self.assertIn('not event time',result['todayPeg']['reason'])

    def test_material_peg_cites_changed_source_not_newer_unchanged_reporting(self):
        value=self.event(publishedAt='2026-10-01T12:00:00Z')
        changed=value['evidence'][0]
        value['evidence'].append({**changed,'id':'newer','publishedAt':'2026-10-02T13:00:00Z','excerpt':'Unchanged background reporting.'})
        value['change']={'material':True,'at':'2026-10-02T13:55:00Z','evidenceIds':['report']}
        result=self.assess(value)
        self.assertEqual(result['lane'],'developing');self.assertEqual(result['todayPeg']['sourceId'],'report')
        self.assertEqual(result['todayPeg']['quote'],changed['excerpt'])
        changed['available']=False
        self.assertEqual(self.assess(value)['lane'],'held')
        value['change']['evidenceIds']=['missing']
        result=self.assess(value)
        self.assertEqual(result['lane'],'held');self.assertIsNone(result['todayPeg']['sourceId'])

    def test_national_publisher_does_not_make_a_local_or_foreign_story_national(self):
        for title in ['Dallas city council approves park','France opens a town library','What paintings teach us about life']:
            value=self.assess(self.event(title,excerpt='A story about the named place and people.'))
            self.assertEqual(value['lane'],'held')
        self.assertEqual(self.assess(self.event('China cuts global oil supplies',excerpt='Oil shipping and supply chains are affected.'))['scope'],'world-impact')

    def test_political_sparring_and_reaction_remain_held(self):
        self.assertEqual(self.assess(self.event('Trump slams rival over federal taxes'))['lane'],'held')

    def test_unavailable_stale_and_mismatched_evidence_cannot_lead(self):
        for changes in [{'available':False},{'revisionMismatch':True},{'sourceLastSuccess':'2026-10-01T12:00:00Z'}]:
            self.assertEqual(self.assess(self.event(**changes))['lane'],'held')

    def test_proposals_and_future_releases_are_watch_items(self):
        value=self.assess(self.event('Federal Reserve will release its decision today'))
        self.assertEqual(value['lane'],'watch');self.assertIn('accomplished fact',value['todayPeg']['reason'])

    def test_filings_are_not_final_rules_or_planned_publication(self):
        feed={**self.feed,'deskRole':'primary','deskScope':'national'}
        value=self.assess(self.event('Federal eligibility standards',sourceTimeKind='filed'),feed)
        self.assertEqual(value['lane'],'watch');self.assertEqual(value['todayPeg']['kind'],'public-inspection')
        self.assertIn('legal effect',value['todayPeg']['reason'])

    def test_local_weather_does_not_flood_national_desk(self):
        value=self.assess(self.event('National Weather Service issues a warning',alert={'severity':'Severe','event':'Red Flag Warning'}))
        self.assertEqual(value['scope'],'local');self.assertEqual(value['lane'],'held')

    def test_today_uses_central_calendar_day_at_utc_midnight(self):
        self.now=datetime(2026,10,3,1,tzinfo=timezone.utc)
        value=self.event(publishedAt='2026-10-02T23:00:00Z',sourceLastSuccess='2026-10-03T00:59:00Z')
        self.assertEqual(self.assess(value)['todayPeg']['label'],'Reported today')

    def test_beats_match_words_not_ai_in_raised_or_flu_in_fluids(self):
        self.assertEqual(assignment.beat_for('Money raised for aid and mountain fluids')[0],'general')
        self.assertEqual(assignment.beat_for('New AI research at NASA')[0],'technology')

    def test_nhc_dateline_and_routine_bulletin_are_not_us_impact(self):
        feed={**self.feed,'id':'nhc-pacific','deskRole':'primary'}
        value=self.assess(self.event('Hurricane Rachel Forecast Discussion',excerpt='NWS National Hurricane Center Miami FL. Winds west of Mexico.'),feed)
        self.assertEqual(value['lane'],'held')
        value=self.assess(self.event('Hurricane warning issued',excerpt='Storm surge warning in effect for Florida before landfall.'),feed)
        self.assertEqual(value['scope'],'national')

    def test_forecast_excerpt_does_not_establish_released_figures(self):
        value=self.assess(self.event('U.S. payrolls rise by 29,000',excerpt='Nonfarm payrolls were expected to increase by 84,000.'))
        self.assertEqual(value['lane'],'watch');self.assertEqual(value['todayPeg']['kind'],'evidence-check')

    def test_expired_or_future_alert_is_not_a_current_lead(self):
        for times in [{'expires':'2026-10-02T12:00:00Z'},{'effective':'2026-10-03T12:00:00Z'}]:
            value=self.assess(self.event('National Hurricane warning issued',alert={'severity':'Extreme','event':'Hurricane Warning',**times}))
            self.assertEqual(value['lane'],'held')

    def test_specialized_agency_content_is_not_automatically_new_national_news(self):
        feed={**self.feed,'deskRole':'primary','deskScope':'specialized'}
        for title in ['NASA movie night','NASA research archive','10 Things from NASA']:
            self.assertNotEqual(self.assess(self.event(title),feed)['lane'],'today')

    def test_snapshot_keeps_held_evidence_and_excludes_bootstrap_lag(self):
        one=self.event(discoveryKind='baseline',publicationLagSeconds=99999)
        two=self.event(discoveryKind='arrival',publicationLagSeconds=120);two['id']='two'
        snap={'events':[one,two],'sourceHealth':{'total':1,'healthy':1,'checkedAt':'2026-10-02T13:58:00Z'}}
        before=copy.deepcopy(snap)
        result=assignment.enrich(snap,{'sources':[self.feed]},self.now)
        self.assertEqual(before,snap);self.assertEqual(result['assignment']['health']['latencySamples'],1)
        self.assertEqual(result['assignment']['health']['medianDiscoveryMinutes'],2)
        self.assertTrue(any(row['gap'] for row in result['assignment']['coverage']))

    def test_atomic_bundle_prevents_half_updated_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'production/runs').mkdir(parents=True)
            bundle={'schema':1,'reporting':{'items':[{'id':'coherent'}]},'candidates':{'items':[]},'sourceHealth':{}}
            path=root/'production/runs/intake-snapshot.json';path.write_text(json.dumps(bundle))
            store=producer.ProducerStore(root,now=lambda:self.now)
            inputs=store._inputs('live',{})
            self.assertEqual(inputs[0]['items'][0]['id'],'coherent')
            path.write_text('{')
            with self.assertRaises(RuntimeError):store._inputs('live',{})

    def test_primary_adapter_uses_filed_clock_and_does_not_invent_excerpt(self):
        row={'title':'New federal standard','html_url':'https://www.federalregister.gov/public-inspection/2026-1/example',
             'filed_at':'2026-10-02T08:45:00-04:00','publication_date':'2026-10-05','type':'Proposed Rule','agencies':[{'name':'Agency'}]}
        values=primary_feeds.parse_inspection(json.dumps({'results':[row,{**row,'html_url':'https://evil.example/doc'}]}).encode())
        self.assertEqual(len(values),1);self.assertEqual(values[0]['published'],row['filed_at'])
        self.assertEqual(values[0]['description'],'');self.assertEqual(values[0]['filing']['publicationDate'],'2026-10-05')
        self.assertEqual(values[0]['timestampKind'],'filed')
        with self.assertRaises(ValueError):primary_feeds.parse_inspection(b'{}')


if __name__=='__main__':unittest.main()
