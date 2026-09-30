import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
import film_audio as audio


class FilmAudioTests(unittest.TestCase):
 def test_quiet_sentence_edit_keeps_first_phoneme_and_every_spoken_sample(self):
  rate=24000;signal=np.zeros(36000);signal[:12000]=.21;signal[21600:]=-.18
  meta={'duration':1.5,'captions':[{'text':'First sentence.','start':0,'end':.55},{'text':'Next sentence.','start':.85,'end':1.5}],'wordTimings':[{'text':'sentence.','start':.1,'end':.5},{'text':'Next','start':.9,'end':1.3}]}
  result,edited=audio.compact_silence(signal,meta,{'minimumSentenceGap':.2,'minimumPhraseGap':.12})
  self.assertAlmostEqual(edited['duration'],1.3);self.assertEqual(edited['silenceEdits'][0]['gapAfter'],.2)
  np.testing.assert_array_equal(result[:12000],signal[:12000]);np.testing.assert_array_equal(result[-14400:],signal[-14400:])
  self.assertEqual(edited['wordTimings'][0],meta['wordTimings'][0]);self.assertAlmostEqual(edited['wordTimings'][1]['start'],.7)
  self.assertEqual(meta['wordTimings'][1]['start'],.9)
 def test_audible_breath_or_word_tail_is_never_removed_as_silence(self):
  signal=np.full(36000,.025);meta={'duration':1.5,'captions':[],'wordTimings':[{'text':'one.','start':0,'end':.5},{'text':'Two','start':.9,'end':1.5}]}
  result,edited=audio.compact_silence(signal,meta,{'minimumSentenceGap':.2,'minimumPhraseGap':.12})
  np.testing.assert_array_equal(result,signal);self.assertEqual(edited['silenceEdits'],[])
  with self.assertRaisesRegex(ValueError,'breathing'):audio.compact_silence(signal,meta,{'minimumSentenceGap':.05})
 def test_all_caption_and_word_boundaries_follow_an_edit_inside_a_sentence(self):
  signal=np.zeros(48000);signal[:10000]=.2;signal[18000:]=.2
  meta={'duration':2,'captions':[{'text':'A phrase, then another.','start':0,'end':2}],'wordTimings':[{'text':'phrase,','start':.1,'end':.4},{'text':'then','start':.8,'end':1.1}]}
  result,edited=audio.compact_silence(signal,meta,{'minimumSentenceGap':.2,'minimumPhraseGap':.12})
  self.assertAlmostEqual(edited['wordTimings'][1]['end']-edited['wordTimings'][1]['start'],.3)
  self.assertAlmostEqual(edited['captions'][0]['end'],len(result)/24000)
  self.assertEqual(edited['captions'][0]['text'],meta['captions'][0]['text'])
 def test_opening_accent_is_brief_and_score_is_finite_below_voice(self):
  rate=24000;seconds=5;time=np.arange(rate*seconds)/rate;narration=.2*np.sin(2*np.pi*180*time)
  track={'captions':[{'start':0,'end':4.8}],'wordTimings':[{'text':'A','start':0,'end':.4}]}
  signature=audio.editorial_score('signature',.28);self.assertEqual(float(np.max(np.abs(signature[round(.23*rate):]))),0)
  bed=audio.editorial_score('drift',seconds);handoff=audio.editorial_score('handoff',.28)
  mixed,evidence=audio.mix(narration,track,bed,signature,handoff)
  self.assertEqual(evidence['voiceGain'],1);self.assertEqual(evidence['narrationFadeSeconds'],0)
  self.assertGreater(evidence['firstWord']['voiceRmsDbfs']-evidence['firstWord']['accompanimentRmsDbfs'],18)
  self.assertLess(float(np.max(np.abs(mixed))),.94)
  clean,_=audio.mix(narration,track,np.zeros_like(bed),np.zeros_like(signature),np.zeros_like(handoff))
  np.testing.assert_array_equal(clean,narration)
  with self.assertRaisesRegex(ValueError,'without looping'):audio.mix(narration,track,bed[:-1],signature,handoff)


if __name__=='__main__':unittest.main()
