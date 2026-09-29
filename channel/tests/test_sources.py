import copy, json, tempfile, unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import pipeline

class FeedTests(unittest.TestCase):
    def test_atom_and_rdf_preserve_dates_links_and_summaries(self):
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>A dated report</title><link rel="self" href="https://api.example/a"/><link href="https://www.nasa.gov/a"/><summary>A complete summary.</summary><published>2026-09-28T12:00:00Z</published></entry></feed>'
        rdf=b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/"><item><title>A dated report</title><link>https://www.nasa.gov/a</link><description>A complete summary.</description><dc:date>2026-09-28T12:00:00Z</dc:date></item></rdf:RDF>'
        self.assertEqual(pipeline.parse_feed(atom),pipeline.parse_feed(rdf))
        self.assertEqual(pipeline.parse_feed(atom)[0]['link'],'https://www.nasa.gov/a')
    def test_html_error_page_is_not_a_healthy_empty_feed(self):
        with self.assertRaises(ValueError):pipeline.parse_feed(b'<html><body>Access denied</body></html>')
    def test_tracking_urls_deduplicate_without_removing_article_parameters(self):
        self.assertEqual(pipeline.canonical_url('https://www.nasa.gov/a?id=4&utm_source=rss&amp;fbclid=x#top'),'https://www.nasa.gov/a?id=4')
    def test_ellipsis_and_restricted_publisher_cannot_auto_narrate(self):
        entry={'title':'A long enough sample title','link':'https://www.nasa.gov/a','published':pipeline.stamp(),'description':'This complete looking feed contains enough words to pass a basic length check but ends with an unfinished excerpt about the subject...'}
        self.assertIn('incomplete_excerpt',pipeline.candidate(entry,pipeline.FEEDS[0])['holdReasons'])
        feed={**pipeline.FEEDS[0],'mode':'review'};entry['description']=entry['description'][:-3]+'.'
        self.assertIn('source_requires_review',pipeline.candidate(entry,feed)['holdReasons'])
    def test_304_reuses_content_and_sends_conditional_headers(self):
        feed=pipeline.FEEDS[0];now=datetime.now(timezone.utc)
        entry={'title':'A new NASA research report','description':'Researchers describe a complete report about the project and the observations that informed it, with findings available at the original publisher for further reading.','link':'https://www.nasa.gov/example','published':now.isoformat()}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);work=root/'production';dist=root/'dist';dist.mkdir()
            cache={feed['id']:{'url':feed['url'],'entries':[entry],'etag':'version-1','lastSuccess':now.isoformat(),'nextCheckAt':(now-timedelta(minutes=1)).isoformat()}}
            pipeline.write_json(work/'runs'/'feed-cache.json',cache)
            with patch.object(pipeline,'WORK',work),patch.object(pipeline,'DIST',dist),patch.object(pipeline,'FEEDS',[feed]),patch.object(pipeline,'fetch',return_value={'status':304}) as fetch:
                result=pipeline.collect();self.assertEqual(result['sources'][0]['status'],'unchanged');self.assertEqual(len(result['candidates']),1)
                self.assertEqual(fetch.call_args.args[1],{'If-None-Match':'version-1'})
                pipeline.collect();self.assertEqual(fetch.call_count,1)
                self.assertEqual(len(list((work/'runs').glob('*/intake.json'))),1)
    def test_partial_outage_keeps_healthy_source_and_backs_off(self):
        feeds=pipeline.FEEDS[:2];rss=b'<rss><channel><item><title>A new NASA research report</title><link>https://www.nasa.gov/a</link><pubDate>Mon, 28 Sep 2026 12:00:00 GMT</pubDate><description>A complete source excerpt.</description></item></channel></rss>'
        def fetch(url,headers):
            if url==feeds[1]['url']:raise OSError('Source offline')
            return {'status':200,'body':rss}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dist=root/'dist';dist.mkdir()
            with patch.object(pipeline,'WORK',root/'production'),patch.object(pipeline,'DIST',dist),patch.object(pipeline,'FEEDS',feeds),patch.object(pipeline,'fetch',side_effect=fetch) as call:
                result=pipeline.collect();self.assertEqual([s['status'] for s in result['sources']],['ok','unavailable'])
                pipeline.collect();self.assertEqual(call.call_count,2)
                health=json.loads((dist/'source-status.json').read_text());self.assertEqual(health['healthy'],1)
    def test_selection_prioritizes_missing_topics_and_publisher_variety(self):
        items=[{'id':str(i),'topic':topic,'publisherGroup':publisher,'reviewStatus':'source_excerpt','publishedAt':'2026-09-28','source':{'url':f'https://www.nasa.gov/{i}'}} for i,topic,publisher in [(1,'space','NASA'),(2,'space','NASA'),(3,'nature','USGS'),(4,'technology','NIST')]]
        existing=[{'topic':'space','source':{'url':'https://www.nasa.gov/old'}}]
        chosen=pipeline.balanced_choices(items,existing,3)
        self.assertEqual([s['topic'] for s in chosen],['nature','technology','space'])
    def test_evicted_stories_are_not_produced_again(self):
        item={'id':'old','topic':'nature','publisherGroup':'USGS','reviewStatus':'source_excerpt','publishedAt':'2026-09-28','source':{'url':'https://www.usgs.gov/old'}}
        self.assertEqual(pipeline.balanced_choices([item],[],3,{'https://www.usgs.gov/old':None}),[])
    def test_changed_source_withdraws_only_matching_automatic_story(self):
        stories=[{'id':'a','source':{'url':'https://www.nasa.gov/a'},'contentHash':'old'},{'id':'b','source':{'url':'https://www.nasa.gov/b'},'contentHash':'same'}]
        candidates=[{'source':{'url':'https://www.nasa.gov/a'},'contentHash':'new'},{'source':{'url':'https://www.nasa.gov/b'},'contentHash':'same'}]
        self.assertEqual(pipeline.withdraw_changed(stories,candidates),['a']);self.assertIn('withdrawnAt',stories[0]);self.assertNotIn('withdrawnAt',stories[1])
        self.assertEqual(pipeline.withdraw_changed(stories,candidates),[])
    def test_old_backfill_cannot_evict_newer_reports_or_other_topics(self):
        stories=[{'id':str(day),'topic':'nature','publishedAt':f'2026-09-{day}'} for day in range(25,29)]
        stories+=[{'id':'culture','topic':'culture','eventDate':'2026-09-26'},{'id':'backfill','topic':'nature','publishedAt':'2026-09-23'}]
        retained=pipeline.retain_rotation(stories)
        self.assertEqual(len(retained),5);self.assertNotIn('backfill',[s['id'] for s in retained]);self.assertIn('culture',[s['id'] for s in retained]);self.assertEqual(retained[0]['id'],'28')

if __name__=='__main__':unittest.main()
