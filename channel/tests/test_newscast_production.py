import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'production'))
import newscast_production as adapter


class NewscastProductionTests(unittest.TestCase):
    def job(self):
        report={'id':'report','url':'https://example.com/report','title':'Costs change','excerpt':'New costs','publishedAt':'2026-10-01T12:00:00Z'}
        return {'id':'cast-1','stories':[{'id':'event-a','revision':'a','evidence':[report]},{'id':'event-b','revision':'b','evidence':[report]}],
                'preferences':{'voice':'warm','pace':'natural','music':'quiet'}}

    def handoff(self):
        desk=Mock()
        record={'approval':{'id':'approved'},'prepared':{'packet':{'story':{'id':'source-story'}}},
                'evidence':[{'id':'report','origin':'intake','url':'https://example.com/report','headline':'Costs change','excerpt':'New costs','publishedTime':'2026-10-01T12:00:00Z'}]}
        desk.get.return_value={'selection':record}
        desk._guard.return_value=record
        desk._lineage.return_value={'approval':{'id':'approved'}}
        return desk

    def story(self):
        return {'id':'finished','title':'Costs change','production':{},'voices':{'warm':{'duration':30}}}

    def test_missing_creative_connection_cannot_render_or_claim_readiness(self):
        with patch('produce_film.produce') as produce:
            with self.assertRaises(adapter.NeedsProductionConnection):
                adapter.run_job(self.job(),Mock(),Mock(),Path('.'))
            handoff=self.handoff();handoff.get.return_value={'selection':None}
            with self.assertRaises(adapter.NeedsProductionConnection):
                adapter.run_job(self.job(),Mock(),Mock(),Path('.'),handoff=handoff)
            produce.assert_not_called()
        self.assertFalse(adapter.capabilities(Path('.'))['generationReady'])

    def test_entire_cast_preflights_before_rendering_and_no_approval_is_manufactured(self):
        desk=self.handoff();ready=desk.get.return_value
        desk.get.side_effect=[ready,{'selection':{'approval':None}}]
        with patch('produce_film.produce') as produce:
            with self.assertRaises(adapter.NeedsProductionConnection):
                adapter.run_job(self.job(),Mock(),Mock(),Path('.'),handoff=desk)
            produce.assert_not_called()
        desk.mutate.assert_not_called()

    def test_native_production_keeps_private_order_and_real_progress(self):
        report=Mock();guard=Mock();desk=self.handoff();original=self.story()
        def produce(packet,**kwargs):
            self.assertFalse(kwargs['publish_result'])
            kwargs['completion_guard']()
            kwargs['on_stage']('edit_script')
            return original
        with patch('produce_film.produce',side_effect=produce):
            result=adapter.run_job(self.job(),report,guard,Path('.'),handoff=desk)
        self.assertEqual([s['production']['newscast']['eventId'] for s in result['stories']],['event-a','event-b'])
        self.assertEqual(result['duration'],61.5)
        self.assertNotIn('newscast',original['production'])
        self.assertTrue(any(call.args[0]=='voicing' for call in report.call_args_list))
        self.assertGreater(guard.call_count,3)

    def test_revoked_approval_stops_before_render(self):
        desk=self.handoff();desk._guard.side_effect=ValueError('Approval changed')
        with patch('produce_film.produce') as produce:
            with self.assertRaisesRegex(ValueError,'Approval changed'):
                adapter.run_job(self.job(),Mock(),Mock(),Path('.'),handoff=desk)
            produce.assert_not_called()

    def test_new_report_cannot_reuse_approval_for_same_event(self):
        job=self.job();job['stories'][0]['evidence'][0]['id']='new-report'
        with patch('produce_film.produce') as produce:
            with self.assertRaisesRegex(adapter.NeedsProductionConnection,'newer reporting'):
                adapter.run_job(job,Mock(),Mock(),Path('.'),handoff=self.handoff())
            produce.assert_not_called()

    def test_final_gate_rechecks_evidence_and_exact_lineage(self):
        desk=self.handoff();lineage={'approval':{'id':'approved'},'scriptRevision':'exact'}
        desk._lineage.return_value=lineage
        story=self.story();story['production']['selection']=copy.deepcopy(lineage)
        result={'stories':[story,story]}
        adapter.validate_ready(self.job(),result,Mock(),Path('.'),handoff=desk)
        desk._lineage.return_value={**lineage,'scriptRevision':'changed'}
        with self.assertRaisesRegex(adapter.NeedsProductionConnection,'no longer matches'):
            adapter.validate_ready(self.job(),result,Mock(),Path('.'),handoff=desk)

    def test_slow_pace_changes_estimate_not_approved_packet(self):
        job=self.job();job['preferences']['pace']='unhurried';desk=self.handoff()
        before=copy.deepcopy(desk._guard.return_value)
        with patch('produce_film.produce',return_value=self.story()):
            result=adapter.run_job(job,Mock(),Mock(),Path('.'),handoff=desk)
        self.assertAlmostEqual(result['duration'],round(60/.92+1.5,3))
        self.assertEqual(before,desk._guard.return_value)


if __name__=='__main__':unittest.main()
