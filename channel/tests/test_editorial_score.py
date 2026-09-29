import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'production'))
from broadcast import editorial_score


class EditorialScoreTests(unittest.TestCase):
 def test_signature_is_present_immediately_and_has_a_clean_tail(self):
  for style,duration in [('signature',2.1),('handoff',.95),('bridge',1.5)]:
   signal=editorial_score(style,seconds=duration)
   self.assertGreater(float(np.sqrt(np.mean(signal[240:2400]**2))),.025)
   self.assertEqual(signal[0],0)
   self.assertLess(abs(float(signal[-1])),.00001)
   self.assertLess(float(np.max(np.abs(signal))),.5)
   self.assertTrue(np.isfinite(signal).all())

 def test_bridge_carries_the_full_transition_instead_of_ending_early(self):
  signal=editorial_score('bridge',seconds=1.5)
  self.assertGreater(float(np.sqrt(np.mean(signal[24000:30000]**2))),.02)
  self.assertLess(abs(float(signal[-1])),.00001)

 def test_bed_is_audible_from_first_sentence_and_has_no_loop_click(self):
  for style in ('drift','piano'):
   signal=editorial_score(style)
   self.assertGreater(float(np.sqrt(np.mean(signal[:24000]**2))),.06)
   self.assertLess(float(np.max(np.abs(signal))),.8)
   # A periodic waveform crosses zero at its normal slope, without an extra
   # boundary step; comparing the two steps detects a click independently of gain.
   self.assertLess(abs(float((signal[0]-signal[-1])-(signal[1]-signal[0]))),.001)
   self.assertTrue(np.isfinite(signal).all())


if __name__=='__main__':unittest.main()
