#!/usr/bin/env python3
"""Compile a SongSpec into an ACE-Step 1.5 local API request and optionally generate audio.

The adapter talks only to the user's local ACE-Step API. It has no hosted service
dependency and requires no API key unless the local ACE-Step server is configured
with one.

Default API: http://127.0.0.1:8001
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


def http_json(url, method="GET", payload=None, timeout=30, api_key=None):
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build_prompt(spec):
    c = spec["creative"]
    instruments = ", ".join(c.get("instruments", []))
    vocals = c.get("vocals", {})
    singer = vocals.get("singer", "natural lead vocal")
    world = c.get("world", "")
    style = c.get("style", "")
    ending = c.get("ending", "")
    return (
        f"{style}. {world} "
        f"Instrumentation: {instruments}. "
        f"Vocal character: {singer}. "
        f"Ending: {ending}."
    ).strip()


def build_lyrics(spec):
    parts = []
    for section in spec["lyrics"]["sections"]:
        name = section["name"]
        text = section["text"].strip()
        if not text:
            continue
        if section.get("spoken"):
            parts.append(f"[Spoken: {name}]\n{text}")
        else:
            parts.append(f"[{name}]\n{text}")
    return "\n\n".join(parts)


def build_request(spec, duration=None, model=None):
    c = spec["creative"]
    v = c.get("vocals", {})
    requested_duration = duration or spec.get("metadata", {}).get("duration_seconds")
    request = {
        "prompt": build_prompt(spec),
        "lyrics": build_lyrics(spec),
        "thinking": True,
        "vocal_language": v.get("language") or spec.get("metadata", {}).get("language", "en"),
        "audio_format": "mp3",
        "bpm": int(round(c.get("tempo", 90))),
        "key_scale": c.get("key_or_raga", ""),
        "time_signature": str((c.get("time_signature") or [4, 4])[0]),
        "use_format": False,
    }
    if requested_duration:
        request["audio_duration"] = max(10, min(600, float(requested_duration)))
    if model:
        request["model"] = model
    return request


def extract_data(response):
    if isinstance(response, dict) and "data" in response:
        return response["data"]
    return response


def submit(base_url, request, api_key=None):
    response = http_json(
        f"{base_url.rstrip('/')}/release_task",
        method="POST",
        payload=request,
        timeout=60,
        api_key=api_key,
    )
    data = extract_data(response)
    if not isinstance(data, dict) or not data.get("task_id"):
        raise RuntimeError(f"ACE-Step did not return a task_id: {response}")
    return data["task_id"]


def poll(base_url, task_id, api_key=None, interval=3, timeout=900):
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = http_json(
            f"{base_url.rstrip('/')}/query_result",
            method="POST",
            payload={"task_id_list": [task_id]},
            timeout=60,
            api_key=api_key,
        )
        data = extract_data(response)
        item = data[0] if isinstance(data, list) and data else data
        if isinstance(item, dict):
            status = item.get("status")
            if status == 1:
                result = item.get("result", item)
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        pass
                return result
            if status == 2:
                raise RuntimeError(f"ACE-Step generation failed: {item}")
        time.sleep(interval)
    raise TimeoutError(f"ACE-Step task {task_id} did not finish within {timeout}s")


def download_result(base_url, result, output_path, api_key=None):
    item = result[0] if isinstance(result, list) and result else result
    if not isinstance(item, dict) or not item.get("file"):
        raise RuntimeError(f"ACE-Step result did not contain an audio file: {result}")
    audio_url = item["file"]
    if audio_url.startswith("/"):
        audio_url = base_url.rstrip("/") + audio_url
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(audio_url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as response:
        Path(output_path).write_bytes(response.read())
    return item


def main():
    ap = argparse.ArgumentParser(description="Generate a SongSpec with a local ACE-Step 1.5 server.")
    ap.add_argument("song_spec")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--api-url", default=os.environ.get("ACESTEP_API_URL", "http://127.0.0.1:8001"))
    ap.add_argument("--api-key", default=os.environ.get("ACESTEP_API_KEY"))
    ap.add_argument("--model", default=None)
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--poll-interval", type=float, default=3)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--print", action="store_true", dest="print_request")
    args = ap.parse_args()

    with open(args.song_spec, encoding="utf-8") as f:
        spec = json.load(f)
    if spec.get("song_spec_version") != "1.0":
        raise SystemExit("Unsupported SongSpec version; expected 1.0")

    request = build_request(spec, duration=args.duration, model=args.model)
    os.makedirs(args.out, exist_ok=True)
    manifest_path = os.path.join(args.out, "ace-step-request.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "provider": "ace-step",
                "transport": "local-http",
                "api_url": args.api_url,
                "request": request,
                "source_song_spec_version": spec["song_spec_version"],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"ACE-Step request -> {manifest_path}")
    if args.print_request:
        print(json.dumps(request, ensure_ascii=False, indent=2))

    if not args.generate:
        print("Dry run only. Start ACE-Step locally, then add --generate to create audio.")
        return

    try:
        health = http_json(f"{args.api_url.rstrip('/')}/health", timeout=10, api_key=args.api_key)
        print(f"ACE-Step health: {health}")
        task_id = submit(args.api_url, request, api_key=args.api_key)
        print(f"ACE-Step task: {task_id}")
        result = poll(
            args.api_url,
            task_id,
            api_key=args.api_key,
            interval=args.poll_interval,
            timeout=args.timeout,
        )
        output_path = os.path.join(args.out, f"{Path(args.song_spec).stem}-ace-step.mp3")
        metadata = download_result(args.api_url, result, output_path, api_key=args.api_key)
        print(f"ACE-Step audio -> {output_path}")
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Could not reach ACE-Step at {args.api_url}. "
            f"Start the local API server first. Details: {exc}"
        )


if __name__ == "__main__":
    main()
