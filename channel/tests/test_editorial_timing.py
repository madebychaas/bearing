import json,sys,tempfile,unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'production'))
import broadcast

class EditorialTimingTests(unittest.TestCase):
 def setUp(self):
  self.today=date(2026,9,29)
  self.context={'mode':'context-example','developmentDate':'2026-09-18','sourcePublishedDate':'2026-09-18','sourceUpdatedDate':'2026-09-28','checkedAt':'2026-09-29','reason':'Production review of September 18 announcement; no verified new September 29 development.','evidenceUrl':'https://www.nist.gov/news-events/news/2026/09/nist-awards-more-17-million-support-cybersecurity-workforce-development'}
 def current(self,**changes):
  return {**self.context,'mode':'current','developmentDate':'2026-09-29','sourcePublishedDate':'2026-09-29','basis':'new-development','triggerDate':'2026-09-29','validThrough':'2026-09-30','reason':'New award decisions announced today change which regional partnerships receive funding.',**changes}
 def test_source_update_and_retrieval_do_not_refresh_old_development(self):
  result=broadcast.validate_editorial_timing(self.context,self.today)
  self.assertFalse(result['liveEligible'])
  self.assertEqual(result['developmentDate'],'2026-09-18')
  self.assertEqual(result['sourceUpdatedDate'],'2026-09-28')
  self.assertEqual(result['checkedAt'],'2026-09-29')
  for basis in ('retrieved','page-updated','built'):
   with self.subTest(basis=basis),self.assertRaisesRegex(ValueError,'not an editorial'):
    broadcast.validate_editorial_timing(self.current(basis=basis),self.today)
 def test_current_development_needs_a_bounded_review_window(self):
  self.assertTrue(broadcast.validate_editorial_timing(self.current(),self.today)['liveEligible'])
  for changes in ({'validThrough':'2026-09-28'},{'validThrough':'2026-10-15'},{'triggerDate':'2026-09-18'},{'triggerDate':'2026-09-30'}):
   with self.subTest(changes=changes),self.assertRaises(ValueError):broadcast.validate_editorial_timing(self.current(**changes),self.today)
 def test_older_story_requires_newly_evidenced_impact_or_context(self):
  timing=self.current(developmentDate='2026-09-18',sourcePublishedDate='2026-09-18',basis='ongoing-impact',triggerDate='2026-09-29',reason='A separately sourced effect observed today changes the practical consequence for local trainees.')
  self.assertTrue(broadcast.validate_editorial_timing(timing,self.today)['liveEligible'])
  with self.assertRaises(ValueError):broadcast.validate_editorial_timing({**timing,'triggerDate':'2026-09-30'},self.today)
 def test_deadline_cannot_remain_current_after_it_passes(self):
  self.assertTrue(broadcast.validate_editorial_timing(self.current(basis='deadline',triggerDate='2026-09-30'),self.today)['liveEligible'])
  with self.assertRaisesRegex(ValueError,'passed deadline'):broadcast.validate_editorial_timing(self.current(basis='deadline',triggerDate='2026-09-28'),self.today)
 def test_missing_invalid_or_future_review_evidence_holds(self):
  for changes in ({'reason':'Fetched today'},{'evidenceUrl':'file:///local/news'},{'checkedAt':'2026-09-30'},{'developmentDate':'2026-09-31'},{'sourceUpdatedDate':'2026-10-01'}):
   with self.subTest(changes=changes),self.assertRaises(ValueError):broadcast.validate_editorial_timing({**self.context,**changes},self.today)
 def test_legacy_exception_binds_id_source_and_exact_spoken_copy(self):
  sid='auto-a46bc2af204ae5'
  story=next(s for s in json.loads((ROOT/'dist/edition.json').read_text(encoding='utf-8'))['stories'] if s['id']==sid)
  plan=json.loads((ROOT/'production/programme-plans.json').read_text(encoding='utf-8'))['stories'][sid]
  scripts={'opening':plan.get('openingNarration',f"{plan['title']}. {plan['why']}"),'story':plan.get('body',story['script']),'closing':plan.get('closingNarration',f"{plan['summary']} What to watch next. {plan['lookAhead']}")}
  result=broadcast.editorial_timing(story,plan,scripts,self.today)
  self.assertEqual(result['mode'],'legacy-context');self.assertFalse(result['liveEligible'])
  cases=[({**story,'id':'new-story'},plan,scripts),(story,{**plan,'sourceScriptSha256':'changed'},scripts),(story,plan,{**scripts,'opening':scripts['opening']+' A new claim.'}),(story,{**plan,'visualTreatment':'directed'},scripts)]
  for changed_story,changed_plan,changed_scripts in cases:
   with self.assertRaisesRegex(ValueError,'why-now'):broadcast.editorial_timing(changed_story,changed_plan,changed_scripts,self.today)
 def test_expired_current_record_is_rechecked_before_cache_reuse(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   (root/'production.json').write_text(json.dumps({'state':'published','stages':[{'stage':s} for s in broadcast.STAGES]}),encoding='utf-8')
   (root/'source-evidence.json').write_text(json.dumps({'editorialTiming':self.current()}),encoding='utf-8')
   with patch.object(broadcast,'validate_editorial_timing',side_effect=ValueError('expired')) as check:
    self.assertFalse(broadcast.cache_valid(root,{}));check.assert_called_once()

if __name__=='__main__':unittest.main()
