# ACE-Step 1.5 local provider

Status: supported local provider (`scripts/ace_step.py`)

[ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) is an open-source local
music-generation engine. It generates full songs with sung vocals from a style
caption and section-tagged lyrics, and exposes a REST API. No account, API key or
credits are needed for a default local install; songs stay on local disk.

The skill keeps ACE-Step outside the canonical SongSpec. SongSpec remains the
provider-neutral composition contract.

## Install on macOS Apple Silicon

```bash
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5

curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

chmod +x start_gradio_ui_macos.sh start_api_server_macos.sh
./start_api_server_macos.sh
```

On Linux or Windows with an NVIDIA GPU use `./start_api_server.sh`.

The API is normally available at `http://127.0.0.1:8001`. The first run
downloads the model files (about 8 GB).

For Apple Silicon, the upstream macOS launcher uses the MLX backend. The project
also supports MPS/PyTorch and CPU fallback. On memory-constrained machines,
start with the 2B turbo DiT and 0.6B LM configuration; do not select XL models
on an 8 GB unified-memory Mac.

## Verify the server

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/v1/models
```

## Use the skill adapter

Dry run (no server needed; writes `outputs/ace-step-request.json`):

```bash
python scripts/validate_song_spec.py examples/song-spec.json
python scripts/ace_step.py examples/song-spec.json --out outputs --print
```

Generate:

```bash
python scripts/ace_step.py examples/song-spec.json --out outputs --generate --seed 42
```

The adapter submits the request to `/release_task`, polls `/query_result`, and
saves `outputs/ace-step-song.wav` plus `outputs/ace-step-result.json`.

Options:

- `--seed` fixed seed for a repeatable render
- `--steps` diffusion steps (default 8, for the turbo model)
- `--duration` seconds, overriding the SongSpec
- `--no-thinking` skip ACE-Step's planning LM (faster, usually weaker)
- `--server` (alias `--api-url`) the API address
- `--api-key` only if the local server requires authentication
- `--model` a specific DiT model loaded by the server
- `--timeout` seconds to wait for a render (default 1800)

## Environment variables

```bash
export ACESTEP_API_URL=http://127.0.0.1:8001
# Only needed if you configured ACE-Step with API-key authentication:
export ACESTEP_API_KEY=...
```

## Mapping

SongSpec -> ACE-Step `/release_task`:

| SongSpec | ACE-Step |
|---|---|
| creative.style, instruments, vocals.singer, metadata.tags | `prompt` (compact caption; parentheticals and stage directions dropped) |
| instrumental specs: motif and ending | added to `prompt` with "no vocals" |
| lyrics.sections in arrangement order | `lyrics` with `[Intro]`, `[Verse]`, `[Interlude]`, `[Outro]`... tags |
| instrumental specs: arrangement sections | one tag line each: type, mood, energy as words, texture, transition, instruments |
| extra.narration_bed (true) | caption adds "soft background bed under spoken voiceover, sparse, low-mid range kept clear, no lead melody, no vocals"; every section tag gets "no lead melody, low-mid clear" and energy words never read as driving or full |
| creative.tempo | `bpm` |
| creative.key_or_raga | `key_scale`; church modes fold to major/minor (Dorian -> minor), common ragas map via `Sa = X`. Other free text is left to ACE-Step's LM |
| creative.time_signature | `time_signature` (numerator) |
| metadata.duration_seconds, else section beats / BPM | `audio_duration` (10-600 s) |
| vocals.language | `vocal_language` ISO code |

The adapter turns off ACE-Step's caption and language rewriting (`use_cot_caption`,
`use_cot_language`) because the SongSpec already holds those decisions. `thinking`
stays on so ACE-Step's planning LM still shapes the audio.

ACE-Step reads the section tags as the order of the piece, not as exact timings.

## What ACE-Step cannot do

- **Spoken narration.** It only sings. Sections marked `spoken` become instrumental
  `[Intro]`/`[Interlude]` slots, and the adapter reports their text as not rendered.
  Record the narrator separately (TTS or a person) and mix it over the intro.
- **Exact melody.** It does not take the ABC score or motif; melody is the model's own.
- **Separate ambience layers.** Ambience can only be suggested in the caption.
- **Ragas and talas** are not first-class parameters; describe them in the caption.

## Capability matrix

- full_song: yes
- vocals: yes (50+ languages; English and Chinese strongest)
- lyrics: yes
- instrumental: yes
- spoken narration: no
- melody/score control: no
- reference audio / cover / repaint: yes in ACE-Step; not yet exposed by this adapter
- local REST API: yes
- hosted service required: no
- API key required: no, unless the local server is configured to require one
- runs offline: yes, after the model download
- cost: none beyond local compute
- commercial licensing: verify the current ACE-Step project/model license before commercial distribution

## Speed

On an M2 Pro with 16 GB the turbo model with the 0.6B planning LM took several
minutes per song. The first request after a server start also loads the models.
Measured numbers for the A/B test are in `evals/`.

The adapter is intentionally thin. Creative intelligence stays in Text-to-Compose
and the canonical SongSpec; ACE-Step supplies audio generation.
