import copy,json,shutil,sys,tempfile,threading,unittest
from contextlib import nullcontext
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'production'))
import producer,selection,scriptdesk,pipeline


class SelectionTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);(self.root/'production').mkdir();(self.root/'dist').mkdir()
  self.fixture=json.loads((ROOT/'production/producer-demo.json').read_text(encoding='utf-8'))
  self.step=copy.deepcopy(self.fixture['steps'][0]);self.now=producer._time(self.fixture['baseTime'])
  shutil.copyfile(ROOT/'production/producer-strategy.json',self.root/'production/producer-strategy.json')
  shutil.copyfile(ROOT/'production/producer-demo.json',self.root/'production/producer-demo.json')
  self.write_step(self.step)
  self.desk=producer.ProducerStore(self.root,now=lambda:self.now);self.store=selection.SelectionStore(self.desk)
  self.event='demo-event-heater-recall'
  self.film_validation=patch.object(selection,'validate_film',return_value={'liveEligible':True});self.film_validation.start();self.addCleanup(self.film_validation.stop)

 def write_step(self,step):
  pipeline.write_json(self.root/'dist/reporting.json',step['reporting'])
  pipeline.write_json(self.root/'production/candidates/latest.json',step['candidates'])
  pipeline.write_json(self.root/'dist/source-status.json',step['sourceHealth'])

 def select(self,product='focus',mode='live'):
  prior=self.store.get(self.event,mode)['selection']
  return self.store.mutate({'action':'select','eventId':self.event,'mode':mode,'productId':product,'whyNow':'A current recall gives households a specific product-safety action.','note':'Explain the action without alarm.',**({'expectedRevision':prior['revision']} if prior else {})})['selection']

 def act(self,record,action,**values):
  return self.store.mutate({'action':action,'eventId':record['eventId'],'mode':record['mode'],'expectedRevision':record['revision'],**values})['selection']

 def draft(self,record):
  source=record['evidence'][0]
  def block(text):return {'text':text,'evidence':[{'id':source['id'],'quote':source['excerpt']}]}
  return {'title':'A household safety recall','opening':[block('A product recall gives households a reason to check what they own.')],'body':[block('The source identifies the affected product and explains the recall. Check that description against the product in your home before deciding whether the instructions apply.')],'closing':[block('Follow the recall instructions for the affected product. The next step is to check the details directly with the source.')],'pronunciations':[],'visuals':[{'kind':'text','purpose':'Explain the recall action','description':'Reveal the supported instruction as it is spoken.','evidenceIds':[source['id']]}],'issues':[]}

 def prepared(self,record,draft=None):
  record=self.act(record,'save',draft=draft or self.draft(record))
  packet={'story':{'id':'selection-test-story','script':selection.speech(record['draft']),'source':{'url':record['evidence'][0]['url']}},'plan':{'openingNarration':selection.speech(record['draft'],'opening'),'body':selection.speech(record['draft'],'body'),'closingNarration':selection.speech(record['draft'],'closing'),'review':{'accuracy':'Reviewed source facts.','voice':'Measured phrases.','visuals':'Original explanatory typography.','rights':{'graphics':'Original composition'}}},'visuals':{'assets':[]}}
  return self.act(record,'prepare',packet=packet)

 def approved(self):
  return self.act(self.prepared(self.select()),'review',decision='approve',actor='Test editor',note='Explicit test approval of this script and treatment.')

 def primary(self):
  return {'id':'primary-review','publisher':'Federal agency','title':'Primary recall bulletin','url':'https://agency.example/recall','excerpt':'The agency identified a safety issue with the affected product and provided recall instructions.','checkedAt':producer._stamp(self.now),'reviewNote':'Primary bulletin checked for the affected product and required action.'}

 def test_selection_carries_context_without_assigning_or_publishing(self):
  record=self.select()
  self.assertEqual(record['state'],'selected');self.assertEqual(record['product']['name'],'In Focus')
  self.assertEqual(record['context']['whyNow'],record['whyNow'])
  self.assertTrue(record['context']['opportunity']['fits']);self.assertTrue(record['evidence'][0]['contentHash'])
  self.assertEqual(record['sourceRevision'],selection.digest(record['evidence']))
  self.assertIsNone(record['approval']);self.assertIsNone(record['draft'])
  self.assertEqual(self.desk._state('live')['events'][self.event].get('decision'),None)
  self.assertFalse((self.root/'dist/films.json').exists())

 def test_exact_draft_plan_approval_binding_and_reversible_history(self):
  record=self.prepared(self.select());folder=self.store._path(self.event,'live')
  originals={p:p.read_bytes() for p in (folder/'revisions').glob('*.json')}
  with self.assertRaisesRegex(ValueError,'Reviewer'):self.act(record,'review',decision='approve')
  approved=self.act(record,'review',decision='approve',actor='Named editor',note='Approved in a recorded review.')
  self.assertEqual(approved['approval']['actor'],'Named editor')
  for key in ('scriptHash','sourceRevision','voiceRevision'):self.assertEqual(approved['approval'][key],approved[key])
  self.assertEqual(approved['approval']['packetHash'],approved['prepared']['packetHash'])
  held=self.act(approved,'review',decision='hold',actor='Named editor',note='Hold for a source check.')
  self.assertEqual(held['state'],'held');self.assertIsNone(held['approval'])
  for path,before in originals.items():self.assertEqual(path.read_bytes(),before)
  self.assertEqual(held['history'][-1]['action'],'hold')

 def test_revision_conflict_does_not_overwrite_a_newer_edit(self):
  record=self.select();current=self.act(record,'save',draft=self.draft(record))
  with self.assertRaises(selection.Conflict):self.act(record,'save',draft=self.draft(record))
  self.assertEqual(self.store.get(self.event)['selection']['revision'],current['revision'])

 def test_material_change_latches_reassessment_until_explicitly_refreshed(self):
  approved=self.approved();before=approved['sourceRevision']
  self.write_step(self.fixture['steps'][1])
  changed=self.store.get(self.event)['selection']
  self.assertEqual(changed['state'],'needs-reassessment');self.assertIsNone(changed['approval'])
  self.assertTrue(changed['reassessment']['required']);self.assertEqual(changed['sourceRevision'],before)
  with self.assertRaises(selection.Conflict):self.act(changed,'produce')
  refreshed=self.act(changed,'reassess',reason='The expanded recall changes the audience action; revise the script against the newer facts.')
  self.assertFalse(refreshed['reassessment']['required']);self.assertNotEqual(refreshed['sourceRevision'],before)
  self.assertIsNone(refreshed['approval']);self.assertIsNone(refreshed['prepared']);self.assertIsNone(refreshed['draftReview'])

 def test_deadline_or_negation_change_cannot_hide_behind_desk_heuristic(self):
  record=self.approved()
  step=copy.deepcopy(self.step)
  for group in (producer._items(step['reporting']),producer._items(step['candidates'])):
   item=next(r for r in group if r['id']==record['evidence'][0]['id'])
   if 'sourceExcerpt' in item:item['sourceExcerpt']+=' Do not use the product after October 1, 2026.'
  self.write_step(step)
  self.assertTrue(self.store.get(self.event)['selection']['reassessment']['required'])

 def test_added_unbound_reporting_does_not_invalidate_selected_evidence(self):
  self.event='demo-event-housing-funding-rule';record=self.approved()
  self.write_step(self.fixture['steps'][1])
  current=self.store.get(self.event)['selection']
  self.assertIsNone(current['reassessment']);self.assertEqual(current['approval']['id'],record['approval']['id'])

 def test_revision_mismatch_unavailability_and_voice_change_block(self):
  for cause in ('mismatch','unavailable','voice'):
   with self.subTest(cause=cause):
    self.write_step(self.step);record=self.select()
    step=copy.deepcopy(self.step)
    if cause=='mismatch':
     producer._items(step['reporting'])[0]['version']='different-revision'
     next(r for r in producer._items(step['candidates']) if r['id']==producer._items(step['reporting'])[0]['id'])['contentHash']='original-revision'
    elif cause=='unavailable':
     for item in producer._items(step['reporting']):item['sourceAvailable']=False
    if cause!='voice':self.write_step(step)
    profile=scriptdesk.editorial_voice()
    if cause=='voice':profile['version']='changed'
    with patch.object(scriptdesk,'editorial_voice',return_value=profile):
     changed=self.store.get(self.event)['selection']
    self.assertTrue(changed['reassessment']['required'])

 def test_supplemental_primary_evidence_preserves_intake_and_requires_review(self):
  record=self.select();original=copy.deepcopy(record['evidence'])
  source=self.primary()
  updated=self.act(record,'evidence',sources=[source])
  self.assertEqual(updated['evidence'][:-1],original);self.assertEqual(updated['evidence'][-1]['origin'],'reviewed-primary')
  self.assertNotEqual(updated['sourceRevision'],record['sourceRevision']);self.assertIsNone(updated['approval'])
  source['id']='invalid';source['url']='javascript:alert(1)'
  with self.assertRaises(ValueError):self.act(updated,'evidence',sources=[source])

 def test_primary_replacement_preserves_old_review_and_revokes_script_and_plan_approval(self):
  source=self.primary();record=self.act(self.select(),'evidence',sources=[source])
  draft=self.draft(record);draft['opening'][0]['evidence']=[{'id':source['id'],'quote':source['excerpt']}]
  approved=self.act(self.prepared(record,draft),'review',decision='approve',actor='Editor',note='Reviewed the primary bulletin.')
  archived={p:p.read_bytes() for p in (self.store._path(self.event,'live')/'revisions').glob('*.json')}
  revised={**source,'excerpt':'The agency expanded the affected product list and issued revised safety instructions for consumers.'}
  updated=self.act(approved,'evidence',sources=[revised])
  self.assertEqual(len(updated['evidence']),len(approved['evidence']))
  self.assertEqual(updated['evidence'][-1]['excerpt'],revised['excerpt'])
  self.assertEqual(updated['state'],'needs-reassessment');self.assertTrue(updated['reassessment']['required'])
  for key in ('approval','prepared','draftReview'):self.assertIsNone(updated[key])
  for path,before in archived.items():self.assertEqual(path.read_bytes(),before)
  refreshed=self.act(updated,'reassess',reason='The primary bulletin expanded its product list; the script must be reviewed against that revision.')
  with self.assertRaisesRegex(ValueError,'excerpt does not match'):self.act(refreshed,'save',draft=approved['draft'])

 def test_expired_primary_cannot_be_approved_or_renewed_by_reassessment_alone(self):
  source=self.primary();record=self.prepared(self.act(self.select(),'evidence',sources=[source]))
  self.now+=timedelta(hours=1,seconds=1)
  expired=self.store.get(self.event)['selection']
  self.assertTrue(expired['reassessment']['required']);self.assertIn('last hour',expired['reassessment']['reason'])
  with self.assertRaises(selection.Conflict):self.act(expired,'review',decision='approve',actor='Editor')
  with self.assertRaisesRegex(selection.Conflict,'source recheck'):self.act(expired,'reassess',reason='The editor requests another review of this story.')
  self.assertEqual(self.store.get(self.event)['selection']['evidence'][-1]['checkedAt'],source['checkedAt'])
  fresh={**source,'checkedAt':producer._stamp(self.now),'reviewNote':'The primary page was explicitly reread; its reviewed excerpt is unchanged.'}
  checked=self.act(expired,'evidence',sources=[fresh])
  self.assertTrue(checked['reassessment']['required']);self.assertIsNone(checked['approval']);self.assertIsNone(checked['prepared'])
  refreshed=self.act(checked,'reassess',reason='I reread the primary source and confirmed the same supporting excerpt and current news peg.')
  self.assertFalse(refreshed['reassessment']['required']);self.assertEqual(refreshed['evidence'][-1]['checkedAt'],fresh['checkedAt'])
  self.assertIn('unobserved remote-page change',refreshed['monitoring']['note'])

 def test_primary_review_cannot_replace_intake_or_use_an_expired_check(self):
  record=self.select();source=self.primary();source['id']=record['evidence'][0]['id']
  with self.assertRaisesRegex(ValueError,'intake evidence ID'):self.act(record,'evidence',sources=[source])
  source=self.primary();source['checkedAt']=producer._stamp(self.now-timedelta(hours=1,seconds=1))
  with self.assertRaisesRegex(ValueError,'last hour'):self.act(record,'evidence',sources=[source])
  self.assertEqual(self.store.get(self.event)['selection']['revision'],record['revision'])

 def test_primary_expiring_during_render_blocks_completion(self):
  import produce_film
  record=self.act(self.select(),'evidence',sources=[self.primary()])
  record=self.act(self.prepared(record),'review',decision='approve',actor='Editor',note='Primary source explicitly reread before this render.')
  entered=threading.Event();release=threading.Event()
  def render(packet,*,publish_result,completion_guard):
   self.assertFalse(publish_result);completion_guard();entered.set();release.wait(5);completion_guard();return {'id':'not-exposed'}
  with patch.object(pipeline,'production_lock',side_effect=lambda:nullcontext()),patch.object(produce_film,'produce',side_effect=render):
   self.act(record,'produce');self.assertTrue(entered.wait(5));worker=self.store.workers[record['id']]
   self.now+=timedelta(hours=1,seconds=1);release.set();worker.join(5)
  current=self.store.get(self.event)['selection']
  self.assertEqual(current['state'],'needs-reassessment');self.assertIsNone(current['approval'])
  self.assertIsNone(current['production']['result']);self.assertIn('last hour',current['reassessment']['reason'])

 def test_preparation_requires_exact_script_and_explicit_treatment_review(self):
  record=self.prepared(self.select());packet=copy.deepcopy(record['prepared']['packet'])
  packet['plan']['body']+=' Additional unsupported narration.'
  with self.assertRaisesRegex(ValueError,'exactly match'):self.act(record,'prepare',packet=packet)
  packet=copy.deepcopy(record['prepared']['packet']);del packet['plan']['review']['rights']
  with self.assertRaisesRegex(ValueError,'rights'):self.act(record,'prepare',packet=packet)
  brief=self.act(record,'select',productId='brief',whyNow='An immediate action is useful to the viewer.',note='')
  with self.assertRaisesRegex(ValueError,'The Brief'):self.act(brief,'prepare',packet=packet)

 def test_changed_source_during_worker_cannot_complete_or_publish(self):
  import produce_film
  record=self.approved();entered=threading.Event();release=threading.Event()
  def render(packet,*,publish_result,completion_guard):
   self.assertFalse(publish_result);self.assertEqual(packet['selection']['approval']['id'],record['approval']['id'])
   completion_guard();entered.set();self.assertTrue(release.wait(5));completion_guard()
   return {'id':'should-not-be-exposed'}
  with patch.object(pipeline,'production_lock',side_effect=lambda:nullcontext()),patch.object(produce_film,'produce',side_effect=render):
   self.act(record,'produce');self.assertTrue(entered.wait(5))
   self.write_step(self.fixture['steps'][1]);worker=self.store.workers[record['id']];release.set();worker.join(5)
  current=self.store.get(self.event)['selection']
  self.assertFalse(worker.is_alive());self.assertEqual(current['state'],'needs-reassessment')
  self.assertIsNone(current['approval']);self.assertIsNone(current['production']['result'])
  self.assertFalse((self.root/'dist/films.json').exists())

 def test_explicit_reject_during_worker_is_not_overwritten_by_completion(self):
  import produce_film
  record=self.approved();entered=threading.Event();release=threading.Event()
  def render(packet,*,publish_result,completion_guard):
   completion_guard();entered.set();release.wait(5);completion_guard();return {'id':'not-exposed'}
  with patch.object(pipeline,'production_lock',side_effect=lambda:nullcontext()),patch.object(produce_film,'produce',side_effect=render):
   running=self.act(record,'produce');self.assertTrue(entered.wait(5))
   self.act(running,'review',decision='reject',actor='Editor',note='Reject this treatment.')
   worker=self.store.workers[record['id']];release.set();worker.join(5)
  current=self.store.get(self.event)['selection']
  self.assertEqual(current['state'],'rejected');self.assertIsNone(current['approval']);self.assertIsNone(current['production']['result'])

 def test_successful_worker_returns_traceable_preview_without_publication(self):
  import produce_film
  record=self.approved();entered=threading.Event();release=threading.Event()
  def render(packet,*,publish_result,completion_guard):
   self.assertFalse(publish_result);completion_guard();entered.set();release.wait(5);completion_guard()
   return {'id':'finished-test','voices':{'warm':{'video':'assets/films/test/warm.mp4'}},'production':{'selection':packet['selection']}}
  with patch.object(pipeline,'production_lock',side_effect=lambda:nullcontext()),patch.object(produce_film,'produce',side_effect=render):
   self.act(record,'produce');self.assertTrue(entered.wait(5));worker=self.store.workers[record['id']];release.set();worker.join(5)
  current=self.store.get(self.event)['selection']
  self.assertEqual(current['state'],'complete');self.assertEqual(current['production']['state'],'complete')
  self.assertEqual(current['production']['result']['production']['selection']['sourceRevision'],record['sourceRevision'])
  self.assertEqual(current['production']['result']['production']['selection']['approval']['actor'],'Test editor')
  self.assertFalse((self.root/'dist/films.json').exists())

 def test_production_guard_recomputes_packet_hash_instead_of_trusting_metadata(self):
  record=self.approved();folder=self.store._path(self.event,'live')
  altered=copy.deepcopy(record);altered['prepared']['packet']['plan']['review']['rights']={'graphics':'Unreviewed changed terms'}
  pipeline.write_json(folder/'current.json',altered)
  with self.assertRaisesRegex(selection.Conflict,'approved revision'):self.store._guard(self.event,'live',record['approval']['id'])

 def test_model_passes_receive_carried_context_without_making_it_evidence(self):
  record=self.select();pack=self.store._pack(record);draft=self.draft(record)
  with patch.object(scriptdesk,'model_call',side_effect=[draft,draft]) as model:
   scriptdesk.generate(pack,self.root/'attempt','http://127.0.0.1:1234/v1','mock-model')
  for call in model.call_args_list:
   payload=json.loads(call.args[2][1]['content'])
   self.assertEqual(payload['editorialContext'],record['context']);self.assertEqual(payload['evidence'],record['evidence'])
   self.assertIn('not additional factual evidence',payload['contextPurpose'])
  metadata=json.loads((self.root/'attempt/generation.json').read_text(encoding='utf-8'))
  self.assertEqual(metadata['selectionId'],record['id']);self.assertEqual(metadata['editorialContext'],record['context'])


if __name__=='__main__':unittest.main()
