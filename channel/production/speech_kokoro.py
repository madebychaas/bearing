"""Kokoro narration on two CPU threads, with model-duration word timestamps.

Install kokoro-onnx==0.6.1 in the production environment. The explicit local
model files must already exist; this module never downloads or uploads anything.
Kokoro weights/voice styles: Apache-2.0. ONNX adapter: MIT. See configuration().
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import time
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import onnxruntime

ADAPTER_VERSION = "bearing-kokoro-sentence-words-v1"
MODEL_SOURCE = "https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1"
MODEL_CARD = "https://huggingface.co/hexgrad/Kokoro-82M"
VOICES = {
    "warm": {"voice": "af_heart", "name": "Heart", "speed": 1.0},
    "measured": {"voice": "am_michael", "name": "Michael", "speed": 1.0},
}
_CACHE = {}
_HASH_CACHE = {}


def _file_hash(path):
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    if key not in _HASH_CACHE:
        _HASH_CACHE[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return _HASH_CACHE[key]


def _models(model_dir=None):
    configured = os.environ.get("BEARING_KOKORO_MODEL_DIR")
    path = Path(configured or model_dir or Path(__file__).parent / "kokoro-models")
    # The existing production runtime supplies its legacy Piper directory.
    if not configured and path.name == "piper-models":
        path = path.with_name("kokoro-models")
    for filename in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        if not (path / filename).is_file():
            raise FileNotFoundError(f"Selected Kokoro provider requires local {path / filename}; no voice fallback")
    return path


def configuration(model_dir=None):
    models = _models(model_dir)
    result = {
        "provider": "kokoro-local-cpu", "adapterVersion": ADAPTER_VERSION,
        "engineVersion": importlib.metadata.version("kokoro-onnx"),
        "engineSource": "https://github.com/thewh1teagle/kokoro-onnx", "engineLicense": "MIT",
        "modelCard": MODEL_CARD, "modelSource": MODEL_SOURCE, "modelLicense": "Apache-2.0",
        "modelPath": str((models / "kokoro-v1.0.onnx").resolve()),
        "modelSha256": _file_hash(models / "kokoro-v1.0.onnx"),
        "voiceFileSha256": _file_hash(models / "voices-v1.0.bin"),
        "voiceLicense": "Apache-2.0 (Kokoro-82M voice styles)",
        "voiceCard": MODEL_CARD + "/blob/main/VOICES.md", "voices": VOICES,
        "phonemizer": "espeak-ng en-us via phonemizer",
        "phonemizerVersion": importlib.metadata.version("phonemizer"),
        "espeakLoaderVersion": importlib.metadata.version("espeakng-loader"),
        "inferenceProviders": ["CPUExecutionProvider"], "cpuThreads": 2,
    }
    # Machine paths are not a performance or cache identity.
    identity = {k: v for k, v in result.items() if k != "modelPath"}
    result["fingerprint"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return result


def _load(models):
    key = str(models.resolve())
    if key not in _CACHE:
        from kokoro_onnx import Kokoro
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        session = onnxruntime.InferenceSession(str(models / "kokoro-v1.0.onnx"),
            sess_options=options, providers=["CPUExecutionProvider"])
        engine = Kokoro.from_session(session, str(models / "voices-v1.0.bin"))
        if not engine.has_timings:
            raise ValueError("Reviewed Kokoro narration requires a model with duration output")
        _CACHE[key] = engine
    return _CACHE[key]


def _sentences(script):
    sentences = re.split(r"(?<=[.!?])\s+", script.strip())
    if " ".join(sentences) != " ".join(script.split()):
        raise ValueError("Sentence segmentation changed the narration text")
    return sentences


def _phoneme_words(engine, sentence):
    from phonemizer import phonemize
    from phonemizer.separator import Separator
    from kokoro_onnx.tokenizer import _espeak_lock
    # Word markers survive contextual grapheme-to-phoneme conversion, so the
    # model receives whole sentences instead of isolated word performances.
    with _espeak_lock:
        marked = phonemize(sentence.replace("’", "'"), "en-us", preserve_punctuation=True,
            with_stress=True, separator=Separator(word="|", phone="", syllable=""), strip=True)
    groups = [engine.tokenizer.known(group.strip()) for group in marked.split("|")]
    text_words = sentence.split()
    if len(groups) != len(text_words) or any(not group for group in groups):
        raise ValueError("Cannot map Kokoro phonemes one-to-one to source words; spell out numbers and abbreviations")
    return text_words, groups


def _word_timings(text_words, phoneme_groups, timings, offset):
    phonemes = " ".join(phoneme_groups)
    if "".join(t.phoneme for t in timings) != phonemes:
        raise ValueError("Kokoro duration output does not match the supplied phoneme sequence")
    result, cursor = [], 0
    for text, group in zip(text_words, phoneme_groups):
        selected = timings[cursor:cursor + len(group)]
        voiced = [t for t in selected if t.phoneme not in ".,;:!?—-()\"' "]
        if not voiced:
            raise ValueError("Word has no model-duration timestamps")
        result.append({"text": text, "start": round(offset + voiced[0].start, 5),
                       "end": round(offset + voiced[-1].end, 5)})
        cursor += len(group) + 1
    return result


def synthesize(script, voice_key, output_mp3, model_dir=None):
    if voice_key not in VOICES:
        raise ValueError(f"Unknown voice: {voice_key}")
    if not script or not script.strip():
        raise ValueError("Narration text is empty")
    output = Path(output_mp3).resolve()
    if any(path.exists() for path in (output, output.with_suffix(".wav"), output.with_suffix(".raw.wav"))):
        raise FileExistsError(f"Preserve retained narration; choose a new path: {output}")
    config = configuration(model_dir)
    engine = _load(_models(model_dir))
    output.parent.mkdir(parents=True, exist_ok=True)
    performance = VOICES[voice_key]
    chunks, captions, words, cursor, sample_rate = [], [], [], 0, 24000
    started = time.perf_counter()
    for sentence in _sentences(script):
        text_words, phonemes = _phoneme_words(engine, sentence)
        samples, rate, timings = engine.create_timed(" ".join(phonemes),
            voice=performance["voice"], speed=performance["speed"], lang="en-us",
            is_phonemes=True, trim=True, sentence_pause=.16, clause_pause=0)
        samples = np.asarray(samples, dtype=np.float32)
        if rate != sample_rate or not np.isfinite(samples).all() or not np.any(np.abs(samples) > .0001):
            raise RuntimeError("Kokoro returned invalid or silent speech")
        offset = cursor / sample_rate
        words.extend(_word_timings(text_words, phonemes, timings, offset))
        captions.append({"start": round(offset, 5), "end": round((cursor + len(samples)) / rate, 5), "text": sentence})
        chunks.append(samples)
        cursor += len(samples)
        # A clean sentence boundary, not a clause splice. Keep native cadence.
        gap = np.zeros(int(.16 * sample_rate), dtype=np.float32)
        chunks.append(gap)
        cursor += len(gap)
    inference_seconds = time.perf_counter() - started
    pcm = np.clip(np.concatenate(chunks) * 32767, -32767, 32767).astype("<i2")
    raw_wav, wav_path = output.with_suffix(".raw.wav"), output.with_suffix(".wav")
    with wave.open(str(raw_wav), "wb") as writer:
        writer.setnchannels(1); writer.setsampwidth(2); writer.setframerate(sample_rate)
        writer.writeframes(pcm.tobytes())
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-i", str(raw_wav),
        "-af", "loudnorm=I=-18:TP=-1.5:LRA=7", "-ar", str(sample_rate), "-c:a", "pcm_s16le", "-y", str(wav_path)],
        capture_output=True, check=True, timeout=90)
    subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-i", str(wav_path),
        "-c:a", "libmp3lame", "-b:a", "128k", "-y", str(output)], capture_output=True, check=True, timeout=90)
    decoded = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "info", "-xerror", "-i", str(output),
        "-f", "null", "-"], capture_output=True, check=True, timeout=90)
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", decoded.stderr.decode("utf-8", errors="replace"))
    if not match or output.stat().st_size < 1024:
        raise RuntimeError("Kokoro delivery failed encoded-media verification")
    duration = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
    if captions[-1]["end"] > duration + .1 or words[-1]["end"] > duration + .1:
        raise RuntimeError("Kokoro timestamps exceed the encoded delivery")
    metadata = {**config, "duration": duration, "captions": captions, "wordTimings": words,
        "voice": performance["voice"], "voiceName": performance["name"], "speed": performance["speed"],
        "scriptSha256": hashlib.sha256(script.encode("utf-8")).hexdigest(),
        "captionTiming": "whole-sentence synthesis; exact PCM sample-count boundaries",
        "wordTiming": "model phoneme duration tensor; contextual word markers; no equal-time interpolation",
        "wordTimingResolutionSeconds": .025, "sampleRate": sample_rate, "pcmDuration": cursor / sample_rate,
        "inferenceSeconds": round(inference_seconds, 3), "file": output.name, "bytes": output.stat().st_size,
        "sha256": _file_hash(output), "fullDecodePassed": True, "externalScriptUpload": False}
    output.with_suffix(".captions.json").write_text(json.dumps(captions, ensure_ascii=False, indent=2), "utf-8")
    output.with_suffix(".provenance.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), "utf-8")
    return metadata
