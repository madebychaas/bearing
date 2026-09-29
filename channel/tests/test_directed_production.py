import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import broadcast,produce_programmes as producer

class DirectedProductionTests(unittest.TestCase):
 def test_failed_or_missing_plan_retains_the_published_story(self):
  for plans in ({},{'story':{'title':'draft'}}):
   with self.subTest(plans=plans),tempfile.TemporaryDirectory() as directory:
    root=Path(directory);dist=root/'dist';work=root/'work';dist.mkdir();work.mkdir()
    previous={'id':'story','programmeVersion':'known-good','title':'Published story'}
    def write(path,data):path.write_text(json.dumps(data),encoding='utf-8')
    write(dist/'edition.json',{'edition':'2026-09-29','stories':[{'id':'story'}]})
    write(dist/'programmes.json',{'version':'old','stories':[previous]})
    write(dist/'reporting.json',{'items':[]})
    write(work/'runtime.json',{'modelDir':'unused','ffmpeg':'unused'})
    write(work/'programme-plans.json',{'stories':plans})
    with patch.object(producer,'DIST',dist),patch.object(producer,'WORK',work),patch.object(producer,'make_sounds'),patch.object(producer,'produce_story',side_effect=ValueError('Unreviewed cue')),patch.object(broadcast,'publish_record'):
     producer.produce('story')
    self.assertEqual(json.loads((dist/'programmes.json').read_text())['stories'],[previous])
    self.assertEqual(len(json.loads((work/'runs/programme-status.json').read_text())['held']),1)

 def test_unreviewed_third_party_asset_is_held_before_composition(self):
  story=next(s for s in producer.read(producer.DIST/'edition.json',{})['stories'] if s['id']=='reviewed-nist-workforce-20260918-v1')
  plan=producer.read(producer.WORK/'programme-plans.json',{})['stories'][story['id']]
  plan=json.loads(json.dumps(plan));plan['beats'][-1]['media']['usageApproved']=False
  with tempfile.TemporaryDirectory() as directory:
   run=broadcast.Run(Path(directory),story,'rights-test')
   run.finish=lambda *args,**kwargs:None
   with self.assertRaisesRegex(ValueError,'reviewed rights'):broadcast.visuals(run,story,plan)

if __name__=='__main__':unittest.main()
