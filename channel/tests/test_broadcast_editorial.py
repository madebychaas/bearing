import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import broadcast,editorial,produce_programmes as producer

class EditorialTests(unittest.TestCase):
 def item(self,title,publisher='Axios'):
  return {'id':title,'title':title,'source':{'name':publisher}}
 def test_domestic_quota_and_variety(self):
  stories=[self.item(f'American prices rise {i}', 'BBC' if i<12 else ['Axios','CNBC','NPR'][i%3]) for i in range(50)]
  result=editorial.rank(stories,20)
  self.assertEqual(len(result),20);self.assertGreaterEqual(sum(s['editorial']['domestic'] for s in result),18)
  self.assertGreater(len({s['source']['name'] for s in result[:4]}),1)
 def test_policy_survives_political_sparring(self):
  self.assertFalse(editorial.assess(self.item('President signs tax bill amid feud'))['suppressed'])
  self.assertTrue(editorial.assess(self.item('Senators trade barbs in feud'))['suppressed'])
 def test_election_recall_is_not_consumer_recall(self):
  self.assertEqual(editorial.assess(self.item('Recall petitions target mayor'))['focus'],'general')
  self.assertEqual(editorial.assess(self.item('Product recall over fire risk'))['focus'],'consumer-economy')
 def test_foreign_local_filter(self):
  self.assertTrue(editorial.assess(self.item('NHS funding changes in Britain','BBC'))['foreignLocal'])
  self.assertFalse(editorial.assess(self.item('Global oil prices hit American drivers','BBC'))['foreignLocal'])

class BroadcastTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.story=producer.read(producer.DIST/'edition.json',{})['stories'][0]
  self.plan=producer.read(producer.WORK/'programme-plans.json',{})['stories'][self.story['id']]
  self.run=broadcast.Run(Path(self.temp.name),self.story,'test')
 def test_order_required(self):
  with self.assertRaisesRegex(ValueError,'out of order'):self.run.finish('publish')
 def test_source_revision_held_before_speech(self):
  with self.assertRaisesRegex(ValueError,'revision'):broadcast.write_and_edit(self.run,{**self.story,'script':self.story['script']+' changed'},self.plan)
  self.run.hold('Changed evidence')
  self.assertEqual(self.run.data['heldAt'],'edit_script')
 def test_review_artifacts_are_saved(self):
  scripts=broadcast.write_and_edit(self.run,self.story,self.plan)
  self.assertEqual(set(scripts),{'opening','story','closing'})
  self.assertEqual(self.run.data['stages'][-1]['stage'],'edit_script')
  self.assertTrue((self.run.folder/'script-edited.json').exists())
 def test_published_packages_have_nine_stages_and_intact_assets(self):
  for story in producer.read(producer.DIST/'programmes.json',{})['stories']:
   folder=producer.WORK/'runs'/'programmes'/story['programmeVersion']
   record=producer.read(folder/'production.json',{})
   self.assertEqual([s['stage'] for s in record['stages']],broadcast.STAGES)
   self.assertEqual(record['state'],'published')
   self.assertTrue(broadcast.cache_valid(folder,story))

if __name__=='__main__':unittest.main()
