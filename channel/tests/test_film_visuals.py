import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'production'))
from film_visuals import chart_spec, reveal_progress, scene_schedule


class FilmVisualTests(unittest.TestCase):
    def test_bars_preserve_zero_and_reject_misleading_or_invalid_domain(self):
        self.assertEqual(chart_spec({'previousValue': 2, 'currentValue': 3.7})['baseline'], 0)
        for data in ({'previousValue': 2, 'currentValue': 3.7, 'baseline': 2},
                     {'previousValue': 2, 'currentValue': 3.7, 'ceiling': 3},
                     {'previousValue': 2, 'currentValue': float('nan')},
                     {'previousValue': 2, 'currentValue': '3.7'}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                chart_spec(data)

    def test_reveals_do_not_expose_a_fact_before_the_spoken_cue(self):
        self.assertEqual(reveal_progress(3.999, 4), 0)
        self.assertEqual(reveal_progress(4, 4), 0)
        self.assertGreater(reveal_progress(4.2, 4), 0)
        self.assertEqual(reveal_progress(5, 4), 1)

    def test_scene_clock_uses_actual_narration_not_equal_slides(self):
        packet = {'plan': {'beats': [{'kind': 'pce_comparison'}, {'kind': 'pce_mechanism'}]}}
        track = {'duration': 38, 'chapters': [{'kind': 'opening', 'start': .35, 'end': 12},
                 {'kind': 'story', 'start': 12, 'end': 29}, {'kind': 'closing', 'start': 29, 'end': 37}],
                 'visualCues': [{'start': 12.12, 'end': 20.83, 'beat': 0},
                                {'start': 20.83, 'end': 29, 'beat': 1}]}
        scenes = scene_schedule(packet, track)
        self.assertEqual([s['start'] for s in scenes], [0, 12.12, 20.83, 29])
        self.assertEqual(scenes[-1]['end'], 38)
        track['visualCues'][0]['reveals'] = [{'start': 20.84, 'reveal': 0}]
        with self.assertRaisesRegex(ValueError, 'outside'):
            scene_schedule(packet, track)


if __name__ == '__main__':
    unittest.main()
