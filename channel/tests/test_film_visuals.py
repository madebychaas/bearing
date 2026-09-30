import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'production'))
from film_visuals import Film, IVORY, SCALE, TEAL, chart_spec, reveal_progress, scene_schedule


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

    def test_current_bar_reads_left_before_reference_reveals_right(self):
        packet = {'plan': {'title': 'Test', 'summary': 'Test', 'beats': [
            {'kind': 'pce_mechanism'},
            {'kind': 'pce_comparison', 'reveals': [{'role': 'current'}, {'role': 'goal'}]}]},
            'visuals': {'currentValue': 3.4, 'previousValue': 2, 'ceiling': 4,
                        'currentLabel': 'August', 'previousLabel': 'Fed goal'}}
        track = {'duration': 20, 'chapters': [
            {'kind': 'opening', 'start': .4, 'end': 4},
            {'kind': 'story', 'start': 4, 'end': 16},
            {'kind': 'closing', 'start': 16, 'end': 20}],
            'visualCues': [{'start': 4, 'end': 9, 'beat': 0},
                          {'start': 9, 'end': 16, 'beat': 1,
                           'reveals': [{'start': 10, 'reveal': 0}, {'start': 13, 'reveal': 1}]}]}
        movie = Film(packet, track)
        self.assertEqual([s['kind'] for s in movie.scenes],
                         ['headline', 'mechanism', 'comparison', 'close'])
        pixel = lambda image, x, y: image.getpixel((round(x*SCALE), round(y*SCALE)))
        current_only = movie.frame(11.5)
        self.assertEqual(pixel(current_only, 345, 365), TEAL)
        self.assertEqual(pixel(current_only, 790, 365), IVORY)
        both = movie.frame(14)
        self.assertEqual(pixel(both, 345, 365), TEAL)
        self.assertEqual(pixel(both, 790, 365), (144, 164, 151))
        # Both bars end at the shared zero baseline; no shortened-axis illusion.
        self.assertEqual(pixel(both, 345, 425), IVORY)
        self.assertEqual(pixel(both, 790, 425), IVORY)

    def test_evidence_holds_until_the_spoken_closing_question(self):
        packet = {'plan': {'beats': [{'kind': 'pce_mechanism'}, {'kind': 'pce_comparison'}],
                           'closingReveals': [{'role': 'hinge'}, {'role': 'meaning'}]}}
        track = {'duration': 38, 'chapters': [
            {'kind': 'opening', 'start': .35, 'end': 5},
            {'kind': 'story', 'start': 5, 'end': 29},
            {'kind': 'closing', 'start': 29, 'end': 37}],
            'visualCues': [{'start': 5.12, 'end': 18, 'beat': 0},
                          {'start': 18, 'end': 29, 'beat': 1}],
            'closingCues': [{'start': 30.5, 'reveal': 0}, {'start': 34, 'reveal': 1}]}
        original_chapters = [dict(chapter) for chapter in track['chapters']]
        scenes = scene_schedule(packet, track)
        self.assertEqual(scenes[-2]['end'], 30.5)
        self.assertEqual(scenes[-1]['start'], 30.5)
        self.assertEqual(track['chapters'], original_chapters)
        self.assertEqual(scenes[-1]['end'], track['duration'])
        track['closingCues'] = []
        self.assertEqual(scene_schedule(packet, track)[-1]['start'], 29)
        track['closingCues'] = [{'start': 30.5, 'reveal': 0}, {'start': 30.4, 'reveal': 1}]
        with self.assertRaises(ValueError):
            scene_schedule(packet, track)
        track['closingCues'] = [{'start': 37.5, 'reveal': 0}]
        with self.assertRaisesRegex(ValueError, 'closing chapter'):
            scene_schedule(packet, track)


if __name__ == '__main__':
    unittest.main()
