"""Replaceable local CPU narration. No networking or implicit model downloads.

Public API: synthesize(script, voice_key, output_mp3, model_dir=None, *, provider=None)
Explicit providers: piper-local-cpu (legacy), kokoro-local-cpu (reviewed narration).
An unavailable selected provider fails closed; it never silently changes voices.
Legacy dependencies: piper-tts==1.8.0, onnxruntime==1.30.0, numpy, imageio-ffmpeg.
Kokoro adds kokoro-onnx==0.6.1; see speech_kokoro.py for explicit local setup.
Piper models: argument, CURRENT_PIPER_MODEL_DIR, or sibling piper-models.
Piper captions use exact phrase PCM boundaries; Kokoro also returns
duration-tensor word timings while synthesizing complete sentences.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import onnxruntime

VOICES = {
    "warm": {"model": "en_US-ljspeech-medium", "name": "LJ Speech",
             "modelCard": "https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/ljspeech/medium/MODEL_CARD"},
    "measured": {"model": "en_US-bryce-medium", "name": "Bryce",
                 "modelCard": "https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/bryce/medium/MODEL_CARD"},
}
_CACHE = {}


def _phrases(script):
    # Respect existing clause punctuation; preserve every original word.
    clauses = re.split(r"(?<=[,;:.!?])\s+", script.strip())
    result = []
    for clause in clauses:
        words = clause.split()
        while len(words) > 14:
            break_at = next((n for n in range(11, 5, -1)
                             if words[n].lower() in {"and", "but", "where", "while", "which", "that", "with", "from"}), 11)
            result.append(" ".join(words[:break_at]))
            words = words[break_at:]
        if words:
            result.append(" ".join(words))
    # Tiny clauses attach to their neighbor, keeping their original punctuation.
    merged = []
    for phrase in result:
        if merged and len(phrase.split()) < 4 and len(merged[-1].split()) + len(phrase.split()) <= 14:
            merged[-1] += " " + phrase
        else:
            merged.append(phrase)
    if " ".join(merged) != " ".join(script.split()):
        raise ValueError("Phrase segmentation changed source text")
    return merged


def _load_voice(model_path):
    from piper import PiperVoice
    from piper.config import PiperConfig
    key = str(model_path.resolve())
    if key not in _CACHE:
        config_path = Path(str(model_path) + ".json")
        if not model_path.is_file() or not config_path.is_file():
            raise FileNotFoundError(f"Local Piper model and config required: {model_path}")
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        session = onnxruntime.InferenceSession(str(model_path), sess_options=options,
                                               providers=["CPUExecutionProvider"])
        config = PiperConfig.from_dict(json.loads(config_path.read_text("utf-8")))
        _CACHE[key] = PiperVoice(session=session, config=config)
    return _CACHE[key]


def synthesize(script, voice_key, output_mp3, model_dir=None, *, provider=None):
    selected = provider or os.environ.get("BEARING_TTS_PROVIDER") or "piper-local-cpu"
    if selected == "kokoro-local-cpu":
        from speech_kokoro import synthesize as render_kokoro
        return render_kokoro(script, voice_key, output_mp3, model_dir)
    if selected != "piper-local-cpu":
        raise ValueError(f"Unknown narration provider: {selected}")
    return _synthesize_piper(script, voice_key, output_mp3, model_dir)


def provider_fingerprint(provider=None, model_dir=None):
    """Bind cached narration to its actual engine, voice settings and model files."""
    selected = provider or os.environ.get("BEARING_TTS_PROVIDER") or "piper-local-cpu"
    if selected == "kokoro-local-cpu":
        from speech_kokoro import configuration
        return configuration(model_dir)["fingerprint"]
    if selected != "piper-local-cpu":
        raise ValueError(f"Unknown narration provider: {selected}")
    return "piper-local-cpu-legacy-1.06"


def _synthesize_piper(script, voice_key, output_mp3, model_dir=None):
    """Render MP3/WAV and exact phrase captions locally and return asset metadata."""
    from piper.config import SynthesisConfig
    if voice_key not in VOICES:
        raise ValueError(f"Unknown voice: {voice_key}")
    if not script or not script.strip():
        raise ValueError("Narration text is empty")
    output = Path(output_mp3).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(f"Preserve retained narration; choose a new path: {output}")
    models = Path(model_dir or os.environ.get("CURRENT_PIPER_MODEL_DIR") or Path(__file__).parent / "piper-models")
    model_path = models / (VOICES[voice_key]["model"] + ".onnx")
    voice = _load_voice(model_path)
    sample_rate = voice.config.sample_rate
    config = SynthesisConfig(length_scale=1.06, noise_scale=.667, noise_w_scale=.8,
                             normalize_audio=False)
    segments, captions, cursor = [], [], 0
    phrases = _phrases(script)
    for phrase in phrases:
        pieces = [chunk.audio_float_array for chunk in voice.synthesize(phrase, syn_config=config)]
        if not pieces:
            raise RuntimeError("Piper returned no speech")
        segment = np.concatenate(pieces).astype(np.float32)
        # Remove only outside silence, retaining 70 ms of breath/attack and 110 ms tail.
        active = np.flatnonzero(np.abs(segment) > 10**(-55/20))
        if not len(active):
            raise RuntimeError("Piper returned silent speech")
        start = max(0, int(active[0])-int(.07*sample_rate))
        end = min(len(segment), int(active[-1])+int(.11*sample_rate))
        segment = segment[start:end]
        # 3 ms boundary ramps avoid hard sample discontinuities.
        ramp = min(int(.003*sample_rate), len(segment)//2)
        segment[:ramp] *= np.linspace(0, 1, ramp)
        segment[-ramp:] *= np.linspace(1, 0, ramp)
        captions.append({"start": round(cursor/sample_rate, 5),
                         "end": round((cursor+len(segment))/sample_rate, 5), "text": phrase})
        segments.append(segment)
        cursor += len(segment)
        gap = int((.21 if re.search(r"[.!?]$", phrase) else .07)*sample_rate)
        segments.append(np.zeros(gap, dtype=np.float32))
        cursor += gap
    audio = np.concatenate(segments)
    pcm = np.clip(audio*32767, -32767, 32767).astype("<i2")
    raw_wav = output.with_suffix(".raw.wav")
    wav_path = output.with_suffix(".wav")
    with wave.open(str(raw_wav), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(pcm.tobytes())
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    # One-pass loudness normalization changes level, not the timing or word order.
    command = [ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-i", str(raw_wav),
               "-af", "loudnorm=I=-18:TP=-1.5:LRA=7", "-ar", str(sample_rate),
               "-c:a", "pcm_s16le", "-y", str(wav_path)]
    subprocess.run(command, capture_output=True, check=True)
    subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-i", str(wav_path),
                    "-c:a", "libmp3lame", "-b:a", "128k", "-y", str(output)], capture_output=True, check=True)
    probe = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-v", "info", "-i", str(output),
                            "-f", "null", "-"], capture_output=True, check=True)
    log = probe.stderr.decode("utf-8", errors="replace")
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", log)
    if not match or output.stat().st_size < 1024:
        raise RuntimeError("Produced narration failed media validation")
    duration = int(match[1])*3600 + int(match[2])*60 + float(match[3])
    if captions[-1]["end"] > duration+.1:
        raise RuntimeError("Caption timing exceeds encoded audio duration")
    metadata = {"duration": duration, "captions": captions, "provider": "piper-local-cpu",
                "voice": VOICES[voice_key]["model"], "voiceName": VOICES[voice_key]["name"],
                "engineVersion": importlib.metadata.version("piper-tts"),
                "engineSource": "https://github.com/OHF-Voice/piper1-gpl", "engineLicense": "GPL-3.0",
                "modelCard": VOICES[voice_key]["modelCard"], "modelDatasetLicense": "public domain per model card",
                "modelPath": str(model_path.resolve()), "modelSha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                "scriptSha256": hashlib.sha256(script.encode("utf-8")).hexdigest(),
                "captionTiming": "phrase-aligned: independently synthesized phrases, exact PCM sample-count boundaries",
                "pcmDuration": cursor/sample_rate, "sampleRate": sample_rate,
                "inferenceProviders": voice.session.get_providers(), "lengthScale": 1.06,
                "file": output.name, "bytes": output.stat().st_size,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "fullDecodePassed": True,
                "externalScriptUpload": False}
    output.with_suffix(".captions.json").write_text(json.dumps(captions, ensure_ascii=False, indent=2), "utf-8")
    output.with_suffix(".provenance.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), "utf-8")
    return metadata


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--provider", choices=("piper-local-cpu", "kokoro-local-cpu"))
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    data = json.loads(args.source.read_text("utf-8"))
    for story in data["stories"]:
        for label in VOICES:
            stem = story["topic"]+"-"+label
            if args.only and args.only != stem:
                continue
            target = args.output_dir/(stem+".mp3")
            if target.exists():
                print(json.dumps({"retained": str(target)}), flush=True)
                continue
            result = synthesize(story["script"], label, target, args.model_dir, provider=args.provider)
            print(json.dumps({"asset":stem,"duration":result["duration"],"bytes":result["bytes"],
                              "captions":len(result["captions"]),"provider":result["provider"],
                              "voice":result["voice"],"decoded":result["fullDecodePassed"]}),flush=True)
