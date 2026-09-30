import copy
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PRODUCTION=Path(__file__).resolve().parents[1]/'production'
sys.path.insert(0,str(PRODUCTION))
import scriptdesk


class EditorialVoiceTests(unittest.TestCase):
 def setUp(self):
  self.evidence='The agency opened a public comment period on a proposed rule covering business impersonation scams. Officials have not announced a final decision. Comments will inform the review before any final action.'
  self.pack={'sourceRevision':'a'*64,'voice':'obsolete queued guidance','evidence':[{'id':'source-a','headline':'Agency seeks comments on scam proposal','excerpt':self.evidence}]}
  def block(text):return {'text':text,'evidence':[{'id':'source-a','quote':self.evidence}]}
  self.draft={'title':'A proposed safeguard against impersonation scams','opening':[block('A proposed rule would address business impersonation scams.')],'body':[block('The agency opened a public comment period on the proposal. Officials have not announced a final decision, so the proposed safeguards are still under review.')],'closing':[block('Comments will inform the agency review before any final action.')],'visuals':[{'kind':'text','purpose':'Keep proposal status clear','evidenceIds':['source-a'],'description':'Separate proposal and review; no final approval stamp.'}],'pronunciations':[],'issues':[]}

 def test_long_copy_cannot_pass_a_short_segment_budget(self):
  draft=copy.deepcopy(self.draft)
  draft['body'][0]['text']=' '.join([draft['body'][0]['text']]*6)
  with self.assertRaisesRegex(ValueError,'narration-only'):scriptdesk.validate_draft(draft,self.pack)

 def test_estimate_includes_measured_pace_and_framing_without_claiming_a_render(self):
  result=scriptdesk.validate_draft(self.draft,self.pack)
  self.assertEqual(result['estimatedSeconds'],result['words']/2+2.5)
  self.assertIn('actual TTS',result['durationBasis'])
  self.assertEqual(result['state'],'needs-editor-review')

 def test_both_model_passes_use_current_examples_not_stale_queued_guidance(self):
  with tempfile.TemporaryDirectory() as directory:
   profile=scriptdesk.editorial_voice();profile['version']='new-editorial-revision'
   profile['principles'].append('CURRENT_STYLE_MARKER')
   path=Path(directory)/'voice.json';path.write_text(json.dumps(profile),encoding='utf-8')
   with patch.object(scriptdesk,'VOICE_PATH',path),patch.object(scriptdesk,'model_call',side_effect=[self.draft,self.draft]) as model:
    result=scriptdesk.generate(self.pack,Path(directory)/'attempt','http://127.0.0.1:1234/v1','test-model')
   self.assertEqual(model.call_count,2)
   for call in model.call_args_list:
    instruction=call.args[2][0]['content']
    self.assertIn('CURRENT_STYLE_MARKER',instruction)
    self.assertIn('report-consequence',instruction)
    self.assertIn('examples are not evidence',instruction)
    self.assertNotIn('obsolete queued guidance',instruction)
   saved=json.loads((Path(directory)/'attempt/edited.json').read_text())
   self.assertEqual(saved['voiceRevision'],scriptdesk.fingerprint(profile))
   self.assertEqual(result['voiceRevision'],saved['voiceRevision'])
   self.assertEqual(saved['voiceVersion'],profile['version'])

 def test_style_example_cannot_be_cited_as_story_evidence(self):
  draft=copy.deepcopy(self.draft)
  draft['opening'][0]['evidence'][0]['id']='report-consequence'
  with self.assertRaisesRegex(ValueError,'Evidence reference'):scriptdesk.validate_draft(draft,self.pack)

 def test_generation_uses_one_utc_clock_in_both_passes_and_persisted_review(self):
  import pipeline
  as_of='2026-09-30T23:59:59.123456+00:00'
  self.pack['asOf']='2026-09-01T00:00:00+00:00'
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory)/'attempt'
   with patch.object(pipeline,'stamp',return_value=as_of) as clock,patch.object(scriptdesk,'model_call',side_effect=[self.draft,self.draft]) as model:
    result=scriptdesk.generate(self.pack,folder,'http://127.0.0.1:1234/v1','test-model')
   clock.assert_called_once_with()
   self.assertEqual(model.call_count,2)
   for call in model.call_args_list:
    payload=json.loads(call.args[2][1]['content'])
    self.assertEqual(payload['asOf'],as_of)
    self.assertIn('never evidence',payload['clockPurpose'])
    self.assertEqual(payload['evidence'],self.pack['evidence'])
   metadata=json.loads((folder/'generation.json').read_text(encoding='utf-8'))
   edited=json.loads((folder/'edited.json').read_text(encoding='utf-8'))
   for record in (metadata,edited,edited['review'],result):self.assertEqual(record['asOf'],as_of)
   self.assertEqual(metadata['voiceRevision'],edited['voiceRevision'])
   self.assertEqual(metadata['sourceRevision'],self.pack['sourceRevision'])

 def test_generation_clock_survives_failed_model_attempt(self):
  import pipeline
  as_of='2026-09-30T12:30:00+00:00'
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory)/'attempt'
   with patch.object(pipeline,'stamp',return_value=as_of),patch.object(scriptdesk,'model_call',side_effect=RuntimeError('unavailable')):
    with self.assertRaisesRegex(RuntimeError,'unavailable'):scriptdesk.generate(self.pack,folder,'http://127.0.0.1:1234/v1','test-model')
   metadata=json.loads((folder/'generation.json').read_text(encoding='utf-8'))
   self.assertEqual(metadata['asOf'],as_of)
   self.assertEqual(metadata['voiceRevision'],scriptdesk.fingerprint(scriptdesk.editorial_voice()))
   self.assertFalse((folder/'edited.json').exists())

 def test_queue_marks_latest_draft_style_without_replacing_history_or_states(self):
  import editorial
  pack={**self.pack,'voiceRevision':scriptdesk.fingerprint(scriptdesk.editorial_voice())}
  item={'id':'source-a','title':self.draft['title']}
  with tempfile.TemporaryDirectory() as directory,patch.object(scriptdesk,'packet',return_value=pack),patch.object(editorial,'rank',return_value=[item]),patch.object(scriptdesk,'model_call') as model:
   root=Path(directory)
   def queued():return scriptdesk.prepare_queue([],[],root)[0]
   row=queued()
   self.assertEqual(row['state'],'needs-script')
   self.assertEqual(row['styleStatus'],'not-drafted')
   self.assertFalse(row['needsStyleRefresh'])
   folder=root/'script-desk'/pack['sourceRevision']
   evidence_before=(folder/'evidence.json').read_bytes()
   legacy=folder/'attempt-20260929T120000000000Z'/'edited.json'
   legacy.parent.mkdir();legacy.write_text(json.dumps({'draft':self.draft}),encoding='utf-8')
   legacy_before=legacy.read_bytes()
   row=queued()
   self.assertEqual(row['state'],'needs-editor-review')
   self.assertEqual(row['styleStatus'],'stale')
   self.assertIsNone(row['draftVoiceRevision'])
   self.assertTrue(row['needsStyleRefresh'])
   current=folder/'attempt-20260930T120000000000Z'/'edited.json'
   current.parent.mkdir();current.write_text(json.dumps({'draft':self.draft,'voiceRevision':pack['voiceRevision']}),encoding='utf-8')
   current_before=current.read_bytes()
   row=queued()
   self.assertEqual(row['state'],'needs-editor-review')
   self.assertEqual(row['styleStatus'],'current')
   self.assertFalse(row['needsStyleRefresh'])
   self.assertEqual(row['draftVoiceRevision'],row['voiceRevision'])
   self.assertEqual(root/row['latestDraft'],current)
   pack['voiceRevision']='b'*64
   row=queued()
   self.assertEqual(row['state'],'needs-editor-review')
   self.assertEqual(row['styleStatus'],'stale')
   self.assertTrue(row['needsStyleRefresh'])
   self.assertEqual(row['voiceRevision'],'b'*64)
   self.assertNotEqual(row['draftVoiceRevision'],row['voiceRevision'])
   self.assertEqual((folder/'evidence.json').read_bytes(),evidence_before)
   self.assertEqual(legacy.read_bytes(),legacy_before)
   self.assertEqual(current.read_bytes(),current_before)
   model.assert_not_called()

 def test_unreadable_draft_metadata_is_not_reported_as_current_style(self):
  import editorial
  pack={**self.pack,'voiceRevision':'b'*64}
  with tempfile.TemporaryDirectory() as directory,patch.object(scriptdesk,'packet',return_value=pack),patch.object(editorial,'rank',return_value=[{'id':'source-a','title':'Story'}]):
   root=Path(directory)
   draft=root/'script-desk'/pack['sourceRevision']/'attempt-20260930T120000000000Z'/'edited.json'
   draft.parent.mkdir(parents=True);draft.write_text('{unfinished',encoding='utf-8')
   row=scriptdesk.prepare_queue([],[],root)[0]
   self.assertEqual(row['state'],'needs-editor-review')
   self.assertEqual(row['styleStatus'],'stale')
   self.assertTrue(row['needsStyleRefresh'])
   self.assertEqual(draft.read_text(encoding='utf-8'),'{unfinished')

 def test_missing_style_standard_stops_before_model_call(self):
  with tempfile.TemporaryDirectory() as directory,patch.object(scriptdesk,'VOICE_PATH',Path(directory)/'missing.json'),patch.object(scriptdesk,'model_call') as model:
   with self.assertRaises(FileNotFoundError):scriptdesk.generate(self.pack,Path(directory)/'attempt','http://127.0.0.1:1234/v1','test-model')
   model.assert_not_called()

 def test_rewrite_bank_preserves_baselines_hashes_and_exact_visual_cues(self):
  bank=json.loads((PRODUCTION/'editorial-rewrites-20260930.json').read_text(encoding='utf-8'))
  self.assertEqual(len(bank['stories']),13)
  self.assertEqual(len({s['id'] for s in bank['stories']}),13)
  normalize=lambda value:' '.join(re.findall(r'\w+',value.lower()))
  for story in bank['stories']:
   with self.subTest(story=story['id']):
    self.assertEqual(story['script'],' '.join(story[k] for k in ('opening','body','closing')))
    for value,digest in [('beforeScript','originalSha256'),('script','scriptSha256')]:
     self.assertEqual(hashlib.sha256(story[value].encode()).hexdigest(),story[digest])
    self.assertEqual(story['wordCount'],len(story['script'].split()))
    self.assertLessEqual(story['wordCount'],80)
    self.assertEqual(story['productionStatus'],'not-rendered')
    self.assertIs(story['viewerApproved'],False)
    self.assertIn(story['timeliness']['mode'],('current','dated-context','hold'))
    self.assertTrue(story['sourceCheck']['checkedAt'])
    self.assertTrue(story['claimChecks'])
    for visual in story['visualPlan']:self.assertIn(normalize(visual['cue']),normalize(story['script']))


if __name__=='__main__':unittest.main()
