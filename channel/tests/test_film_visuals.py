import hashlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'production'))
from PIL import Image
from film_visuals import Film, HEIGHT, WIDTH, IVORY, NIGHT, PAPER, SCALE, TEAL, chart_spec, phrase_start, reveal_progress, reviewed_image_scenes, scene_schedule


class FilmVisualTests(unittest.TestCase):
    def loan_impact(self):
        roles = ['hinge', 'meaning', 'default', 'months', 'credit', 'car', 'home', 'consequence']
        packet = {'plan': {'title': 'Default help', 'summary': 'Requirements still apply',
                          'beats': [{'kind': 'service', 'reveals': [{'role': 'rehabilitation'},
                                    {'role': 'consolidation'}, {'role': 'documents'}, {'role': 'progress'}]}],
                          'closingReveals': [{'role': role} for role in roles]},
                  'visuals': {'service': {'title': 'Defaulted Loans Support Center',
                              'options': [{'label': 'Rehabilitation', 'role': 'rehabilitation'},
                                          {'label': 'Consolidation', 'role': 'consolidation'}],
                              'tools': [{'label': 'Upload documents', 'role': 'documents'},
                                        {'label': 'Track progress', 'role': 'progress'}]},
                              'closing': {'kind': 'default-impact', 'title': 'Applying is\nonly the start.',
                                          'text': 'Requirements still apply.'},
                              'defaultImpact': {'months': 9, 'qualifier': 'Generally, about'}}}
        track = {'duration': 44, 'chapters': [{'kind': 'opening', 'start': .3, 'end': 10},
                 {'kind': 'story', 'start': 10, 'end': 23}, {'kind': 'closing', 'start': 23, 'end': 43}],
                 'visualCues': [{'start': 10, 'end': 23, 'beat': 0, 'reveals': [
                     {'start': 15, 'reveal': 0}, {'start': 17, 'reveal': 1},
                     {'start': 19, 'reveal': 2}, {'start': 21, 'reveal': 3}]}],
                 'closingCues': [{'start': start, 'reveal': i} for i, start in enumerate(
                     [23, 27, 30, 32, 35, 38, 40, 41.5])]}
        return packet, track

    def full_frame_loan(self):
        packet, track = self.loan_impact()
        packet['visuals']['treatment'] = 'full-frame-v2'
        track['wordTimings'] = [
            {'text': text, 'start': start, 'end': start+.2}
            for text, start in [('Borrowers',.4), ('have',2), ('a',2.3), ('new',2.6),
                                ('way',2.9), ('online.',7.5), ('support',12), ('center',12.5)]]
        return packet, track

    def image_led_loan(self):
        packet, track = self.full_frame_loan()
        packet['visuals']['treatment'] = 'image-led-v3'
        track['wordTimings'].extend([
            {'text':'The','start':10,'end':10.2},
            {'text':'Treasury','start':10.25,'end':10.8},
            {'text':'compare','start':14.4,'end':14.8}])
        track['wordTimings'].sort(key=lambda word: word['start'])
        return packet, track

    def image_led_movie(self):
        packet, track = self.image_led_loan()
        with patch('film_visuals.reviewed_image_scenes', return_value={
                'opening': Image.new('RGB',(1920,1080),(21,41,61)),
                'body': Image.new('RGB',(1920,1080),(52,72,92))}):
            return Film(packet, track)

    def test_image_led_assets_are_local_large_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root/'approved.png'
            Image.new('RGB',(1280,720),NIGHT).save(path)
            approved = {'path':'approved.png','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            visuals = {'imageScenes':{role:dict(approved) for role in ('opening','body')},
                       'assets':[{**approved,'kind':'original','usageApproved':True}]}
            self.assertEqual(reviewed_image_scenes(visuals, root)['body'].size, (1280,720))
            visuals['assets'][0]['usageApproved'] = False
            with self.assertRaisesRegex(ValueError, 'linked to an approved'):
                reviewed_image_scenes(visuals, root)
            visuals['assets'][0]['usageApproved'] = True
            visuals['assets'][0]['sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'linked to an approved'):
                reviewed_image_scenes(visuals, root)
            visuals['assets'][0]['sha256'] = approved['sha256']
            visuals['imageScenes']['body']['sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                reviewed_image_scenes(visuals, root)
            visuals['imageScenes']['body'] = {**approved,'path':'../outside.png'}
            with self.assertRaisesRegex(ValueError, 'inside channel/dist'):
                reviewed_image_scenes(visuals, root)
            with self.assertRaisesRegex(ValueError, 'path and SHA-256'):
                reviewed_image_scenes({}, root)
            Image.new('RGB',(640,360),NIGHT).save(path)
            approved['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            visuals = {'imageScenes':{role:dict(approved) for role in ('opening','body')},
                       'assets':[{**approved,'kind':'original','usageApproved':True}]}
            with self.assertRaisesRegex(ValueError, 'too small'):
                reviewed_image_scenes(visuals, root)

    def test_image_led_title_builds_once_and_cuts_at_first_body_word(self):
        movie = self.image_led_movie()
        self.assertEqual(movie.picture_cues['body'], 10)
        self.assertEqual(movie.picture_cues['compare'], 14.4)
        # No preloaded title: the story starts on the image, then builds one
        # cohesive title. The attribution sentence immediately gets new picture.
        self.assertEqual(len(set(movie.frame(1).getdata())), 1)
        with patch('film_visuals._display') as display:
            movie.frame(8.5)
            self.assertEqual([call.args[1] for call in display.call_args_list], ['A way back.','Online.'])
        with patch('film_visuals._display') as display:
            self.assertEqual(movie.frame(10).getpixel((0,0)), (52,72,92))
            movie.frame(13.9)
            display.assert_not_called()
        packet, track = self.image_led_loan()
        track['wordTimings'] = [word for word in track['wordTimings'] if word['text'] != 'Treasury']
        with self.assertRaisesRegex(ValueError, 'spoken phrase'):
            Film(packet, track)

    def test_image_led_process_accumulates_and_holds_through_requirements(self):
        movie = self.image_led_movie()
        crop = lambda image, box: image.crop(tuple(round(v*SCALE) for v in box)).tobytes()
        fields = [(45,175,366,440),(450,175,810,440),(855,175,1220,440)]
        for time, count in ((16.5,1),(20.5,2),(22.9,3)):
            frame = movie.frame(time)
            for index, box in enumerate(fields):
                colors = set(frame.crop(tuple(round(v*SCALE) for v in box)).getdata())
                self.assertEqual(len(colors)>1, index<count)
        before = movie.frame(22.9)
        after = movie.frame(29.5)
        for box in fields:
            self.assertEqual(crop(before,box),crop(after,box))
        with patch('film_visuals._display') as display:
            movie.frame(28.5)
            labels = [call.args[1] for call in display.call_args_list]
        for required in ('Rehabilitation','Consolidation','Upload documents','Track progress','Meet the requirements'):
            self.assertIn(required, labels)
        self.assertNotIn('Requirements\nstill apply.', labels)

    def test_image_led_default_accumulates_context_without_cards_or_dissolves(self):
        movie = self.image_led_movie()
        fields = [(80,95,405,530),(492,150,772,482),(900,145,1215,330),(930,325,1195,520)]
        with patch('film_visuals.Image.blend', side_effect=AssertionError('No internal dissolve')):
            for time,count in ((34,1),(37,2),(39.5,3),(43,4)):
                frame = movie.frame(time)
                for index,box in enumerate(fields):
                    colors=set(frame.crop(tuple(round(v*SCALE) for v in box)).getdata())
                    self.assertEqual(len(colors)>1,index<count)
                bottom=frame.crop((0,round(HEIGHT*.82),WIDTH,HEIGHT))
                self.assertEqual(set(bottom.getdata()), {NIGHT})
        calendar = tuple(round(v*SCALE) for v in fields[0])
        self.assertEqual(movie.frame(34).crop(calendar).tobytes(),movie.frame(43).crop(calendar).tobytes())
        with patch('film_visuals._display') as display:
            movie.frame(43)
            labels = [call.args[1] for call in display.call_args_list]
        for required in ('Generally, about','9 months','Can hurt credit','Car loan','Apartment','Can be harder to get'):
            self.assertIn(required, labels)
        self.assertNotIn('Default.',labels)

    def test_full_frame_edits_use_real_word_clock_and_fail_closed_if_it_is_missing(self):
        packet, track = self.full_frame_loan()
        movie = Film(packet, track)
        self.assertEqual(movie.picture_cues['payoff'], 2.3)
        self.assertEqual(movie.picture_cues['online'], 7.5)
        self.assertEqual(movie.picture_cues['center'], 12)
        self.assertEqual(movie.picture_cues['documents'], 19)
        self.assertEqual(movie.picture_cues['consequence'], 41.5)
        track['wordTimings'][5]['start'] = 8.4
        self.assertEqual(Film(packet, track).picture_cues['online'], 8.4)
        track['wordTimings'].pop(5)
        with self.assertRaisesRegex(ValueError, 'spoken phrase'):
            Film(packet, track)
        self.assertEqual(phrase_start({'duration':10,'wordTimings':[
            {'text':'Online.','start':2}]}, 'online'), 2)

    def test_full_frame_has_no_template_furniture_or_cross_dissolves(self):
        packet, track = self.full_frame_loan()
        # These legacy fields must never leak onto the opted-in video canvas.
        packet['visuals']['eyebrow'] = 'FORBIDDEN EYEBROW'
        packet['visuals']['credit'] = 'FORBIDDEN SOURCE FOOTER'
        movie = Film(packet, track)
        with patch('film_visuals.Image.blend', side_effect=AssertionError('No full-frame cross dissolve')):
            for time in (.8, 2.8, 8, 12.5, 15.5, 17.5, 19.5, 21.5,
                         23.5, 27.5, 30.5, 32.5, 35.5, 38.5, 40.5, 42.5):
                frame = movie.frame(time)
                self.assertEqual(frame.size, (1920,1080))
                # Real estate remains available for optional native CC/controls.
                bottom=frame.crop((0, round(HEIGHT*.82), WIDTH, HEIGHT))
                self.assertEqual(len(set(bottom.getdata())),1)
                self.assertIn(bottom.getpixel((0,0)), (NIGHT,PAPER))
        with patch('film_visuals._text') as small_text:
            for time in (2,16,20,25,34,43):
                movie.frame(time)
            small_text.assert_not_called()

    def test_full_frame_uses_distinct_service_pictures_and_preserves_rehabilitation_scope(self):
        packet, track = self.full_frame_loan()
        movie = Film(packet,track)
        def visible_copy(time):
            with patch('film_visuals._display') as display:
                movie.frame(time)
                return [call.args[1] for call in display.call_args_list
                        if len(call.args)<8 or call.args[7]>0]
        self.assertEqual(visible_copy(13), ['Defaulted Loans\nSupport Center'])
        self.assertEqual(visible_copy(16), ['Rehabilitation'])
        self.assertEqual(visible_copy(18), ['Rehabilitation','Consolidation'])
        self.assertEqual(visible_copy(20), ['Rehabilitation','Upload\ndocuments.'])
        self.assertEqual(visible_copy(22), ['Rehabilitation','Track\nprogress.'])

    def test_full_frame_consequences_wait_for_reference_and_remain_qualified(self):
        packet, track = self.full_frame_loan()
        movie = Film(packet,track)
        def visible_copy(time):
            with patch('film_visuals._display') as display:
                movie.frame(time)
                return [call.args[1] for call in display.call_args_list
                        if len(call.args)<8 or call.args[7]>0]
        self.assertEqual(visible_copy(31), ['Default.'])
        self.assertEqual(visible_copy(34), ['Generally, about','9','months','of missed payments'])
        self.assertEqual(visible_copy(36), ['Can hurt\ncredit.'])
        self.assertEqual(visible_copy(39), ['Can hurt credit.','Car loan'])
        self.assertEqual(visible_copy(40.8), ['Can hurt credit.','Car loan','Apartment'])
        self.assertEqual(visible_copy(43), ['Can be harder to get.','Car loan','Apartment'])
        # No fictional score or completed application appears anywhere.
        self.assertGreater(len(set(movie.frame(38.3).getdata())),1)
        self.assertNotEqual(movie.frame(38.1).tobytes(),movie.frame(38.4).tobytes())

    def test_loan_closing_changes_composition_at_spoken_definition(self):
        packet, track = self.loan_impact()
        movie = Film(packet, track)
        self.assertEqual([s['kind'] for s in movie.scenes], ['headline', 'service', 'close', 'default-impact'])
        self.assertEqual(movie.scenes[-2]['end'], 30)
        self.assertEqual(movie.scenes[-1]['start'], 30)
        self.assertEqual(movie.scenes[-1]['end'], 44)
        self.assertEqual([c['reveal'] for c in movie.scenes[-1]['reveals']], [2, 3, 4, 5, 6, 7])

    def test_loan_timeline_and_consequences_wait_for_voice_and_hold(self):
        packet, track = self.loan_impact()
        movie = Film(packet, track)
        region = lambda image, box: set(image.crop(tuple(round(v*SCALE) for v in box)).getdata())
        months, credit, car, home, qualifier = ((80, 244, 345, 445), (469, 244, 769, 444),
                                               (826, 250, 1187, 317), (826, 338, 1187, 405),
                                               (826, 425, 1187, 458))
        self.assertEqual(region(movie.frame(31.7), months), {IVORY})
        month_frame = movie.frame(34)
        self.assertGreater(len(region(month_frame, months)), 1)
        self.assertEqual(region(month_frame, credit), {IVORY})
        credit_frame = movie.frame(37)
        self.assertGreater(len(region(credit_frame, credit)), 1)
        self.assertEqual(region(credit_frame, car), {IVORY})
        car_frame = movie.frame(39)
        self.assertGreater(len(region(car_frame, car)), 1)
        self.assertEqual(region(car_frame, home), {IVORY})
        self.assertEqual(region(movie.frame(41.3), qualifier), {IVORY})
        completed = movie.frame(43)
        for box in (months, credit, car, home, qualifier):
            self.assertGreater(len(region(completed, box)), 1)
        self.assertEqual(region(month_frame, months), region(completed, months))
        self.assertEqual(region(completed, (0, 480, 1280, 720)), {IVORY})

    def test_loan_impact_rejects_missing_cues_and_unqualified_definition(self):
        packet, track = self.loan_impact()
        track['closingCues'].pop(3)
        with self.assertRaisesRegex(ValueError, 'eight authored'):
            Film(packet, track)
        packet, track = self.loan_impact()
        packet['visuals']['defaultImpact']['qualifier'] = 'Always after'
        with self.assertRaisesRegex(ValueError, 'qualified nine-month'):
            Film(packet, track).frame(43)

    def test_service_choices_reveal_left_to_right_and_hold_during_tool_explanation(self):
        packet={'plan':{'title':'Default help','summary':'Requirements still apply','beats':[{'kind':'service','reveals':[{'role':'rehabilitation'},{'role':'consolidation'},{'role':'documents'},{'role':'progress'}]}]},
                'visuals':{'service':{'title':'Defaulted Loans Support Center','options':[{'label':'Rehabilitation','role':'rehabilitation'},{'label':'Consolidation','role':'consolidation'}],
                           'tools':[{'label':'Upload documents','role':'documents'},{'label':'Track progress','role':'progress'}]}}}
        track={'duration':30,'chapters':[{'kind':'opening','start':.3,'end':7},{'kind':'story','start':7,'end':20},{'kind':'closing','start':20,'end':29}],
               'visualCues':[{'start':7,'end':20,'beat':0,'reveals':[{'start':12,'reveal':0},{'start':14,'reveal':1},{'start':16,'reveal':2},{'start':18,'reveal':3}]}]}
        movie=Film(packet,track)
        self.assertIsNone(movie.chart)
        def colors(image,x):
            region=image.crop(tuple(round(v*SCALE) for v in (x,260,x+540,359)))
            return set(region.getdata())
        initial=movie.frame(11)
        self.assertEqual(colors(initial,82),{IVORY});self.assertEqual(colors(initial,650),{IVORY})
        first=movie.frame(13)
        self.assertGreater(len(colors(first,82)),1);self.assertEqual(colors(first,650),{IVORY})
        later=movie.frame(19)
        self.assertEqual(colors(first,82),colors(later,82));self.assertGreater(len(colors(later,650)),1)
        self.assertEqual([s['kind'] for s in movie.scenes],['headline','service','close'])

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
