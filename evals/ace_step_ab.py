#!/usr/bin/env python3
"""A/B test: the same text sent straight to ACE-Step vs. sent through the skill.

  A (direct): the raw text goes to ACE-Step as lyrics with no caption. ACE-Step's
              own language model fills in caption, BPM, key and structure.
  B (skill):  the skill's SongSpec for the same text goes through scripts/ace_step.py.

Held equal in both: model, seed, inference steps, duration, batch size, format.

Usage (ACE-Step API server running on :8001):
  python evals/ace_step_ab.py ab-runs/river-at-dusk --seeds 11 22 33

The run folder must hold input.txt (raw text) and skill/song-spec.json.
Writes a/<seed>.wav, b/<seed>.wav and results.json into the run folder.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import ace_step  # noqa: E402


def direct_request(text, seed, steps, duration):
    return {
        "prompt": "",
        "lyrics": text.strip(),
        "thinking": True,
        "use_cot_caption": True,
        "use_cot_language": True,
        "audio_duration": duration,
        "inference_steps": steps,
        "batch_size": 1,
        "audio_format": "wav",
        "use_random_seed": False,
        "seed": seed,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--server", default=ace_step.DEFAULT_SERVER)
    args = ap.parse_args()

    run = args.run_dir
    text = open(os.path.join(run, "input.txt"), encoding="utf-8").read()
    spec = json.load(open(os.path.join(run, "skill", "song-spec.json"), encoding="utf-8"))
    duration = ace_step.song_duration(spec)
    os.makedirs(os.path.join(run, "a"), exist_ok=True)
    os.makedirs(os.path.join(run, "b"), exist_ok=True)

    results = {"duration": duration, "steps": args.steps, "seeds": args.seeds, "runs": []}
    for seed in args.seeds:
        req_b, notes_b = ace_step.build_request(spec, seed=seed, steps=args.steps, duration=duration)
        for path, req in (("a", direct_request(text, seed, args.steps, duration)), ("b", req_b)):
            out = os.path.join(run, path, f"{seed}.wav")
            t0 = time.time()
            res = ace_step.generate(args.server, req, out)
            secs = time.time() - t0
            print(f"[{path}] seed {seed}: {out} in {secs:.0f}s", flush=True)
            results["runs"].append({
                "path": path, "seed": seed, "file": os.path.relpath(out, run),
                "seconds_to_generate": round(secs, 1), "request": req,
                "ace_used": {k: res.get(k) for k in ("prompt", "lyrics", "metas", "seed_value", "lm_model", "dit_model")},
                "notes": notes_b if path == "b" else {},
            })
            with open(os.path.join(run, "results.json"), "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Done -> {os.path.join(run, 'results.json')}")


if __name__ == "__main__":
    main()
