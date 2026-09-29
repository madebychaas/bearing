import asyncio, copy, json, tempfile, unittest, sys
from pathlib import Path
from unittest.mock import patch, AsyncMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import pipeline

class VisualTests(unittest.TestCase):
    def setUp(self):self.edition=json.loads((pipeline.DIST/'edition.json').read_text(encoding='utf-8'))
    def test_shared_topic_art_without_story_binding_is_rejected(self):
        story=self.edition['stories'][0];story.pop('visual',None)
        with self.assertRaisesRegex(ValueError,'bespoke'):pipeline.check_story(story,decode_media=False)
    def test_wrong_story_or_script_cannot_reuse_reviewed_visual(self):
        for field in ('storyId','scriptSha256'):
            story=copy.deepcopy(self.edition['stories'][0]);story['visual'][field]='different'
            with self.assertRaises(ValueError):pipeline.check_visual(story)
    def test_changed_image_or_video_is_rejected(self):
        for field in ('imageSha256','videoSha256'):
            story=copy.deepcopy(self.edition['stories'][0]);story['visual'][field]='invalid'
            with self.assertRaisesRegex(ValueError,'hash mismatch'):pipeline.check_visual(story)
    def test_duplicate_image_cannot_replace_live_edition(self):
        original=(pipeline.DIST/'edition.json').read_bytes();a,b=self.edition['stories'][:2]
        b['image']=a['image'];b['visual']['image']=a['image'];b['visual']['imageSha256']=a['visual']['imageSha256']
        with self.assertRaisesRegex(ValueError,'share the same illustration'):pipeline.publish(self.edition,decode_media=False)
        self.assertEqual((pipeline.DIST/'edition.json').read_bytes(),original)
    def test_new_excerpt_waits_for_art_without_speech_work_or_edition_changes(self):
        candidate=copy.deepcopy(self.edition['stories'][0]);candidate.update(id='new-story',reviewStatus='source_excerpt',publishedAt='2026-09-28',publisherGroup='NASA',source={'name':'NASA','url':'https://www.nasa.gov/new-story'})
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dist=root/'dist';dist.mkdir();edition=dist/'edition.json';edition.write_text(json.dumps(self.edition),encoding='utf-8');original=edition.read_bytes()
            with patch.object(pipeline,'DIST',dist),patch.object(pipeline,'WORK',root/'production'),patch.object(pipeline,'collect',return_value={'candidates':[candidate]}),patch.object(pipeline,'narrate',new_callable=AsyncMock) as narrate:
                asyncio.run(pipeline.automatic(4));narrate.assert_not_called();self.assertEqual(edition.read_bytes(),original)
                pending=json.loads((pipeline.WORK/'runs'/'visual-requests.json').read_text())['pending']
                self.assertEqual(pending[0]['id'],'new-story');self.assertEqual(pending[0]['scriptSha256'],pipeline.script_hash(candidate))

if __name__=='__main__':unittest.main()
