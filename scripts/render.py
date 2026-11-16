#!/usr/bin/env python3
"""
render.py: turn a composition JSON into a MIDI file and an instrumental WAV.

Usage:
    python render.py song.json --out outputs/            # writes song.mid, song.wav, song.pitch.csv
    python render.py song.json --out outputs/ --no-wav   # MIDI only
    python render.py --schema                             # print the JSON schema with an example

Rendering path for the WAV, chosen automatically:
    1. FluidSynth + a General MIDI SoundFont (if `fluidsynth` is on PATH and a .sf2 is found or given with --sf2)
    2. Built-in numpy synthesizer (additive tones per GM family, filtered noise for percussion)
Ambience and drone layers are always rendered by the built-in synth and mixed in.

Composition JSON schema (keys in order of importance):
{
  "title": "River at Dusk",
  "bpm": 72,
  "time_signature": [4, 4],          # or [7, 8] etc.
  "sections": [                       # used for timing checks and the pitch-track labels
    {"name": "prelude", "start_beat": 0,  "end_beat": 32},
    {"name": "verse",   "start_beat": 32, "end_beat": 96},
    {"name": "conclusion", "start_beat": 96, "end_beat": 120}
  ],
  "tracks": [
    {
      "name": "vocal",                # a track named "vocal" (case-insensitive) is exported as the pitch track
      "program": 52,                  # General MIDI program 0-127 (52 = choir aahs, 73 = flute, 40 = violin, 104 = sitar, 105 = banjo ...)
      "channel": 0,                   # 0-15; channel 9 is percussion
      "volume": 100,                  # 0-127
      "pan": 64,                      # 0-127
      "notes": [
        {"beat": 32, "dur": 2, "pitch": "A3", "vel": 80, "lyric": "All"},
        {"beat": 34, "dur": 1, "pitch": "C4", "vel": 84, "lyric": "a-", "gamaka": true},
        {"beat": 35, "dur": 1, "pitch": 60}            # pitch may be a MIDI number
      ]
    },
    {"name": "drone", "drone": {"pitches": ["D2", "A2"], "start_beat": 0, "end_beat": 120, "gain": 0.25, "timbre": "tanpura"}},
    {"name": "ambience", "ambience": {"kind": "river", "start_beat": 0, "end_beat": 120, "gain": 0.15}},
    {"name": "percussion", "channel": 9, "notes": [{"beat": 32, "dur": 0.5, "pitch": 36, "vel": 90}]}
  ]
}

Notes:
  - "beat" and "dur" are in quarter-note beats from the start of the piece (floats allowed).
  - "gamaka": true adds a slow pitch-bend oscillation (Carnatic/Hindustani ornament). "slide_from": "G3" adds a meend/portamento into the note.
  - Drone timbres: "tanpura", "didgeridoo", "morin_khuur", "pad", "sine".
  - Ambience kinds: "river", "wind", "rain", "insects", "fire", "crowd", "sea", "city".
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np

SR = 44100
NOTE_NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def to_midi(p):
    if isinstance(p, (int, float)):
        return int(p)
    s = p.strip()
    name = s[0].upper()
    i = 1
    acc = 0
    while i < len(s) and s[i] in "#b":
        acc += 1 if s[i] == "#" else -1
        i += 1
    octave = int(s[i:])
    return 12 * (octave + 1) + NOTE_NAMES[name] + acc


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- MIDI -----

def write_midi(comp, path):
    import mido

    bpm = comp.get("bpm", 90)
    ts = comp.get("time_signature", [4, 4])
    mid = mido.MidiFile(ticks_per_beat=480)
    meta = mido.MidiTrack()
    mid.tracks.append(meta)
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=ts[0], denominator=ts[1], time=0))
    meta.append(mido.MetaMessage("track_name", name=comp.get("title", "song"), time=0))

    for t in comp["tracks"]:
        if "notes" not in t:
            continue
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        ch = int(t.get("channel", 0))
        tr.append(mido.MetaMessage("track_name", name=t.get("name", "track"), time=0))
        if ch != 9:
            tr.append(mido.Message("program_change", program=int(t.get("program", 0)), channel=ch, time=0))
        tr.append(mido.Message("control_change", control=7, value=int(t.get("volume", 100)), channel=ch, time=0))
        tr.append(mido.Message("control_change", control=10, value=int(t.get("pan", 64)), channel=ch, time=0))
        # pitch bend range 2 semitones (RPN 0)
        for c, v in ((101, 0), (100, 0), (6, 2), (38, 0)):
            tr.append(mido.Message("control_change", control=c, value=v, channel=ch, time=0))

        events = []  # (tick, order, message)
        for n in t["notes"]:
            start = int(round(n["beat"] * 480))
            end = int(round((n["beat"] + n["dur"]) * 480))
            p = to_midi(n["pitch"])
            vel = int(n.get("vel", 90))
            if n.get("lyric"):
                events.append((start, 0, mido.MetaMessage("lyrics", text=str(n["lyric"]))))
            if n.get("slide_from") is not None:
                # bend from slide_from up/down into the note over the first 1/4 of its length
                src = to_midi(n["slide_from"])
                semis = max(-2, min(2, src - p))
                steps = 8
                for k in range(steps + 1):
                    frac = k / steps
                    bend = int(8191 * semis * (1 - frac) / 2)
                    events.append((start + int((end - start) * 0.25 * frac), 1, mido.Message("pitchwheel", pitch=bend, channel=ch)))
            elif n.get("gamaka"):
                cycles = max(2, int((end - start) / 480 * 5))
                steps = cycles * 8
                for k in range(steps + 1):
                    frac = k / steps
                    bend = int(8191 * 0.5 * math.sin(2 * math.pi * cycles * frac) / 2)  # ±0.5 semitone
                    events.append((start + int((end - start) * frac), 1, mido.Message("pitchwheel", pitch=bend, channel=ch)))
            events.append((start, 2, mido.Message("note_on", note=p, velocity=vel, channel=ch)))
            events.append((end, 1, mido.Message("note_off", note=p, velocity=0, channel=ch)))
            if n.get("gamaka") or n.get("slide_from") is not None:
                events.append((end, 3, mido.Message("pitchwheel", pitch=0, channel=ch)))
        events.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for tick, _, msg in events:
            msg.time = tick - last
            last = tick
            tr.append(msg)
    mid.save(path)
    return path


# ------------------------------------------------------------ synthesis -----

def adsr(n, a=0.02, d=0.1, s=0.7, r=0.2):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    env = np.ones(n)
    if a_n:
        env[:a_n] = np.linspace(0, 1, a_n)
    if d_n and a_n + d_n < n:
        env[a_n:a_n + d_n] = np.linspace(1, s, d_n)
        env[a_n + d_n:] = s
    if r_n and r_n < n:
        env[-r_n:] *= np.linspace(1, 0, r_n)
    return env


FAMILY = {  # GM program ranges -> (partials, attack, decay, sustain, release)
    "piano": ([1, .5, .3, .2, .1], .005, .3, .3, .3),
    "chromatic": ([1, .3, .1], .002, .5, .1, .4),
    "organ": ([1, 1, .5, .5, .3], .05, .05, 1, .1),
    "guitar": ([1, .6, .3, .15], .005, .4, .2, .3),
    "bass": ([1, .4, .1], .01, .2, .6, .2),
    "strings": ([1, .7, .5, .35, .2, .1], .15, .2, .8, .4),
    "ensemble": ([1, .6, .4, .3], .3, .3, .9, .6),
    "brass": ([1, .9, .8, .6, .4, .3, .2], .08, .1, .8, .2),
    "reed": ([1, .2, .8, .3, .5], .06, .1, .8, .2),
    "pipe": ([1, .3, .1, .05], .08, .1, .85, .25),
    "synth": ([1, .5, .33, .25, .2], .02, .2, .7, .4),
    "ethnic": ([1, .8, .5, .4, .3, .2], .01, .4, .4, .5),
}


def family_for(program):
    p = int(program)
    if p < 8: return "piano"
    if p < 16: return "chromatic"
    if p < 24: return "organ"
    if p < 32: return "guitar"
    if p < 40: return "bass"
    if p < 48: return "strings"
    if p < 56: return "ensemble"
    if p < 64: return "brass"
    if p < 72: return "reed"
    if p < 80: return "pipe"
    if p < 104: return "synth"
    return "ethnic"


def tone(freq, dur, partials, env_args, vel=90, gamaka=False, slide_from_hz=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.full(n, freq)
    if slide_from_hz is not None:
        k = max(1, int(n * 0.25))
        f[:k] = np.linspace(slide_from_hz, freq, k)
    if gamaka:
        f = f * 2 ** (0.5 * np.sin(2 * np.pi * 5 * t) / 12)
    phase = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros(n)
    for i, a in enumerate(partials, start=1):
        out += a * np.sin(i * phase)
    out /= sum(partials)
    return out * adsr(n, *env_args) * (vel / 127)


def drum(pitch, dur):
    n = max(int(0.25 * SR), int(dur * SR))
    t = np.arange(n) / SR
    rng = np.random.default_rng(pitch)
    if pitch in (35, 36):  # kick
        return np.sin(2 * np.pi * (60 * np.exp(-t * 20) + 40) * t) * np.exp(-t * 12)
    if pitch in (38, 40):  # snare
        return (rng.standard_normal(n) * 0.5 + np.sin(2 * np.pi * 180 * t) * 0.5) * np.exp(-t * 18)
    if pitch in (42, 44, 46):  # hats
        return rng.standard_normal(n) * np.exp(-t * (60 if pitch == 42 else 15)) * 0.4
    if pitch in (41, 43, 45, 47, 48, 50):  # toms / low drums (use for mridangam, djembe, taiko approximations)
        f0 = 80 + (pitch - 41) * 15
        return np.sin(2 * np.pi * (f0 * np.exp(-t * 6) + f0 * 0.6) * t) * np.exp(-t * 7)
    if pitch in (75, 76, 77):  # claves / woodblocks (clapsticks)
        return np.sin(2 * np.pi * 2500 * t) * np.exp(-t * 90)
    if pitch in (39, 82):  # clap / shaker
        return rng.standard_normal(n) * np.exp(-t * 30) * 0.5
    return rng.standard_normal(n) * np.exp(-t * 25) * 0.3


def drone_layer(spec, total_sec, spb):
    n = int(total_sec * SR)
    out = np.zeros(n)
    t = np.arange(n) / SR
    timbre = spec.get("timbre", "pad")
    for p in spec["pitches"]:
        f = hz(to_midi(p))
        if timbre == "tanpura":
            # plucked-string drone: periodic re-pluck with rich harmonics and slow jawari shimmer
            period = 1.4
            for k in range(int(total_sec / period) + 1):
                s = int(k * period * SR)
                ln = min(n - s, int(2.5 * SR))
                if ln <= 0:
                    break
                tt = np.arange(ln) / SR
                sig = sum((1 / i) * np.sin(2 * np.pi * f * i * tt * (1 + 0.0003 * np.sin(2 * np.pi * 0.7 * tt))) for i in range(1, 12))
                out[s:s + ln] += sig * np.exp(-tt * 1.2) * 0.3
        elif timbre == "didgeridoo":
            lfo = 1 + 0.15 * np.sin(2 * np.pi * 2.2 * t) + 0.08 * np.sin(2 * np.pi * 0.37 * t)
            sig = sum((1 / i) * np.sin(2 * np.pi * f * i * t) for i in range(1, 16))
            out += sig * lfo * 0.3
        elif timbre == "morin_khuur":
            vib = f * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t))
            phase = 2 * np.pi * np.cumsum(vib) / SR
            sig = sum((1 / i) * np.sin(i * phase) for i in range(1, 9))
            out += sig * 0.35
        elif timbre == "sine":
            out += np.sin(2 * np.pi * f * t) * 0.6
        else:  # pad
            sig = sum((0.6 ** (i - 1)) * np.sin(2 * np.pi * f * i * t * (1 + 0.001 * np.sin(2 * np.pi * 0.1 * i * t))) for i in range(1, 6))
            out += sig * 0.3
    a, b = int(spec["start_beat"] * spb * SR), int(spec["end_beat"] * spb * SR)
    env = np.zeros(n)
    fade = int(2 * SR)
    b = min(b, n)
    env[a:b] = 1
    if b - a > 2 * fade:
        env[a:a + fade] = np.linspace(0, 1, fade)
        env[b - fade:b] = np.linspace(1, 0, fade)
    return out * env * spec.get("gain", 0.25)


def ambience_layer(spec, total_sec, spb):
    n = int(total_sec * SR)
    rng = np.random.default_rng(7)
    white = rng.standard_normal(n)
    kind = spec.get("kind", "wind")
    from scipy.signal import butter, lfilter
    t = np.arange(n) / SR

    def bp(x, lo, hi, order=2):
        b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band")
        return lfilter(b, a, x)

    if kind == "river":
        sig = bp(white, 400, 4000) * (1 + 0.3 * np.sin(2 * np.pi * 0.2 * t)) + bp(white, 80, 300) * 0.5
    elif kind == "sea":
        sig = bp(white, 100, 2000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 0.08 * t)) ** 2)
    elif kind == "rain":
        sig = bp(white, 1500, 9000) * (1 + 0.2 * np.sin(2 * np.pi * 0.5 * t))
        drops = (rng.random(n) < 0.0004).astype(float)
        sig += lfilter([1], [1, -0.995], drops) * 0.3
    elif kind == "wind":
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t) * np.sin(2 * np.pi * 0.23 * t + 1)
        sig = bp(white, 150, 900) * (0.3 + mod)
    elif kind == "insects":
        sig = bp(white, 4000, 9000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * t)))
    elif kind == "fire":
        sig = bp(white, 200, 3000) * 0.5
        crackle = (rng.random(n) < 0.0008).astype(float)
        sig += lfilter([1], [1, -0.98], crackle) * 0.8
    elif kind == "crowd":
        sig = bp(white, 250, 2500) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t))
    elif kind == "city":
        sig = bp(white, 60, 500) * 0.7 + bp(white, 1000, 3000) * 0.2 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t))
    else:
        sig = bp(white, 200, 2000)
    sig = sig / (np.max(np.abs(sig)) + 1e-9)
    a, b = int(spec["start_beat"] * spb * SR), int(min(spec["end_beat"] * spb * SR, n))
    env = np.zeros(n)
    fade = int(3 * SR)
    env[a:b] = 1
    if b - a > 2 * fade:
        env[a:a + fade] = np.linspace(0, 1, fade)
        env[b - fade:b] = np.linspace(1, 0, fade)
    return sig * env * spec.get("gain", 0.15)


def builtin_synth(comp, total_sec):
    spb = 60 / comp.get("bpm", 90)
    n = int(total_sec * SR)
    mix = np.zeros((n, 2))
    for tr in comp["tracks"]:
        if "notes" not in tr:
            continue
        ch = int(tr.get("channel", 0))
        pan = int(tr.get("pan", 64)) / 127
        vol = int(tr.get("volume", 100)) / 127
        fam = FAMILY[family_for(tr.get("program", 0))]
        for nd in tr["notes"]:
            s = int(nd["beat"] * spb * SR)
            dur = nd["dur"] * spb
            if ch == 9:
                sig = drum(to_midi(nd["pitch"]), dur) * (int(nd.get("vel", 90)) / 127)
            else:
                sf = hz(to_midi(nd["slide_from"])) if nd.get("slide_from") is not None else None
                sig = tone(hz(to_midi(nd["pitch"])), dur + fam[4], fam[0], fam[1:], int(nd.get("vel", 90)), bool(nd.get("gamaka")), sf)
            e = min(n, s + len(sig))
            if e > s:
                seg = sig[: e - s] * vol
                mix[s:e, 0] += seg * (1 - pan)
                mix[s:e, 1] += seg * pan
    return mix


def fluidsynth_render(midi_path, wav_path, sf2):
    cmd = ["fluidsynth", "-ni", "-F", wav_path, "-r", str(SR), "-g", "0.8", sf2, midi_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import soundfile as sf
    data, sr = sf.read(wav_path, dtype="float64")
    if data.ndim == 1:
        data = np.stack([data, data], axis=1)
    return data


def find_sf2(explicit):
    if explicit and os.path.exists(explicit):
        return explicit
    for d in ("/usr/share/sounds/sf2", "/usr/share/soundfonts", "/usr/local/share/soundfonts", os.path.expanduser("~/soundfonts")):
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.lower().endswith(".sf2"):
                    return os.path.join(d, f)
    return None


def reverb(x, mix=0.18, decay=0.45):
    # cheap multi-tap comb reverb; enough to give instruments a room
    out = x.copy()
    for delay_ms, g in ((29, decay), (37, decay * .8), (53, decay * .6), (71, decay * .5)):
        d = int(delay_ms * SR / 1000)
        y = np.zeros_like(x)
        y[d:] = x[:-d]
        for _ in range(3):
            z = np.zeros_like(y)
            z[d:] = y[:-d] * g
            y = y + z
        out += y * mix / 4
    return out


# ------------------------------------------------------------------ main ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json", nargs="?")
    ap.add_argument("--out", default=".")
    ap.add_argument("--no-wav", action="store_true")
    ap.add_argument("--sf2")
    ap.add_argument("--force-builtin", action="store_true")
    ap.add_argument("--schema", action="store_true")
    args = ap.parse_args()
    if args.schema or not args.json:
        print(__doc__)
        return
    with open(args.json) as f:
        comp = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    stem = os.path.join(args.out, os.path.splitext(os.path.basename(args.json))[0])
    bpm = comp.get("bpm", 90)
    spb = 60 / bpm

    last_beat = 0
    for tr in comp["tracks"]:
        for nd in tr.get("notes", []):
            last_beat = max(last_beat, nd["beat"] + nd["dur"])
        for key in ("drone", "ambience"):
            if key in tr:
                last_beat = max(last_beat, tr[key]["end_beat"])
    for s in comp.get("sections", []):
        last_beat = max(last_beat, s["end_beat"])
    total_sec = last_beat * spb + 3

    midi_path = write_midi(comp, stem + ".mid")
    print(f"MIDI  -> {midi_path}")

    # pitch track for the vocal
    for tr in comp["tracks"]:
        if tr.get("name", "").lower() == "vocal" and tr.get("notes"):
            with open(stem + ".pitch.csv", "w") as f:
                f.write("start_sec,end_sec,midi,hz,lyric,gamaka\n")
                for nd in tr["notes"]:
                    m = to_midi(nd["pitch"])
                    f.write(f"{nd['beat'] * spb:.3f},{(nd['beat'] + nd['dur']) * spb:.3f},{m},{hz(m):.2f},{nd.get('lyric', '')},{int(bool(nd.get('gamaka')))}\n")
            print(f"pitch -> {stem}.pitch.csv")

    if args.no_wav:
        return

    import soundfile as sf
    sf2 = None if args.force_builtin else find_sf2(args.sf2)
    if sf2 and shutil.which("fluidsynth"):
        inst = fluidsynth_render(midi_path, stem + ".inst.wav", sf2)
        n = int(total_sec * SR)
        if len(inst) < n:
            inst = np.vstack([inst, np.zeros((n - len(inst), 2))])
        inst = inst[:n]
        path_used = f"FluidSynth + {os.path.basename(sf2)}"
    else:
        inst = builtin_synth(comp, total_sec)
        path_used = "built-in numpy synth (no SoundFont/FluidSynth found)"
    inst = reverb(inst)

    layers = np.zeros_like(inst)
    for tr in comp["tracks"]:
        if "drone" in tr:
            d = drone_layer(tr["drone"], total_sec, spb)
            layers[:, 0] += d
            layers[:, 1] += d
        if "ambience" in tr:
            a = ambience_layer(tr["ambience"], total_sec, spb)
            layers[:, 0] += a
            layers[:, 1] += a * 0.9
    mix = inst + layers
    peak = np.max(np.abs(mix)) + 1e-9
    mix = mix / peak * 0.89  # -1 dBFS
    sf.write(stem + ".wav", mix.astype(np.float32), SR, subtype="PCM_16")
    print(f"WAV   -> {stem}.wav  ({total_sec:.1f}s, instruments via {path_used})")
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", stem + ".wav", "-b:a", "192k", stem + ".mp3"], check=False)
        if os.path.exists(stem + ".mp3"):
            print(f"MP3   -> {stem}.mp3")
    if os.path.exists(stem + ".inst.wav"):
        os.remove(stem + ".inst.wav")


if __name__ == "__main__":
    main()
