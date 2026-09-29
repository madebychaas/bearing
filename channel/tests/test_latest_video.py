import copy, json, sys, tempfile, unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import latest_video as video

def item(number=1,topic='world'):
    return {'id':f'news-{number}','title':f'An attributed report about a new project {number}',
        'topic':topic,'topicLabel':video.pipeline.TOPICS[topic],
        'publishedTime':(datetime.now(timezone.utc)-timedelta(minutes=number)).isoformat(),
        'source':{'name':'NASA','url':f'https://www.nasa.gov/news-{number}'},'version':'v1'}

class LatestVideoTests(unittest.TestCase):
    def test_headline_readout_cannot_include_excerpts_or_invented_context(self):
        source=item();source['excerpt']='A detail which must not be narrated.'
        script=video.script_for(source)
        self.assertEqual(script,f"A headline from NASA. {source['title']}.")
        self.assertNotIn(source['excerpt'],script)
    def test_revised_evidence_creates_new_media_but_rechecks_do_not(self):
        source=item();key=video.media_key(source)
        self.assertEqual(key,video.media_key({**source,'checkedAt':'later','version':'excerpt-change'}))
        self.assertNotEqual(key,video.media_key({**source,'title':'A corrected report about the project'}))
        self.assertNotEqual(key,video.media_key({**source,'publishedTime':'2026-09-29T10:00:00Z'}))
    def test_only_precise_recent_allowlisted_publication_enters_production(self):
        good=item();old={**item(2),'publishedTime':(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()}
        future={**item(3),'publishedTime':(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()}
        day={**item(4),'publishedTime':'2026-09-29'}
        remote={**item(5),'source':{'name':'Bad','url':'https://example.com/news'}}
        injected={**item(6),'title':'An attributed <script>bad</script> headline'}
        self.assertEqual(video.eligible([old,future,day,remote,injected,good,good]),[good])
    def test_initial_production_covers_interests_before_second_story(self):
        stories=[item(1),item(2),item(3,'culture'),item(4,'sport'),item(5,'nature')]
        ordered=video.production_order(stories,4)
        self.assertEqual([s['topic'] for s in ordered],['world','culture','sport','nature'])
    def test_failed_revised_clip_is_withdrawn_and_previous_edition_archived(self):
        revised=item();old={**revised,'title':'Old title','mediaVersion':'old','status':'ready'}
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dist=root/'dist';work=root/'production';dist.mkdir();work.mkdir()
            video.pipeline.write_json(dist/'reporting.json',{'items':[revised]})
            video.pipeline.write_json(dist/'latest-edition.json',{'version':'old-edition','stories':[old]})
            with patch.object(video,'DIST',dist),patch.object(video,'WORK',work),patch.object(video,'verified_existing',return_value=None),patch.object(video,'build',side_effect=RuntimeError('simulated failed media')):
                result=video.produce(1)
            edition=json.loads((dist/'latest-edition.json').read_text())
            self.assertEqual(edition['stories'],[]);self.assertEqual(len(result['errors']),1)
            self.assertTrue((work/'runs'/'latest-video-editions'/'old-edition.json').exists())
    def test_typography_produces_unique_complete_frames(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            a=Path(temp)/'a.png';b=Path(temp)/'b.png'
            video.render_card(item(1),a);video.render_card(item(2,'culture'),b)
            with Image.open(a) as frame:self.assertEqual(frame.size,(1280,720))
            self.assertNotEqual(a.read_bytes(),b.read_bytes())

if __name__=='__main__':unittest.main()
