#!/usr/bin/env python3
"""Measure every song in an A/B run folder (results.json from ace_step_ab.py).

Run with throwaway dependencies, e.g.:
  uv run --no-project --with librosa --with mlx-whisper python evals/analyze_audio.py ab-runs/river-at-dusk --transcribe

Per song: length, peak and average loudness, share of near-silence, detected
tempo and key, brightness (spectral centroid), note-onset density and, with
--transcribe, what words a speech recogniser hears (rough on singing) plus the
share of the input's words that come through. Also writes an MP3 next to each
WAV for listening. Results go into analysis.json.
"""
import argparse
import json
import os
import re
import subprocess

import librosa
import numpy as np

KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def estimate_key(y, sr):
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    best = (-2.0, "")
    for i in range(12):
        for profile, mode in ((MAJOR, "major"), (MINOR, "minor")):
            r = np.corrcoef(chroma, np.roll(profile, i))[0, 1]
            if r > best[0]:
                best = (r, f"{KEYS[i]} {mode}")
    return best[1], round(float(best[0]), 2)


def words(text):
    return re.findall(r"[a-z']+", text.lower())


def measure(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    dur = len(y) / sr
    rms = librosa.feature.rms(y=y)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    key, key_conf = estimate_key(y, sr)
    return {
        "duration_s": round(dur, 1),
        "peak_dbfs": round(float(20 * np.log10(max(np.abs(y).max(), 1e-9))), 1),
        "avg_loudness_db": round(float(np.mean(db)), 1),
        "near_silence_pct": round(float(np.mean(db < -45) * 100), 1),
        "tempo_bpm": round(float(np.atleast_1d(tempo)[0]), 1),
        "key": key, "key_confidence": key_conf,
        "brightness_hz": round(float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())),
        "onsets_per_s": round(len(onsets) / dur, 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--transcribe", action="store_true")
    ap.add_argument("--whisper", default="mlx-community/whisper-small-mlx")
    args = ap.parse_args()

    results = json.load(open(os.path.join(args.run_dir, "results.json"), encoding="utf-8"))
    source = words(open(os.path.join(args.run_dir, "input.txt"), encoding="utf-8").read())
    out = []
    for run in results["runs"]:
        wav = os.path.join(args.run_dir, run["file"])
        mp3 = wav[:-4] + ".mp3"
        if not os.path.exists(mp3):
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-b:a", "160k", mp3], check=True)
        m = measure(wav)
        if args.transcribe:
            import mlx_whisper
            text = mlx_whisper.transcribe(wav, path_or_hf_repo=args.whisper, language="en")["text"].strip()
            heard = set(words(text))
            m["heard"] = text
            m["source_words_heard_pct"] = round(100 * sum(w in heard for w in set(source)) / len(set(source)))
        out.append({"path": run["path"], "seed": run["seed"], "mp3": os.path.relpath(mp3, args.run_dir), **m})
        print(run["path"], run["seed"], json.dumps(m, ensure_ascii=False)[:300], flush=True)
    with open(os.path.join(args.run_dir, "analysis.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
