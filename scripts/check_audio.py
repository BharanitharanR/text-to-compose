#!/usr/bin/env python3
"""
check_audio.py: verify a rendered song against its composition JSON, since the composer cannot listen.

Usage:
    python check_audio.py song.json outputs/song.wav [--midi outputs/song.mid]

Reports (and exits non-zero on a hard failure):
  - duration vs the planned length (sections / last note), tolerance 4 s
  - clipping: count of samples at or above 0.999 full scale
  - unplanned silence: runs longer than 2.5 s under -50 dBFS inside the planned span
  - section timing: each section's start in seconds
  - vocal range: lowest/highest vocal note vs the singer range in comp["voice_range"] (e.g. "A3-E5") if present
  - MIDI note count equals the JSON note count (if --midi given)
"""
import argparse
import json
import sys

import numpy as np
import soundfile as sf

NOTE_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def to_midi(p):
    if isinstance(p, (int, float)):
        return int(p)
    s = p.strip(); name = s[0].upper(); i = 1; acc = 0
    while i < len(s) and s[i] in "#b":
        acc += 1 if s[i] == "#" else -1; i += 1
    return 12 * (int(s[i:]) + 1) + NOTE_NAMES[name] + acc


def name(m):
    return "C C# D D# E F F# G G# A A# B".split()[m % 12] + str(m // 12 - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json"); ap.add_argument("wav"); ap.add_argument("--midi")
    a = ap.parse_args()
    comp = json.load(open(a.json))
    data, sr = sf.read(a.wav, dtype="float64")
    mono = data.mean(axis=1) if data.ndim > 1 else data
    spb = 60 / comp.get("bpm", 90)
    ok = True

    last_beat = 0
    for tr in comp["tracks"]:
        for nd in tr.get("notes", []):
            last_beat = max(last_beat, nd["beat"] + nd["dur"])
        for k in ("drone", "ambience"):
            if k in tr: last_beat = max(last_beat, tr[k]["end_beat"])
    for s in comp.get("sections", []):
        last_beat = max(last_beat, s["end_beat"])
    planned = last_beat * spb
    dur = len(mono) / sr
    flag = "OK" if abs(dur - planned) <= 4 + 3 else "FAIL"
    ok &= flag == "OK"
    print(f"[{flag}] duration {dur:.1f}s vs planned {planned:.1f}s (+3s tail allowed)")

    clip = int(np.sum(np.abs(mono) >= 0.999))
    flag = "OK" if clip == 0 else "FAIL"; ok &= clip == 0
    print(f"[{flag}] clipping samples: {clip}")

    win = int(0.1 * sr)
    frames = mono[: len(mono) // win * win].reshape(-1, win)
    rms_db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    quiet = rms_db < -50
    runs, cur = [], 0
    for i, q in enumerate(quiet):
        cur = cur + 1 if q else 0
        if not q and cur == 0:
            pass
        if q and cur * 0.1 >= 2.5 and (i + 1 == len(quiet) or not quiet[i + 1]):
            runs.append(((i + 1 - cur) * 0.1, cur * 0.1))
    inside = [r for r in runs if r[0] + r[1] < planned - 1]
    flag = "OK" if not inside else "WARN"
    print(f"[{flag}] silent runs >2.5s inside the piece: {[(round(s,1), round(l,1)) for s,l in inside] or 'none'}")

    for s in comp.get("sections", []):
        print(f"      section {s['name']:<12} {s['start_beat']*spb:7.1f}s -> {s['end_beat']*spb:7.1f}s")

    for tr in comp["tracks"]:
        if tr.get("name", "").lower() == "vocal" and tr.get("notes"):
            ms = [to_midi(n["pitch"]) for n in tr["notes"]]
            lo, hi = min(ms), max(ms)
            line = f"vocal range {name(lo)} to {name(hi)}"
            vr = comp.get("voice_range")
            if vr:
                a_, b_ = vr.replace(" ", "").split("-")
                inr = to_midi(a_) <= lo and hi <= to_midi(b_)
                flag = "OK" if inr else "FAIL"; ok &= inr
                line += f" vs singer {vr}"
            else:
                flag = "INFO"
            print(f"[{flag}] {line}")
            print(f"      peak note at {max(tr['notes'], key=lambda n: to_midi(n['pitch']))['beat']*spb:.1f}s "
                  f"(lyric: {max(tr['notes'], key=lambda n: to_midi(n['pitch'])).get('lyric','')})")

    if a.midi:
        import mido
        mid = mido.MidiFile(a.midi)
        midi_notes = sum(1 for t in mid.tracks for m in t if m.type == "note_on" and m.velocity > 0)
        json_notes = sum(len(t.get("notes", [])) for t in comp["tracks"])
        flag = "OK" if midi_notes == json_notes else "FAIL"; ok &= midi_notes == json_notes
        print(f"[{flag}] MIDI notes {midi_notes} vs JSON notes {json_notes}")

    print("RESULT:", "pass" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
