import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import produce_programmes as producer

class ProgrammeTests(unittest.TestCase):
    def setUp(self):
        self.story=producer.read(producer.DIST/'edition.json',{})['stories'][0]
        self.plan=producer.read(producer.WORK/'programme-plans.json',{})['stories'][self.story['id']]
    def test_source_revision_prevents_stale_editorial_presentation(self):
        producer.validate_plan(self.story,self.plan)
        changed={**self.story,'script':self.story['script']+' A correction.'}
        with self.assertRaisesRegex(ValueError,'Source script changed'):producer.validate_plan(changed,self.plan)
    def test_incomplete_closing_card_is_held(self):
        with self.assertRaisesRegex(ValueError,'lookAhead'):producer.validate_plan(self.story,{**self.plan,'lookAhead':''})
    def test_cross_story_visual_is_held(self):
        story=copy.deepcopy(self.story);story['visual']['storyId']='unrelated'
        with self.assertRaisesRegex(ValueError,'visual binding'):producer.validate_plan(story,self.plan)
    def test_all_original_programme_audio_is_decoded_and_script_bound(self):
        edition=producer.read(producer.DIST/'programmes.json',{})
        for story in edition['stories']:
            self.assertEqual(len(story['sourceScriptSha256']),64)
            for track in story['voices'].values():
                self.assertTrue(track['fullDecodePassed'])
                self.assertEqual(producer.hashlib.sha256(producer.asset(track['audio']).read_bytes()).hexdigest(),track['sha256'])
                self.assertGreater(track['duration'],25)

if __name__=='__main__':unittest.main()
