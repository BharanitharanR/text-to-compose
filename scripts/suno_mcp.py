#!/usr/bin/env python3
"""Prepare a Suno MCP generation request from a canonical SongSpec.

This is intentionally a placeholder adapter. It does NOT call Suno directly.
It creates a provider-neutral request manifest that an MCP-capable host agent
can translate into the official Suno MCP tools.
"""
import argparse, json, os
def build_request(spec):
    c, l = spec["creative"], spec["lyrics"]
    parts = [
        c.get("style", ""), f"{c.get('tempo', 90)} bpm",
        f"key/raga: {c.get('key_or_raga', 'unspecified')}",
        "instruments: " + ", ".join(c.get("instruments", [])),
        "vocals: " + c.get("vocals", {}).get("singer", "unspecified"),
        "narrator: " + c.get("vocals", {}).get("narrator", "none"),
        "ending: " + c.get("ending", "natural resolution")
    ]
    lyric_parts = []
    for section in l["sections"]:
        tag = section["name"]
        text = section["text"]
        lyric_parts.append(f"[Spoken narration: {tag}]\n({text})" if section.get("spoken") else f"[{tag}]\n{text}")
    return {
        "provider": "suno-mcp", "transport": "MCP", "status": "placeholder",
        "title": spec["metadata"]["title"],
        "capabilities_requested": spec.get("providers", {}).get("requested_capabilities", []),
        "style": "; ".join(parts), "lyrics": "\n\n".join(lyric_parts),
        "source_song_spec_version": spec["song_spec_version"],
        "note": "Local dry-run only. Use the official Suno MCP integration from an MCP-capable host to execute this request."
    }
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song_spec"); ap.add_argument("--out", default="outputs"); ap.add_argument("--print", action="store_true", dest="print_request")
    args = ap.parse_args()
    spec = json.load(open(args.song_spec, encoding="utf-8"))
    if spec.get("song_spec_version") != "1.0": raise SystemExit("Unsupported SongSpec version; expected 1.0")
    req = build_request(spec)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "suno-mcp-request.json")
    json.dump(req, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Suno MCP placeholder request -> {path}")
    if args.print_request: print(json.dumps(req, ensure_ascii=False, indent=2))
if __name__ == "__main__": main()
