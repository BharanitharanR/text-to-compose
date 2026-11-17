#!/usr/bin/env python3
"""Validate a canonical SongSpec JSON document."""
import argparse, json, sys
REQUIRED = ("song_spec_version", "metadata", "creative", "lyrics", "arrangement")
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    args = ap.parse_args()
    try:
        data = json.load(open(args.json, encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot read JSON: {exc}"); return 1
    errors = [f"missing required field: {k}" for k in REQUIRED if k not in data]
    if data.get("song_spec_version") != "1.0": errors.append("song_spec_version must be '1.0'")
    if not isinstance(data.get("lyrics", {}).get("sections"), list): errors.append("lyrics.sections must be an array")
    if not isinstance(data.get("arrangement", {}).get("sections"), list): errors.append("arrangement.sections must be an array")
    tempo = data.get("creative", {}).get("tempo")
    if tempo is not None and not (20 <= float(tempo) <= 300): errors.append("creative.tempo must be between 20 and 300 BPM")
    if errors:
        print("FAIL"); [print(f"  - {e}") for e in errors]; return 1
    print("OK: valid SongSpec 1.0")
    print(f"  title: {data['metadata'].get('title', '(untitled)')}")
    print(f"  provider: {data.get('providers', {}).get('preferred', 'none')}")
    print(f"  lyric sections: {len(data['lyrics']['sections'])}")
    print(f"  arrangement sections: {len(data['arrangement']['sections'])}")
    return 0
if __name__ == "__main__": sys.exit(main())
