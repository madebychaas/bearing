"""Independent gathering, honest clocks and coherent source snapshots."""
import asyncio
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import pipeline
import server


class IntakeSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.work=self.root/'production';self.dist=self.root/'dist'
        self.work.mkdir();self.dist.mkdir()
        self.feed={**pipeline.FEEDS[0],'pollMinutes':2}
        self.now=datetime.now(timezone.utc)
        self.xml=('<rss><channel><item><title>A new NASA research report</title><link>https://www.nasa.gov/example</link><pubDate>'+self.now.isoformat()+'</pubDate><description>Researchers describe a complete report about the project and the observations that informed it, with findings available at the original publisher for further reading.</description></item></channel></rss>').encode()
        for field,value in [('WORK',self.work),('DIST',self.dist),('FEEDS',[self.feed])]:
            mocked=patch.object(pipeline,field,value);mocked.start();self.addCleanup(mocked.stop)

    def collect(self,**response):
        with patch.object(pipeline,'fetch',return_value={'status':200,'body':self.xml,**response}):return pipeline.collect()

    def test_intake_runs_while_production_is_locked_but_another_intake_cannot(self):
        with pipeline.production_lock():result=self.collect()
        self.assertEqual(result['sources'][0]['status'],'ok')
        before=(self.work/'runs'/'intake-snapshot.json').read_bytes()
        with pipeline.intake_lock(),self.assertRaisesRegex(RuntimeError,'intake check'):
            self.collect()
        self.assertEqual(before,(self.work/'runs'/'intake-snapshot.json').read_bytes())

    def test_bundle_joins_exact_reporting_and_candidate_revision(self):
        self.collect()
        bundle=json.loads((self.work/'runs'/'intake-snapshot.json').read_text())
        candidate=bundle['candidates']['candidates'][0];report=bundle['reporting']['items'][0]
        self.assertEqual(candidate['contentHash'],report['version'])
        self.assertEqual(candidate['firstSeenAt'],report['firstSeenAt'])
        self.assertEqual(bundle['checkedAt'],bundle['sourceHealth']['checkedAt'])
        self.assertEqual(bundle['sourceHealth']['discoveryLatency']['sampleCount'],0)
        self.assertEqual(candidate['discoveryKind'],'baseline')
        self.assertIsNone(candidate['publicationLagSeconds'])

    def test_failed_publication_never_replaces_coherent_snapshot(self):
        self.collect();before=(self.work/'runs'/'intake-snapshot.json').read_bytes()
        with patch.object(pipeline,'write_reporting',side_effect=OSError('Interrupted legacy output')):
            with self.assertRaises(OSError):self.collect()
        self.assertEqual(before,(self.work/'runs'/'intake-snapshot.json').read_bytes())

    def test_http_cache_and_rss_ttl_prevent_early_requests(self):
        self.xml=self.xml.replace(b'<channel>',b'<channel><ttl>5</ttl>')
        self.collect(cacheControl='public, max-age=600')
        with patch.object(pipeline,'fetch',side_effect=AssertionError('Polling before due')):
            result=pipeline.collect()
        self.assertEqual(result['sources'][0]['effectivePollMinutes'],10)
        self.assertEqual(result['sources'][0]['status'],'cached')
        self.assertFalse(result['sources'][0]['attempted'])
        self.assertIsNotNone(result['sources'][0]['lastAttemptAt'])
        self.assertIsNotNone(result['sources'][0]['lastDurationMs'])

    def test_empty_official_feed_and_304_remain_healthy(self):
        self.xml=b'<feed xmlns="http://www.w3.org/2005/Atom"><title>No active significant events</title></feed>'
        result=self.collect();self.assertEqual(result['candidates'],[])
        self.assertEqual(result['sources'][0]['status'],'ok')
        with patch.object(pipeline,'fetch',return_value={'status':304}):result=pipeline.collect(force=True)
        self.assertEqual(result['sources'][0]['status'],'unchanged')
        self.assertEqual(result['sources'][0]['entryCount'],0)

    def test_outage_publishes_honest_health_without_losing_retained_evidence(self):
        self.collect()
        with patch.object(pipeline,'fetch',side_effect=OSError('Offline')):
            with self.assertRaisesRegex(RuntimeError,'All approved sources'):pipeline.collect(force=True)
        bundle=json.loads((self.work/'runs'/'intake-snapshot.json').read_text())
        self.assertEqual(bundle['sourceHealth']['healthy'],0)
        self.assertFalse(bundle['reporting']['items'][0]['sourceAvailable'])
        self.assertEqual(bundle['sourceHealth']['sources'][0]['reason'],'Offline')

    def test_arrival_clocks_survive_rotation_and_revision_has_own_clock(self):
        self.collect()
        first=datetime.now(timezone.utc).isoformat()
        item=pipeline.candidate({'title':'Another newly reported NASA research project','link':'https://www.nasa.gov/new','published':(self.now-timedelta(minutes=3)).isoformat(),'description':'A detailed report.'},self.feed)
        result={'retrievedAt':first,'sources':[{'id':self.feed['id'],'attempted':True,'status':'ok','lastSuccess':first,'previousSuccess':(self.now-timedelta(minutes=4)).isoformat(),'discoveryBaselineAt':(self.now-timedelta(hours=1)).isoformat(),'initialDiscovery':False}],'candidates':[item]}
        pipeline.record_discovery(result)
        self.assertEqual(item['discoveryKind'],'arrival');self.assertGreater(item['publicationLagSeconds'],170)
        pipeline.record_discovery({**result,'candidates':[]})
        later=(self.now+timedelta(minutes=5)).isoformat();changed={**item,'contentHash':'new revision'}
        pipeline.record_discovery({'retrievedAt':later,'sources':[{**result['sources'][0],'lastSuccess':later}],'candidates':[changed]})
        self.assertEqual(changed['firstSeenAt'],first);self.assertEqual(changed['firstRevisionSeenAt'],later)

    def test_legacy_feed_cache_first_check_is_a_baseline_even_if_it_has_last_success(self):
        entries=pipeline.parse_feed(self.xml)
        cache={self.feed['id']:{'url':self.feed['url'],'entries':entries,'lastSuccess':(self.now-timedelta(minutes=5)).isoformat(),'nextCheckAt':(self.now-timedelta(minutes=1)).isoformat()}}
        pipeline.write_json(self.work/'runs'/'feed-cache.json',cache)
        result=self.collect();item=result['candidates'][0]
        self.assertTrue(result['sources'][0]['initialDiscovery'])
        self.assertEqual(item['discoveryKind'],'baseline');self.assertIsNone(item['publicationLagSeconds'])
        migrated=json.loads((self.work/'runs'/'feed-cache.json').read_text())
        self.assertEqual(migrated[self.feed['id']]['discoveryVersion'],pipeline.DISCOVERY_VERSION)
        self.assertIsNotNone(migrated[self.feed['id']]['discoveryBaselineAt'])

    def test_unversioned_arrival_measurements_migrate_without_rewriting_discovery_clock(self):
        item=pipeline.candidate(pipeline.parse_feed(self.xml)[0],self.feed)
        first=(self.now-timedelta(days=1)).isoformat()
        pipeline.write_json(self.work/'runs'/'report-discovery.json',{item['id']:{'firstSeenAt':first,'firstRevisionSeenAt':first,'contentHash':item['contentHash'],'discoveryKind':'arrival'}})
        result=self.collect();migrated=result['candidates'][0]
        self.assertEqual(migrated['firstSeenAt'],first)
        self.assertEqual(migrated['discoveryKind'],'baseline');self.assertIsNone(migrated['publicationLagSeconds'])

    def test_expanded_feed_old_links_are_backfill_not_arrival_samples(self):
        first=self.collect()['sources'][0]['discoveryBaselineAt']
        self.xml=self.xml.replace(b'/example',b'/older-backfill').replace(self.now.isoformat().encode(),(self.now-timedelta(days=3)).isoformat().encode())
        with patch.object(pipeline,'fetch',return_value={'status':200,'body':self.xml}):result=pipeline.collect(force=True)
        item=result['candidates'][0]
        self.assertFalse(result['sources'][0]['initialDiscovery'])
        self.assertEqual(result['sources'][0]['discoveryBaselineAt'],first)
        self.assertEqual(item['discoveryKind'],'backfill');self.assertIsNone(item['publicationLagSeconds'])

    def test_delayed_indexing_after_fixed_baseline_counts_even_before_previous_poll(self):
        baseline=(self.now-timedelta(hours=3)).isoformat()
        prior=(self.now-timedelta(minutes=5)).isoformat()
        publication=(self.now-timedelta(hours=2)).isoformat()
        cache={self.feed['id']:{'url':self.feed['url'],'entries':[],'lastSuccess':prior,'nextCheckAt':prior,'discoveryVersion':pipeline.DISCOVERY_VERSION,'discoveryBaselineAt':baseline}}
        pipeline.write_json(self.work/'runs'/'feed-cache.json',cache)
        self.xml=self.xml.replace(self.now.isoformat().encode(),publication.encode())
        result=self.collect();item=result['candidates'][0]
        self.assertEqual(result['sources'][0]['discoveryBaselineAt'],baseline)
        self.assertEqual(item['discoveryKind'],'arrival')
        self.assertGreaterEqual(item['publicationLagSeconds'],7200)

    def test_existing_url_revision_does_not_create_or_recalculate_discovery_latency(self):
        first=self.now.isoformat();prior=(self.now-timedelta(minutes=2)).isoformat()
        item=pipeline.candidate({'title':'A new NASA research report','link':'https://www.nasa.gov/update','published':(self.now-timedelta(minutes=1)).isoformat(),'description':'A detailed report.'},self.feed)
        source={'id':self.feed['id'],'attempted':True,'status':'ok','lastSuccess':first,'previousSuccess':prior,'discoveryBaselineAt':(self.now-timedelta(hours=1)).isoformat(),'initialDiscovery':False}
        pipeline.record_discovery({'retrievedAt':first,'sources':[source],'candidates':[item]})
        self.assertEqual(item['publicationLagSeconds'],60)
        later=(self.now+timedelta(minutes=5)).isoformat()
        revision={**item,'contentHash':'corrected description','publishedTime':(self.now-timedelta(days=100)).isoformat()}
        pipeline.record_discovery({'retrievedAt':later,'sources':[{**source,'lastSuccess':later}],'candidates':[revision]})
        self.assertEqual(revision['firstSeenAt'],first)
        self.assertEqual(revision['firstRevisionSeenAt'],later)
        self.assertEqual(revision['publicationLagSeconds'],60)

    def test_update_only_timestamp_is_not_independently_published(self):
        entry=pipeline.parse_feed(b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Weather alert with an updated timestamp</title><updated>2026-10-02T10:00:00Z</updated><link href="https://www.nasa.gov/test"/></entry></feed>')[0]
        item=pipeline.candidate(entry,self.feed)
        self.assertEqual(item['sourceTimeKind'],'updated')
        self.assertIn('updated_timestamp_only',item['holdReasons'])
        self.assertEqual(item['sourceUpdatedAt'],'2026-10-02T10:00:00+00:00')
        date_only=pipeline.candidate({**entry,'published':'2026-10-02','timestampKind':'published'},self.feed)
        self.assertEqual(date_only['publishedAt'],'2026-10-02');self.assertIsNone(date_only['publishedTime'])

    def test_alert_fields_are_preserved_as_bounded_source_data(self):
        entry=pipeline.parse_feed(b'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:cap="urn:oasis:names:tc:emergency:cap:1.2"><entry><title>Severe weather alert</title><updated>2026-10-02T10:00:00Z</updated><cap:event>Tornado Warning</cap:event><cap:severity>Extreme</cap:severity><cap:areaDesc>Multiple counties</cap:areaDesc><cap:expires>2026-10-02T11:00:00Z</cap:expires></entry></feed>')[0]
        self.assertEqual(entry['alert']['severity'],'Extreme')
        self.assertEqual(entry['alert']['areaDesc'],'Multiple counties')
        self.assertEqual(pipeline.candidate(entry,self.feed)['alert'],entry['alert'])

    def test_media_skip_collect_reads_completed_intake_without_network(self):
        self.collect();pipeline.write_json(self.dist/'edition.json',{'stories':[]})
        with patch.object(pipeline,'collect',side_effect=AssertionError('Media invoked intake')),patch.object(pipeline,'balanced_choices',return_value=[]),patch.object(pipeline,'visual_registry',return_value={}):
            asyncio.run(pipeline.automatic(2,skip_collect=True))

    def test_server_intake_uses_only_collect_command_and_separate_health(self):
        self.collect()
        run=SimpleNamespace(returncode=0,stdout='',stderr='')
        calendar=SimpleNamespace(refresh=lambda root:{'status':'current'})
        with patch.object(server,'ROOT',self.root),patch.object(server.subprocess,'run',return_value=run) as execute,patch.object(server,'status',{'state':'rendering'}),patch.dict(sys.modules,{'release_calendar':calendar}):
            result=server.intake_once()
            self.assertEqual(server.status['state'],'rendering')
            self.assertEqual(server.status['intake'],result)
        self.assertEqual(execute.call_count,1)
        self.assertEqual(execute.call_args.args[0][-1],'collect')
        self.assertNotIn('auto',execute.call_args.args[0])

    def test_scheduler_waits_remaining_cadence_not_media_time(self):
        event=SimpleNamespace(is_set=lambda:False,wait=lambda seconds: self.assertEqual(seconds,23) or True)
        with patch.object(server,'stop',event),patch.object(server,'intake_once') as collect,patch.object(server.time,'monotonic',side_effect=[100,107]):
            server.refresh_intake(30)
        collect.assert_called_once()


if __name__=='__main__':unittest.main()
