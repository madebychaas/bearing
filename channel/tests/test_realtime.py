import copy, json, sys, tempfile, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import pipeline

class RealtimeTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,9,28,23,0,tzinfo=timezone.utc)
        self.feed=pipeline.FEEDS[0]
        self.entry={'title':'An observation with an exact publication time','link':'https://www.nasa.gov/test-realtime','published':'Mon, 28 Sep 2026 14:35:42 -0400','description':'Researchers describe a complete report about the project and the observations that informed it, with findings available at the original publisher for further reading.'}
    def test_original_publication_time_is_preserved_in_utc(self):
        item=pipeline.candidate(self.entry,self.feed,self.now)
        self.assertEqual(item['publishedTime'],'2026-09-28T18:35:42+00:00')
        self.assertNotEqual(item['publishedTime'],item['retrievedAt'])
    def test_publisher_ttl_can_slow_but_not_accelerate_polling(self):
        self.assertEqual(pipeline.feed_interval(b'<rss><channel><ttl>15</ttl></channel></rss>',5),15)
        self.assertEqual(pipeline.feed_interval(b'<rss><channel><ttl>1</ttl></channel></rss>',5),5)
        self.assertEqual(pipeline.feed_interval(b'<rss><channel><ttl>bad</ttl></channel></rss>',5),5)
    def test_date_only_or_unknown_timezone_cannot_claim_an_exact_minute(self):
        for value in ('2026-09-28','2026-09-28T14:30:00'):
            item=pipeline.candidate({**self.entry,'published':value},self.feed,self.now)
            self.assertIsNone(item['publishedTime']);self.assertEqual(item['publishedAt'],'2026-09-28')
    def test_a_recheck_does_not_make_reports_new(self):
        item=pipeline.candidate(self.entry,self.feed,self.now);source={'id':self.feed['id'],'status':'ok','lastSuccess':self.now.isoformat()}
        with tempfile.TemporaryDirectory() as temp,patch.object(pipeline,'DIST',Path(temp)):
            path=pipeline.DIST/'reporting.json';pipeline.write_reporting([item],[source],self.now.isoformat());first=json.loads(path.read_text())
            pipeline.write_reporting([item],[source],(self.now+timedelta(minutes=1)).isoformat());second=json.loads(path.read_text())
            self.assertEqual(first['version'],second['version']);self.assertEqual(first['items'],second['items'])
    def test_source_revision_is_recorded_without_resetting_publication_time(self):
        item=pipeline.candidate(self.entry,self.feed,self.now);source={'id':self.feed['id'],'status':'ok','lastSuccess':self.now.isoformat()}
        with tempfile.TemporaryDirectory() as temp,patch.object(pipeline,'DIST',Path(temp)):
            path=pipeline.DIST/'reporting.json';pipeline.write_reporting([item],[source],self.now.isoformat());first=json.loads(path.read_text())
            revised=pipeline.candidate({**self.entry,'title':'An observation with a corrected source headline'},self.feed,self.now)
            changed=(self.now+timedelta(minutes=1)).isoformat();pipeline.write_reporting([revised],[source],changed);second=json.loads(path.read_text())
            self.assertNotEqual(first['version'],second['version']);self.assertEqual(second['items'][0]['lastChangedAt'],changed)
            for field in ('publishedTime','firstSeenAt'):self.assertEqual(first['items'][0][field],second['items'][0][field])
    def test_partial_outage_retains_original_link_time_and_flags_source(self):
        feeds=pipeline.FEEDS[:2];now=datetime.now(timezone.utc);entry={**self.entry,'published':(now-timedelta(hours=2)).isoformat()}
        rss=b'<rss><channel><item><title>A complete NOAA source headline</title><link>https://www.noaa.gov/test</link><pubDate>Mon, 28 Sep 2026 12:00:00 GMT</pubDate><description>A complete description.</description></item></channel></rss>'
        def fetch(url,headers):
            if url==feeds[0]['url']:raise OSError('Simulated outage')
            return {'status':200,'body':rss}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dist=root/'dist';dist.mkdir();work=root/'production'
            pipeline.write_json(work/'runs'/'feed-cache.json',{feeds[0]['id']:{'url':feeds[0]['url'],'entries':[entry],'lastSuccess':(now-timedelta(minutes=20)).isoformat(),'nextCheckAt':(now-timedelta(minutes=1)).isoformat()}})
            with patch.object(pipeline,'DIST',dist),patch.object(pipeline,'WORK',work),patch.object(pipeline,'FEEDS',feeds),patch.object(pipeline,'fetch',side_effect=fetch):
                pipeline.collect();report=json.loads((dist/'reporting.json').read_text())
                retained=next(item for item in report['items'] if item['sourceId']==feeds[0]['id'])
                self.assertFalse(retained['sourceAvailable']);self.assertEqual(retained['publishedTime'],entry['published'])

if __name__=='__main__':unittest.main()
