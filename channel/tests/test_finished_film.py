import sys,tempfile,unittest
from unittest.mock import patch
import numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import produce_film as film


class FinishedFilmTests(unittest.TestCase):
 def clips(self,seconds=9):
  return {phase:(Path('unused.wav'),{'duration':seconds,'voiceName':'Michael','captions':[{'text':text,'start':0,'end':seconds-.2}],'wordTimings':[{'text':word,'start':i*.5,'end':i*.5+.4} for i,word in enumerate(text.split())]}) for phase,text in [('opening','The new development matters'),('story','Prices rose while income lagged'),('closing','Watch the next spending report')]}
 def plan(self):
  return {'maxDuration':45,'narrationRate':.93,'beats':[{'kind':'pce_comparison','cue':'Prices rose'},{'kind':'pce_mechanism','cue':'income lagged'}]}
 def test_performance_timing_and_chapters_stay_ordered(self):
  track,placements=film.build_track(self.clips(),self.plan())
  self.assertLess(track['captions'][0]['start'],.6)
  self.assertEqual(track['chapters'][-1]['end'],track['duration'])
  self.assertEqual(track['visualCues'][0]['start'],track['chapters'][2]['start']+.1)
  self.assertLess(track['visualCues'][0]['end'],track['chapters'][2]['end'])
  self.assertEqual(len(placements),3)
 def test_duration_hold_precedes_render_or_publication(self):
  with self.assertRaisesRegex(ValueError,'duration budget'):film.build_track(self.clips(16),self.plan())
 def test_word_and_caption_times_follow_per_story_tempo_without_mutating_source(self):
  meta={'captions':[{'text':'Today','start':.1,'end':1.2}],'wordTimings':[{'text':'Today','start':.2,'end':1.1}]}
  output=film.scale_metadata(meta,.93,2)
  self.assertAlmostEqual(output['wordTimings'][0]['start'],.2/.93,places=4)
  self.assertEqual(meta['wordTimings'][0]['start'],.2)
  with self.assertRaisesRegex(ValueError,'exceeds'):film.scale_metadata(meta,.93,.5)
 def test_subtitles_preserve_millisecond_and_hour_boundaries(self):
  self.assertEqual(film.subtitle_time(59.9996),'00:01:00,000')
  self.assertEqual(film.subtitle_time(3601.023),'01:00:01,023')
 def test_empty_or_incomplete_cache_is_never_a_complete_film(self):
  self.assertFalse(film.cache_valid({}))
  self.assertFalse(film.cache_valid({'story':{'id':'x'},'assets':[]}))
 def test_editorial_pause_preserves_speech_and_shifts_later_word_and_caption_cues(self):
  samples=np.zeros(72000);samples[:24000]=.2;samples[28800:]=.3
  meta={'duration':3,'captions':[{'text':'Two percent goal.','start':0,'end':1},{'text':'Income rose.','start':1.2,'end':3}],'wordTimings':[{'text':'goal','start':.7,'end':.95},{'text':'Income','start':1.21,'end':1.5}]}
  output,updated=film.insert_narration_pauses(samples,meta,[{'after':'two percent goal.','seconds':1.7}])
  self.assertEqual(len(output),len(samples)+40800)
  self.assertEqual(updated['captions'][0],meta['captions'][0]);self.assertEqual(updated['captions'][1]['start'],2.9)
  self.assertAlmostEqual(updated['wordTimings'][1]['start'],2.91);self.assertEqual(meta['captions'][1]['start'],1.2)
  self.assertTrue(np.array_equal(output[:24000],samples[:24000]));self.assertTrue(np.array_equal(output[-43200:],samples[-43200:]))
  with self.assertRaisesRegex(ValueError,'audible speech'):film.insert_narration_pauses(np.ones(72000)*.2,meta,[{'after':'two percent goal','seconds':1.7}])
  with self.assertRaisesRegex(ValueError,'complete sentence'):film.insert_narration_pauses(samples,meta,[{'after':'Two percent','seconds':1.7}])
 def test_readable_captions_preserve_words_punctuation_and_actual_word_boundaries(self):
  text="Today's federal report puts annual price growth at three point four percent, above the Fed's two percent goal."
  words=[{'text':word,'start':i*.2,'end':i*.2+.15} for i,word in enumerate(text.split())]
  captions=film.readable_captions([{'text':text,'start':0,'end':4}],words)
  self.assertEqual(' '.join(c['text'] for c in captions),text)
  self.assertTrue(all(len(c['text'])<=52 and len(c['text'].split())<=8 for c in captions))
  self.assertTrue(all(c['start'] in [w['start'] for w in words] and c['end'] in [w['end'] for w in words] for c in captions))
  with self.assertRaisesRegex(ValueError,'do not match'):film.readable_captions([{'text':text,'start':0,'end':4}],words[:-1])
 def test_final_delivery_is_atomic_and_recoverable_after_a_failed_replace(self):
  with tempfile.TemporaryDirectory() as directory:
   source=Path(directory)/'staged.mp4';source.write_bytes(b'complete verified movie');target=Path(directory)/'published.mp4';digest=film.broadcast.file_hash(source)
   with patch.object(film.os,'replace',side_effect=OSError('interrupted')):
    with self.assertRaises(OSError):film.deliver_asset(source,target,digest)
   self.assertFalse(target.exists());self.assertFalse(list(Path(directory).glob('*.tmp')))
   film.deliver_asset(source,target,digest);self.assertEqual(target.read_bytes(),source.read_bytes())
   source.write_bytes(b'different movie')
   with self.assertRaisesRegex(ValueError,'Immutable'):film.deliver_asset(source,target,film.broadcast.file_hash(source))
   self.assertEqual(target.read_bytes(),b'complete verified movie')


if __name__=='__main__':unittest.main()
