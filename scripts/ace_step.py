#!/usr/bin/env python3
"""Prepare or execute an ACE-Step 1.5 generation request from a canonical SongSpec.

ACE-Step 1.5 is an open-source music model that runs locally. Its REST API
server listens on http://127.0.0.1:8001 by default (start_api_server_macos.sh
on Apple Silicon, start_api_server.sh elsewhere).

Dry run (no server needed):
  python scripts/ace_step.py examples/song-spec.json --out outputs --print

Generate (server running):
  python scripts/ace_step.py examples/song-spec.json --out outputs --generate --seed 42

The adapter is a thin translation layer. ACE-Step sings; it cannot speak, so
SongSpec sections marked "spoken" become instrumental [Intro]/[Interlude]
sections and are reported as not rendered.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_SERVER = os.environ.get("ACESTEP_API_URL", "http://127.0.0.1:8001")

LANGUAGE_CODES = {
    "english": "en", "tamil": "ta", "hindi": "hi", "telugu": "te", "bengali": "bn",
    "punjabi": "pa", "urdu": "ur", "nepali": "ne", "sanskrit": "sa", "japanese": "ja",
    "chinese": "zh", "mandarin": "zh", "cantonese": "yue", "korean": "ko", "spanish": "es",
    "french": "fr", "german": "de", "italian": "it", "portuguese": "pt", "russian": "ru",
    "arabic": "ar", "persian": "fa", "turkish": "tr", "irish": "unknown", "gaelic": "unknown",
}

SECTION_TAGS = {
    "prelude": "Intro", "intro": "Intro", "conclusion": "Outro", "outro": "Outro",
    "coda": "Outro", "ending": "Outro",
    # Carnatic kriti form: pallavi is the refrain, anupallavi and charanam the verses.
    "pallavi": "Chorus", "anupallavi": "Verse 1", "charanam": "Verse 2",
    "alap": "Intro", "alapana": "Intro",
}

# Ragas whose scale reads clearly as Western major or minor, so ACE-Step gets a
# usable key. Tonic comes from "Sa = X" in the SongSpec; ragas not listed are
# left to ACE-Step's own LM.
RAGA_MODES = {
    "shankarabharanam": "major", "bilaval": "major", "kalyani": "major", "yaman": "major",
    "harikambhoji": "major", "khamaj": "major", "mohanam": "major", "bhoopali": "major",
    "kharaharapriya": "minor", "kafi": "minor", "natabhairavi": "minor", "asavari": "minor",
    "hindolam": "minor", "malkauns": "minor", "abheri": "minor", "bhimpalasi": "minor",
    "sindhubhairavi": "minor", "bhairavi": "minor", "keeravani": "minor", "shanmukhapriya": "minor",
}


def language_code(name):
    if not name:
        return "unknown"
    name = name.strip().lower()
    if len(name) <= 3:
        return name
    for word in re.split(r"[^a-z]+", name):
        if word in LANGUAGE_CODES:
            return LANGUAGE_CODES[word]
    return "unknown"


MINOR_MODES = {"minor", "min", "m", "aeolian", "dorian", "phrygian", "locrian"}
MAJOR_MODES = {"major", "maj", "ionian", "lydian", "mixolydian"}


def key_scale(text):
    """Return an ACE-Step key like 'D minor' (church modes folded to major/minor),
    or '' for ragas and free text, which ACE-Step's own LM then fills."""
    if not text:
        return ""
    low = text.lower()
    raga = next((r for r in RAGA_MODES if r in low), None)
    if raga:
        sa = re.search(r"\bsa\s*=\s*([A-G])([#b♯♭]?)", text, re.I)
        if sa:
            return f"{sa.group(1).upper()}{sa.group(2)} {RAGA_MODES[raga]}"
        # No tonic named: fall through, a leading "D mixolydian ..." still gives a key.
    m = re.match(r"^\s*([A-Ga-g])([#b♯♭]?)(?:\s+([A-Za-z]+)|(m)\b)?", text)
    if not m:
        return ""
    note, acc = m.group(1).upper(), m.group(2)
    mode = (m.group(3) or m.group(4) or "major").lower()
    if mode in MINOR_MODES:
        return f"{note}{acc} minor"
    if mode in MAJOR_MODES:
        return f"{note}{acc} major"
    return ""


def section_seconds(section, bpm):
    if "duration_ms" in section:
        return float(section["duration_ms"]) / 1000.0
    start = float(section.get("start_beat", 0))
    end = float(section.get("end_beat", start + 16))
    return (end - start) * 60.0 / float(bpm)


def song_duration(spec):
    meta = spec.get("metadata", {})
    if meta.get("duration_seconds"):
        seconds = float(meta["duration_seconds"])
    else:
        bpm = spec["creative"].get("tempo", 90)
        seconds = sum(section_seconds(s, bpm) for s in spec["arrangement"]["sections"])
    return max(10.0, min(600.0, round(seconds)))


def _short(text):
    """Caption-sized phrase: drop parentheticals and keep the first clause."""
    text = re.sub(r"\([^)]*\)", "", text or "")
    text = re.split(r"[;.:]", text)[0]
    text = re.sub(r"\s+,", ",", re.sub(r"\s+", " ", text))
    return text.strip(" ,")


