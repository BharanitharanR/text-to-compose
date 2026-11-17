#!/usr/bin/env python3
"""Render a canonical SongSpec using the existing local reference renderer."""
import argparse, json, os, subprocess, sys, tempfile
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song_spec"); ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    spec = json.load(open(args.song_spec, encoding="utf-8"))
    if spec.get("song_spec_version") != "1.0": raise SystemExit("Unsupported SongSpec version; expected 1.0")
    tracks = spec.get("score", {}).get("tracks")
    if not tracks:
        raise SystemExit("SongSpec is valid, but has no score.tracks. The composer must compile the SongSpec into note tracks before local rendering.")
    comp = {
        "title": spec["metadata"]["title"], "bpm": spec["creative"]["tempo"],
        "time_signature": spec["creative"].get("time_signature", [4, 4]),
        "sections": spec["arrangement"]["sections"], "tracks": tracks,
        "voice_range": spec["creative"].get("vocals", {}).get("range")
    }
    os.makedirs(args.out, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(comp, f, ensure_ascii=False, indent=2); temp = f.name
    try:
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "render.py"), temp, "--out", args.out], check=True)
    finally: os.unlink(temp)
if __name__ == "__main__": main()
