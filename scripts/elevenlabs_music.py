#!/usr/bin/env python3
"""Prepare or execute an Eleven Music API request from a canonical SongSpec.

Dry-run is the default and requires no credentials:
  python scripts/elevenlabs_music.py examples/song-spec.json --out outputs --print

Generate audio with the official Eleven Music API:
  ELEVENLABS_API_KEY=... python scripts/elevenlabs_music.py examples/song-spec.json --out outputs --generate

The adapter uses Eleven Music v2.5 composition plans when the SongSpec has
section-level arrangement data. The API is paid; this script never prints or
stores the API key.
"""
import argparse
import json
import os
import urllib.error
import urllib.request

API_URL = "https://api.elevenlabs.io/v1/music"
MODEL_ID = "music_v2_5"

def section_duration_ms(section, bpm):
    if "duration_ms" in section:
        return max(3000, min(120000, int(section["duration_ms"])))
    start = float(section.get("start_beat", 0))
    end = float(section.get("end_beat", start + 4))
    duration = (end - start) * 60000.0 / float(bpm)
    return max(3000, min(120000, round(duration)))

def build_plan(spec):
    creative = spec["creative"]
    bpm = creative.get("tempo", 90)
    base_styles = [
        creative.get("style", ""),
        f"{bpm} BPM",
        creative.get("key_or_raga", ""),
        *creative.get("instruments", []),
    ]
    vocals = creative.get("vocals", {})
    if vocals.get("required"):
        base_styles.extend([
            vocals.get("singer", "expressive vocals"),
            f"language: {vocals.get('language', spec['metadata']['language'])}",
            vocals.get("technique", ""),
        ])

    chunks = []
    lyric_by_name = {s["name"]: s for s in spec["lyrics"]["sections"]}
    for section in spec["arrangement"]["sections"]:
        name = section["name"]
        lyric = lyric_by_name.get(name, {})
        text = f"[{name}]"
        if lyric.get("text"):
            text += "\n" + lyric["text"]
        if lyric.get("spoken"):
            text += "\n{spoken narration}"

        styles = [x for x in base_styles + section.get("instruments", []) if x]
        if section.get("purpose"):
            styles.append(section["purpose"])

        chunks.append({
            "text": text,
            "duration_ms": section_duration_ms(section, bpm),
            "positive_styles": styles[:50],
            "negative_styles": [],
            "context_adherence": "high",
        })

    if not chunks:
        raise ValueError("SongSpec arrangement.sections must contain at least one section")
    return {"chunks": chunks[:30]}

def build_request(spec):
    return {
        "model_id": MODEL_ID,
        "composition_plan": build_plan(spec),
        "output_format": "mp3_48000_192",
    }

def post_json(payload, api_key):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json", "xi-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            return response.read(), response.headers
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Eleven Music API returned HTTP {exc.code}: {body}") from exc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song_spec")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--print", action="store_true", dest="print_request")
    ap.add_argument("--generate", action="store_true")
    args = ap.parse_args()

    with open(args.song_spec, encoding="utf-8") as f:
        spec = json.load(f)
    if spec.get("song_spec_version") != "1.0":
        raise SystemExit("Unsupported SongSpec version; expected 1.0")

    request = build_request(spec)
    os.makedirs(args.out, exist_ok=True)
    manifest_path = os.path.join(args.out, "elevenlabs-music-request.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(request, f, ensure_ascii=False, indent=2)

    print(f"Eleven Music request -> {manifest_path}")
    if args.print_request:
        print(json.dumps(request, ensure_ascii=False, indent=2))

    if not args.generate:
        print("Dry run only. Add --generate with ELEVENLABS_API_KEY to create audio.")
        return 0

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise SystemExit("--generate requires ELEVENLABS_API_KEY")

    audio, headers = post_json(request, api_key)
    output_path = os.path.join(args.out, "elevenlabs-song.mp3")
    with open(output_path, "wb") as f:
        f.write(audio)

    song_id = headers.get("song-id", "")
    print(f"Eleven Music audio -> {output_path}")
    if song_id:
        print(f"song-id: {song_id}")

if __name__ == "__main__":
    main()
