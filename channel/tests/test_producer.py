import copy,json,shutil,sys,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'production'))
import producer

class ProducerTests(unittest.TestCase):
 def setUp(self):
  self.fixture=json.loads((ROOT/'production/producer-demo.json').read_text(encoding='utf-8'))
  self.config=producer._config();self.now=datetime(2026,9,29,18,tzinfo=timezone.utc)
  self.step=self.fixture['steps'][0]
 def snapshot(self,step=None,state=None,now=None,config=None):
  step=step or self.step
  return producer.build_snapshot(step['reporting'],step['candidates'],step['sourceHealth'],state,config or self.config,now or self.now)
 def observe(self,step,state=None,now=None):
  state=state or {};groups=producer._groups(step['reporting'],step['candidates'],step['sourceHealth'],state)
  return producer._observe(groups,state,now or self.now)
 def event(self,snapshot,key):return next(e for e in snapshot['events'] if e['id']==key)
 def store(self):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
  (root/'production').mkdir();(root/'dist').mkdir()
  for filename in ('producer-demo.json','producer-strategy.json'):shutil.copyfile(ROOT/'production'/filename,root/'production'/filename)
  return producer.ProducerStore(root,now=lambda:self.now)
 def test_products_rank_distinct_jobs_and_reasons_cite_matched_evidence(self):
  value=self.snapshot()
  self.assertEqual(value['rankings']['brief'][0],'demo-event-heater-recall')
  self.assertEqual(value['rankings']['focus'][0],'demo-event-housing-funding-rule')
  for event in value['events']:
   evidence={r['id']:r for r in event['evidence']}
   for match in event['strategy']['matches']:
    self.assertTrue(match['evidenceIds'])
    text=' '.join(evidence[key]['title']+' '+evidence[key]['excerpt'] for key in match['evidenceIds']).lower()
    for term in match['terms']:self.assertIn(term.lower(),text)
 def test_pure_builder_preserves_inputs_and_candidate_pool_exceeds_board_size(self):
  before=copy.deepcopy(self.step);value=self.snapshot()
  self.assertEqual(before,self.step)
  self.assertGreater(len(value['events']),self.config['boardSize'])
  self.assertEqual(len(value['rankings']['brief']),len(value['events']))
 def test_current_timestamp_required_and_future_or_stale_not_eligible(self):
  value=self.snapshot()
  for status in ('future','stale'):
   events=[e for e in value['events'] if e['whyNow']['status']==status]
   self.assertTrue(events)
   self.assertTrue(all(not e['eligible'] and e['gaps'] for e in events))
  step=copy.deepcopy(self.step)
  step['reporting']['items'][0]['publishedTime']='2026-09-29'
  event=self.event(self.snapshot(step),step['reporting']['items'][0]['coverage']['id'])
  self.assertEqual(event['whyNow']['status'],'unknown');self.assertFalse(event['eligible'])
 def test_headline_only_gaps_are_explicit(self):
  step=copy.deepcopy(self.step);sid=step['reporting']['items'][0]['id']
  for source in (step['reporting']['items'],step['candidates']['items']):
   next(r for r in source if r['id']==sid)['sourceExcerpt']=''
  event=self.event(self.snapshot(step),'demo-event-heater-recall')
  self.assertTrue(any('Headline-only' in gap for gap in event['gaps']))
  self.assertTrue(all(e['level']=='headline' for e in event['evidence']))
 def test_material_change_cosmetic_and_new_source_are_distinct(self):
  state=self.observe(self.step);step=self.fixture['steps'][1];now=self.now+timedelta(minutes=30)
  state=self.observe(step,state,now);value=self.snapshot(step,state,now)
  recall=self.event(value,'demo-event-heater-recall')
  self.assertTrue(recall['change']['material']);self.assertTrue(recall['signals']['update'])
  self.assertIn('10000',recall['change']['details'][0]['reason'])
  self.assertIn('40000',recall['change']['details'][0]['reason'])
  housing=self.event(value,'demo-event-housing-funding-rule')
  self.assertEqual(housing['change']['kind'],'source-added');self.assertFalse(housing['signals']['update'])
  outage=self.event(value,'demo-event-utility-outage')
  self.assertFalse(outage['signals']['update'])
 def test_timestamp_and_promotional_append_do_not_create_material_update(self):
  state=self.observe(self.step);step=copy.deepcopy(self.step)
  for source in (step['reporting']['items'],step['candidates']['items']):
   report=source[0];report['publishedTime']='2026-09-29T17:59:00Z'
   report['sourceExcerpt']+=' Sign up for our newsletter for 50 deals every week.'
  result=self.observe(step,state,self.now+timedelta(minutes=2))
  self.assertEqual(len(result['events']['demo-event-heater-recall']['history']),1)
 def test_cosmetic_after_material_does_not_hide_update(self):
  state=self.observe(self.step);second=self.fixture['steps'][1];now=self.now+timedelta(minutes=30)
  state=self.observe(second,state,now);third=copy.deepcopy(second)
  for items in (third['reporting']['items'],third['candidates']['items']):
   item=next(r for r in items if r['id']=='demo-heater-recall');item['title']='Updated: '+item['title']+' | Report'
  state=self.observe(third,state,now+timedelta(minutes=1));event=self.event(self.snapshot(third,state,now+timedelta(minutes=1)),'demo-event-heater-recall')
  self.assertTrue(event['signals']['update']);self.assertTrue(event['change']['material'])
 def test_local_convergence_requires_three_original_owners_markets(self):
  value=self.snapshot();signals=[e for e in value['events'] if e['localSignal']]
  self.assertEqual(len(signals),3)
  for event in signals:
   self.assertEqual(len(event['localSignal']['markets']),3)
   self.assertEqual(event['localSignal']['label'],'Insurance costs across local markets')
   self.assertNotIn('demo-event-ap-insurance-wire',[event['id']])
  step=copy.deepcopy(self.step)
  # A third local masthead belonging to the same owner is not an independent third source.
  local=[r for r in step['reporting']['items'] if r.get('local') and r.get('originalReporting') and 'insurance' in r['title']]
  local[2]['owner']=local[0]['owner']
  self.assertFalse(any(e['localSignal'] for e in self.snapshot(step)['events']))
 def test_syndicated_or_near_duplicate_local_copies_do_not_make_pattern(self):
  step=copy.deepcopy(self.step);local=[r for r in step['reporting']['items'] if r.get('local') and r.get('originalReporting') and 'insurance' in r['title']]
  local[2]['sourceExcerpt']=local[0]['sourceExcerpt']
  self.assertFalse(any(e['localSignal'] for e in self.snapshot(step)['events']))
 def test_foreign_local_and_promotional_reports_cannot_crowd_recommendations(self):
  step=copy.deepcopy(self.step);first=step['reporting']['items'][0]
  first['editorial']={'foreignLocal':True,'domestic':False}
  event=self.event(self.snapshot(step),'demo-event-heater-recall')
  self.assertFalse(event['eligible']);self.assertLess(event['fits']['brief']['score'],self.event(self.snapshot(),'demo-event-heater-recall')['fits']['brief']['score'])
  self.assertTrue(any('outside the U.S.' in gap for gap in event['gaps']))
 def test_decisions_persist_reverse_and_dismissal_does_not_hide_new_material(self):
  store=self.store();event_id='demo-event-heater-recall'
  store.decide(event_id,'shortlist','Potential service item',mode='demo')
  result=store.decide(event_id,'dismiss','Already covered',mode='demo')
  self.assertEqual(self.event(result,event_id)['decision']['action'],'dismiss')
  result=store.demo('advance');event=self.event(result,event_id)
  self.assertEqual(event['decision']['action'],'dismiss');self.assertTrue(event['signals']['update'])
  reloaded=producer.ProducerStore(store.root,now=lambda:self.now)
  result=reloaded.decide(event_id,'reset',mode='demo');decision=self.event(result,event_id)['decision']
  self.assertEqual(decision['action'],'none');self.assertEqual([x['action'] for x in decision['history']],['shortlist','dismiss','reset'])
  self.assertFalse((store.runs/'producer-state.json').exists())
 def test_demo_reset_does_not_touch_live_state(self):
  store=self.store();store.snapshot();before=(store.runs/'producer-state.json').read_bytes()
  store.demo('advance');result=store.demo('reset')
  self.assertEqual(result['demo']['step'],0)
  self.assertEqual(before,(store.runs/'producer-state.json').read_bytes())
 def test_input_revision_mismatch_withholds_mixed_claims_and_preserves_baseline(self):
  state=self.observe(self.step);step=copy.deepcopy(self.fixture['steps'][1]);sid='demo-heater-recall'
  report=next(r for r in step['reporting']['items'] if r['id']==sid);report['version']='old-revision'
  candidate=next(r for r in step['candidates']['items'] if r['id']==sid);candidate['contentHash']='new-revision'
  value=self.snapshot(step,state,self.now+timedelta(minutes=30));event=self.event(value,'demo-event-heater-recall')
  self.assertFalse(event['eligible']);self.assertTrue(event['evidence'][0]['revisionMismatch']);self.assertEqual(event['evidence'][0]['excerpt'],'')
  unchanged=self.observe(step,state,self.now+timedelta(minutes=30))
  self.assertEqual(state['events']['demo-event-heater-recall']['fingerprint'],unchanged['events']['demo-event-heater-recall']['fingerprint'])
 def test_single_server_threads_do_not_lose_decisions_or_break_json(self):
  store=self.store();store.snapshot('demo');ids=[e['id'] for e in store.snapshot('demo')['events'][:6]]
  with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(lambda key:store.decide(key,'watch',mode='demo'),ids))
  result=store.snapshot('demo');self.assertEqual(result['stats']['watching'],6)
  self.assertEqual(len(json.loads((store.runs/'producer-demo-state.json').read_text(encoding='utf-8'))['events']),13)
 def test_corrupt_state_is_preserved_instead_of_silently_erasing_decisions(self):
  store=self.store();store.snapshot('demo');path=store.runs/'producer-demo-state.json';path.write_text('broken state',encoding='utf-8')
  with self.assertRaisesRegex(RuntimeError,'preserved'):store.snapshot('demo')
  self.assertEqual(path.read_text(encoding='utf-8'),'broken state')
 def test_corrupt_input_does_not_rewrite_existing_history(self):
  store=self.store();store.snapshot();path=store.runs/'producer-state.json';before=path.read_bytes()
  (store.root/'dist/reporting.json').write_text('{broken',encoding='utf-8')
  with self.assertRaisesRegex(RuntimeError,'preserved'):store.snapshot()
  self.assertEqual(path.read_bytes(),before)
 def test_ambiguous_keywords_and_reaction_are_alternatives_not_primary(self):
  cases=[('The future is AI vs. AI','Researchers say more training improves AI systems. The models blocked attacks in a controlled benchmark, and the technology companies plan to keep working on software reliability.'),
         ('Musician demands government stop using his song','The artist argues that copyright law protects his recording, and his lawyers asked the government to stop using the song in a publicity video.'),
         ('Council members face recall election','Residents called for their recall over a proposed data center. A recall election is planned next year after a contentious council meeting.'),
         ('Politician criticizes rollback of fuel economy standards','The policy rollback may raise costs for drivers, according to a new estimate. The speech focused on criticism of the administration and its motives.'),
         ('Argentina threatens legal action against UK over Falkland oilfield','The government set a two-week deadline for the oilfield exploration project to be scrapped after a disagreement with British officials.')]
  for title,excerpt in cases:
   with self.subTest(title=title):
    step=copy.deepcopy(self.step)
    for items in (step['reporting']['items'],step['candidates']['items']):
     item=items[0];item['title']=title;item['sourceExcerpt']=excerpt
    self.assertFalse(self.event(self.snapshot(step),'demo-event-heater-recall')['eligible'])
 def test_product_scores_do_not_saturate_into_hash_order(self):
  value=self.snapshot();scores=[e['fits']['brief']['score'] for e in value['events']]
  self.assertGreater(max(scores),100)
  self.assertEqual(value['rankings']['brief'][0],'demo-event-heater-recall')
 def test_invalid_actions_modes_and_ids_do_not_write_decisions(self):
  store=self.store()
  for action in ('publish','assign','delete'):
   with self.assertRaises(ValueError):store.decide('anything',action)
  with self.assertRaises(ValueError):store.snapshot('unknown')
  with self.assertRaises(ValueError):store.decide('missing','watch',mode='demo')
  with self.assertRaises(ValueError):store.decide('demo-event-heater-recall','watch','x'*501,mode='demo')
 def test_no_party_or_person_preference_in_configuration(self):
  text=json.dumps(self.config).lower()
  for name in ('democrat','republican','trump','biden','liberal','conservative'):self.assertNotIn(name,text)

if __name__=='__main__':unittest.main()