def _words(text, limit):
    """_short(), then at most `limit` words, so one field cannot swamp a tag."""
    return " ".join(_short(text).split()[:limit]).strip(" ,")


def build_caption(spec):
    """ACE-Step reads a compact tag-style caption; stage directions only add noise."""
    c = spec["creative"]
    vocals = c.get("vocals", {})
    parts = [_short(c.get("style", ""))]
    parts += [_short(i) for i in c.get("instruments", [])]
    if vocals.get("required", True):
        parts.append(_short(vocals.get("singer", "")) + " vocals")
    else:
        # Without lyrics to anchor it, the caption is the only place the motif
        # and the ending can reach ACE-Step.
        parts += ["instrumental", "no vocals",
                  _words(spec.get("arrangement", {}).get("motif", ""), 10),
                  _words(c.get("ending", ""), 10)]
    parts += spec.get("metadata", {}).get("tags", [])
    seen, out = set(), []
    for p in parts:
        p = (p or "").strip()
        if p and p.lower() not in seen:
            seen.add(p.lower())
            out.append(p)
    return ", ".join(out)


def _tag(name):
    low = re.sub(r"[_\-]+", " ", name.strip().lower())
    for key, tag in SECTION_TAGS.items():
        if low == key or low.startswith(key + " "):
            return tag
    return low.title()


def _is_wordless(section):
    text = (section.get("text") or "").strip()
    return section.get("wordless") or not text or (text.startswith("(") and text.endswith(")"))


def build_lyrics(spec):
    """Section-tagged lyrics in arrangement order. Arrangement sections with no
    lyric (interludes) become empty instrumental tags."""
    lyric_sections = spec["lyrics"]["sections"]
    by_name = {s["name"].strip().lower(): s for s in lyric_sections}
    order = []
    for a in spec.get("arrangement", {}).get("sections", []):
        low = a["name"].strip().lower()
        match = by_name.get(low) or next((s for n, s in by_name.items() if n.startswith(low + " ")), None)
        order.append((a["name"], match))
    used = {id(m) for _, m in order if m}
    if any(id(s) not in used for s in lyric_sections):
        order = [(s["name"], s) for s in lyric_sections]  # names don't line up: trust lyric order

    lines, dropped = [], []
    for name, section in order:
        lines.append(f"[{_tag(name)}]")
        if section and section.get("spoken"):
            # ACE-Step cannot speak: the slot stays instrumental.
            dropped.append({"section": section["name"], "text": section.get("text", "")})
        elif section and not _is_wordless(section):
            lines.append(section["text"].strip())
        lines.append("")
    return "\n".join(lines).strip(), dropped


def _energy_words(energy):
    """ACE-Step reads words, not numbers: a 0-1 section energy becomes a feel."""
    if energy is None:
        return ""
    energy = float(energy)
    if energy < 0.35:
        return "soft and sparse"
    if energy < 0.65:
        return "moderate"
    return "driving and full"


def _instrumental_tag(index, count, section):
    """Section type for one arrangement section of an instrumental piece. A
    recognised name (intro, outro, ...) wins; otherwise first is Intro, last is
    Outro, and the middle reads as Verse when it carries energy, Interlude when
    it breathes."""
    low = re.sub(r"[_\-]+", " ", section.get("name", "").strip().lower())
    for key, tag in SECTION_TAGS.items():
        if low == key or low.startswith(key + " "):
            return tag
    if index == 0:
        return "Intro"
    if index == count - 1 and count > 1:
        return "Outro"
    energy = section.get("energy")
    if energy is None:
        return "Verse" if index % 2 else "Interlude"
    if float(energy) >= 0.55:
        return "Verse"
    return "Interlude" if float(energy) < 0.35 else "Bridge"


def build_instrumental_lyrics(spec):
    """One descriptive tag line per arrangement section, e.g.
    [Verse - instrumental, playful, driving and full, acoustic guitar, shaker].
    ACE-Step follows these as the order of the piece, not as exact timings.
    Falls back to a bare [Instrumental] when the spec has no arrangement."""
    sections = spec.get("arrangement", {}).get("sections", [])
    if not sections:
        return "[Instrumental]"
    lines = []
    for i, s in enumerate(sections):
        mood = (s.get("mood") or "").strip()
        parts = ["instrumental", "" if mood.lower() == "neutral" else _words(mood, 4),
                 _energy_words(s.get("energy")), _words(s.get("texture", ""), 6),
                 _words(s.get("transition", ""), 6)]
        # `purpose` is left out on purpose: it is a stage direction ("lift
        # energy for the exchange"), and cut to tag length it reads as noise.
        parts += [_short(x) for x in s.get("instruments", [])]
        seen, out = set(), []
        for p in parts:
            if p and p.lower() not in seen:
                seen.add(p.lower())
                out.append(p)
        lines += [f"[{_instrumental_tag(i, len(sections), s)} - {', '.join(out)}]", ""]
    return "\n".join(lines).strip()


