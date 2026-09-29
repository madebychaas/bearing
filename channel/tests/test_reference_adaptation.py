import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import coverage,editorial,scriptdesk

class CoverageTests(unittest.TestCase):
 def item(self,id,title,date='2026-09-29T12:00:00+00:00'):
  return {'id':id,'title':title,'publishedTime':date,'source':{'url':'https://example.org/'+id,'name':'NPR'},'editorial':{'score':40}}
 def test_same_event_retains_every_source(self):
  a=self.item('a','Trump weakens fuel efficiency standards for new cars');b=self.item('b',"What Trump's rollback of fuel economy standards means for drivers")
  grouped,audit=coverage.group_reports([a,b]);self.assertEqual(len(audit),1);self.assertEqual(grouped[0]['coverage']['id'],grouped[1]['coverage']['id']);self.assertEqual(len(grouped[0]['coverage']['sources']),2)
 def test_same_topic_different_event_kept_separate(self):
  a=self.item('a','Court approves new tax rule for banks');b=self.item('b','Court rejects new tax rule for banks')
  self.assertIsNone(coverage.same_event(a,b))
 def test_new_figure_or_old_event_is_not_a_duplicate(self):
  a=self.item('a','Agency approves 20 million in housing grants')
  self.assertIsNone(coverage.same_event(a,self.item('b','Agency approves 30 million in housing grants')))
  self.assertIsNone(coverage.same_event(a,self.item('b',a['title'],'2026-09-20T12:00:00+00:00')))
 def test_split_groups_do_not_keep_the_same_identity(self):
  a=self.item('a','Court approves new tax rule for banks');b=self.item('b','Court rejects new tax rule for banks');prior={x['id']:{'coverage':{'id':'event-old'}} for x in (a,b)}
  grouped,_=coverage.group_reports([a,b],prior);self.assertEqual(len({s['coverage']['id'] for s in grouped}),2)
 def test_roundups_cannot_lead_single_story_queue(self):
  result=editorial.assess(self.item('a','Fuel prices rise. And, a court case reopens'))
  self.assertTrue(result['suppressed']);self.assertTrue(result['roundup'])

class DraftDeskTests(unittest.TestCase):
 def setUp(self):
  self.text='The agency opened a public comment period on a proposed rule. The proposal covers business impersonation scams. Officials have not announced a final decision. Comments will inform the agency review before any final action.'
  self.pack={'sourceRevision':'a'*64,'evidence':[{'id':'a','headline':'Agency seeks comments on proposed scam rule','excerpt':self.text}]}
  def block(text):return {'text':text,'evidence':[{'id':'a','quote':self.text}]}
  self.draft={'title':'A proposal on impersonation scams','opening':[block('The agency is asking for public comments on a proposed rule covering business impersonation scams.')],'body':[block('The proposal remains under review. Officials have not announced a final decision, so a proposed change should not be described as an adopted rule.')],'closing':[block('Comments will inform the review before any final action. The next development to watch is the agency decision.')],'visuals':[{'kind':'text','purpose':'Explain proposal status','evidenceIds':['a'],'description':'Show proposal and review as separate steps'}],'pronunciations':[],'issues':[]}
 def test_valid_draft_stays_unapproved(self):
  result=scriptdesk.validate_draft(self.draft,self.pack);self.assertEqual(result['state'],'needs-editor-review')
 def test_invented_number_is_rejected(self):
  self.draft['body'][0]['text']+=' It affects 20 million people.'
  with self.assertRaisesRegex(ValueError,'figure'):scriptdesk.validate_draft(self.draft,self.pack)
 def test_invented_evidence_quote_is_rejected(self):
  self.draft['body'][0]['evidence'][0]['quote']='The agency made a final decision.'
  with self.assertRaisesRegex(ValueError,'excerpt'):scriptdesk.validate_draft(self.draft,self.pack)
 def test_unknown_media_source_is_rejected(self):
  self.draft['visuals'][0]['evidenceIds']=['fiction']
  with self.assertRaisesRegex(ValueError,'source-bound'):scriptdesk.validate_draft(self.draft,self.pack)
 def test_model_failure_cannot_publish(self):
  with tempfile.TemporaryDirectory() as temp,patch.object(scriptdesk,'model_call',side_effect=OSError('offline')):
   with self.assertRaises(OSError):scriptdesk.generate(self.pack,Path(temp),'http://127.0.0.1:1234/v1','configured-model')
   self.assertFalse((Path(temp)/'edited.json').exists())
 def test_two_pass_generation_saves_review_required_output(self):
  with tempfile.TemporaryDirectory() as temp,patch.object(scriptdesk,'model_call',side_effect=[self.draft,self.draft]) as model:
   result=scriptdesk.generate(self.pack,Path(temp),'http://127.0.0.1:1234/v1','test-only')
   self.assertEqual(model.call_count,2);self.assertEqual(result['state'],'needs-editor-review');self.assertTrue((Path(temp)/'draft.json').exists());self.assertTrue((Path(temp)/'edited.json').exists())
 def test_external_model_destination_rejected(self):
  with self.assertRaisesRegex(ValueError,'loopback'):scriptdesk.model_call('https://example.org/v1','model',[])

if __name__=='__main__':unittest.main()
