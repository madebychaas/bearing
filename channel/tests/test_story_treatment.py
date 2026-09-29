import sys,unittest,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import broadcast,scriptdesk

class StoryTreatmentTests(unittest.TestCase):
 def test_cues_follow_real_voice_timing_and_cross_caption_boundaries(self):
  beats=[{'cue':'The awards'},{'cue':'Local employers need practical skills'}]
  captions=[{'start':12,'text':'The awards support training.'},{'start':22,'text':'Local employers need'},{'start':24,'text':'practical skills.'}]
  self.assertEqual(broadcast.timed_beats(beats,captions,{'start':10,'end':35}),[{'start':10,'end':22,'beat':0},{'start':22,'end':35,'beat':1}])
  shifted=[{**c,'start':c['start']+3} for c in captions]
  self.assertEqual(broadcast.timed_beats(beats,shifted,{'start':10,'end':40})[1]['start'],25)
 def test_missing_ambiguous_and_out_of_order_cues_hold_the_package(self):
  captions=[{'start':2,'text':'One event. One event.'},{'start':5,'text':'Next event.'}]
  for beats in ([{'cue':'Missing'}],[{'cue':'One event'}],[{'cue':'Next event'},{'cue':'One event One event'}]):
   with self.assertRaises(ValueError):broadcast.timed_beats(beats,captions,{'start':0,'end':10})
 def test_existing_plans_keep_their_old_visual_timing(self):
  self.assertIsNone(broadcast.timed_beats([{'text':'Existing fact'}],[],{'start':0,'end':10}))
 def test_reveals_use_actual_word_times_instead_of_sentence_start(self):
  captions=[{'start':2,'text':'Funding supports nine partnerships.'}]
  words=[{'start':2,'text':'Funding'},{'start':3,'text':'supports'},{'start':4,'text':'nine'},{'start':5,'text':'partnerships.'}]
  chapter={'start':1,'end':8}
  self.assertEqual(broadcast.timed_reveals([{'cue':'nine partnerships'}],captions,chapter,words),[{'start':4,'reveal':0}])
  with self.assertRaises(ValueError):broadcast.timed_reveals([{'cue':'nine'},{'cue':'Funding'}],captions,chapter,words)
 def test_reviewed_spoken_copy_is_shared_by_assembly_and_production_brief(self):
  root=Path(__file__).resolve().parents[1]
  plan=json.loads((root/'production/programme-plans.json').read_text(encoding='utf-8'))['stories']['reviewed-nist-workforce-20260918-v1']
  story=next(s for s in json.loads((root/'dist/edition.json').read_text(encoding='utf-8'))['stories'] if s['id']=='reviewed-nist-workforce-20260918-v1')
  with tempfile.TemporaryDirectory() as d:
   run=broadcast.Run(Path(d),story,'test');scripts=broadcast.write_and_edit(run,story,plan)
   brief=scriptdesk.production_brief(story,plan)
   self.assertEqual(scripts,{b['phase']:b['spokenText'] for b in brief['blocks']})
   self.assertEqual(scripts['opening'],plan['openingNarration'])
   self.assertEqual(json.loads((Path(d)/'source-evidence.json').read_text(encoding='utf-8'))['presentationReview'],plan['review'])

if __name__=='__main__':unittest.main()