def build_request(spec, seed=None, steps=8, duration=None, thinking=True, audio_format="wav"):
    c = spec["creative"]
    vocals = c.get("vocals", {})
    lyrics, dropped = build_lyrics(spec)
    if not vocals.get("required", True):
        lyrics = build_instrumental_lyrics(spec)
    ts = c.get("time_signature") or [4, 4]
    request = {
        "prompt": build_caption(spec),
        "lyrics": lyrics,
        "bpm": int(round(c.get("tempo", 90))),
        "key_scale": key_scale(c.get("key_or_raga", "")),
        "time_signature": str(ts[0]),
        "audio_duration": float(duration) if duration else song_duration(spec),
        "vocal_language": language_code(vocals.get("language") or spec["metadata"].get("language")),
        "thinking": thinking,
        # The SongSpec already carries the creative decisions; keep ACE's LM from rewriting them.
        "use_cot_caption": False,
        "use_cot_language": False,
        "inference_steps": steps,
        "batch_size": 1,
        "audio_format": audio_format,
    }
    if seed is not None:
        request["use_random_seed"] = False
        request["seed"] = int(seed)
    notes = {
        "not_rendered": dropped,
        "raga_or_free_key": c.get("key_or_raga", "") if not request["key_scale"] else "",
    }
    return request, notes


# ---------------------------------------------------------------- HTTP client

# Only needed when the local ACE-Step server was started with API-key auth.
API_KEY = os.environ.get("ACESTEP_API_KEY")


def _headers(extra=None):
    headers = dict(extra or {})
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def _post(server, path, payload, timeout=60):
    req = urllib.request.Request(
        server.rstrip("/") + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_headers({"Content-Type": "application/json"}),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(f"Cannot reach ACE-Step API at {server}: {exc}. Start it with start_api_server_macos.sh") from exc
    if body.get("code") != 200:
        raise RuntimeError(f"ACE-Step {path} failed: {body.get('error')}")
    return body["data"]


def generate(server, request, out_path, poll_seconds=3, timeout_seconds=1800):
    """Submit one task, wait for it, download the first audio file. Returns the result record."""
    task = _post(server, "/release_task", request)
    task_id = task["task_id"]
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        rows = _post(server, "/query_result", {"task_id_list": [task_id]})
        row = rows[0] if rows else {}
        status = row.get("status")
        if status == 1:
            results = row.get("result")
            results = json.loads(results) if isinstance(results, str) else results
            first = results[0]
            url = first["file"]
            if url.startswith("/"):
                url = server.rstrip("/") + url
            with urllib.request.urlopen(urllib.request.Request(url, headers=_headers()), timeout=300) as r, \
                    open(out_path, "wb") as f:
                f.write(r.read())
            first["task_id"] = task_id
            return first
        if status == 2:
            raise RuntimeError(f"ACE-Step task {task_id} failed: {row.get('result') or row}")
        time.sleep(poll_seconds)
    raise TimeoutError(f"ACE-Step task {task_id} did not finish in {timeout_seconds}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("song_spec")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--print", action="store_true", dest="print_request")
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--server", "--api-url", dest="server", default=DEFAULT_SERVER)
    ap.add_argument("--api-key", default=None, help="only if the local server requires auth (or set ACESTEP_API_KEY)")
    ap.add_argument("--model", default=None, help="a specific DiT model loaded by the server")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--duration", type=float)
    ap.add_argument("--timeout", type=int, default=1800, help="seconds to wait for a render")
    ap.add_argument("--no-thinking", action="store_true")
    args = ap.parse_args()
    global API_KEY
    API_KEY = args.api_key or API_KEY

    with open(args.song_spec, encoding="utf-8") as f:
        spec = json.load(f)
    if spec.get("song_spec_version") != "1.0":
        raise SystemExit("Unsupported SongSpec version; expected 1.0")

    request, notes = build_request(spec, args.seed, args.steps, args.duration, not args.no_thinking)
    if args.model:
        request["model"] = args.model
    os.makedirs(args.out, exist_ok=True)
    manifest = os.path.join(args.out, "ace-step-request.json")
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump({"request": request, "notes": notes}, f, ensure_ascii=False, indent=2)
    print(f"ACE-Step request -> {manifest}")
    if args.print_request:
        print(json.dumps(request, ensure_ascii=False, indent=2))
    for d in notes["not_rendered"]:
        print(f"Not rendered (ACE-Step cannot speak): {d['section']}: {d['text']}")
    if notes["raga_or_free_key"]:
        print(f"Key left to ACE-Step: '{notes['raga_or_free_key']}' is not a major/minor key")

    if not args.generate:
        print("Dry run only. Add --generate with the ACE-Step API server running.")
        return 0

    out_path = os.path.join(args.out, f"ace-step-song.{request['audio_format']}")
    t0 = time.time()
    result = generate(args.server, request, out_path, timeout_seconds=args.timeout)
    print(f"ACE-Step audio -> {out_path} ({time.time() - t0:.0f}s, seed {result.get('seed_value', '?')})")
    with open(os.path.join(args.out, "ace-step-result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
