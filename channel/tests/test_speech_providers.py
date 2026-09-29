import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "production"))
import speech
import speech_kokoro


class NarrationProviderTests(unittest.TestCase):
    def test_selected_provider_never_falls_back_to_piper(self):
        with patch("speech_kokoro.synthesize", side_effect=FileNotFoundError("model missing")), \
             patch("speech._synthesize_piper") as legacy:
            with self.assertRaises(FileNotFoundError):
                speech.synthesize("A complete sentence.", "warm", "unused.mp3", provider="kokoro-local-cpu")
            legacy.assert_not_called()

    def test_explicit_provider_overrides_environment(self):
        with patch.dict(os.environ, {"BEARING_TTS_PROVIDER": "kokoro-local-cpu"}), \
             patch("speech._synthesize_piper", return_value={"provider": "piper-local-cpu"}) as legacy:
            self.assertEqual(speech.synthesize("Text.", "warm", "unused.mp3", provider="piper-local-cpu")["provider"], "piper-local-cpu")
            legacy.assert_called_once()
        with self.assertRaisesRegex(ValueError, "Unknown narration"):
            speech.synthesize("Text.", "warm", "unused.mp3", provider="missing-provider")

    def test_sentence_synthesis_preserves_clauses_and_text(self):
        source = "The idea: match training to needs, through internships and hands-on projects. The test comes next."
        sentences = speech_kokoro._sentences(source)
        self.assertEqual(len(sentences), 2)
        self.assertEqual(" ".join(sentences), source)

    def test_word_alignment_uses_model_durations_not_equal_slices(self):
        phonemes = "abc de."
        spans = [(0, .1), (.1, .4), (.4, .9), (.9, 1.1), (1.1, 1.3), (1.3, 1.7), (1.7, 2)]
        timings = [SimpleNamespace(phoneme=p, start=a, end=b) for p, (a, b) in zip(phonemes, spans)]
        aligned = speech_kokoro._word_timings(["Three", "two."], ["abc", "de."], timings, 4)
        self.assertEqual(aligned, [{"text": "Three", "start": 4, "end": 4.9}, {"text": "two.", "start": 5.1, "end": 5.7}])
        with self.assertRaisesRegex(ValueError, "does not match"):
            speech_kokoro._word_timings(["Three", "two."], ["abc", "df."], timings, 0)

    def test_missing_model_is_local_explicit_failure(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(FileNotFoundError, "no voice fallback"):
                speech_kokoro.configuration(directory)


if __name__ == "__main__":
    unittest.main()
