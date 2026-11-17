<<<<<<< HEAD
# ACE-Step 1.5 local provider

Status: supported local provider

ACE-Step 1.5 is an open-source local music-generation engine that can generate
full songs from text and lyrics, including vocals. The upstream project provides
a REST API and macOS Apple Silicon launch scripts.

The skill keeps ACE-Step outside the canonical SongSpec. SongSpec remains the
provider-neutral composition contract.

## Install on macOS Apple Silicon

Use the upstream repository:

```bash
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5

curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

chmod +x start_gradio_ui_macos.sh start_api_server_macos.sh
./start_api_server_macos.sh
```

The API is normally available at:

```
http://127.0.0.1:8001
```

The first run downloads the required model files.

For Apple Silicon, the upstream macOS launcher uses the MLX backend. The project
also supports MPS/PyTorch and CPU fallback. On memory-constrained machines,
start with the 2B turbo DiT and 0.6B LM configuration; do not select XL models
on an 8 GB unified-memory Mac.

## Verify the server

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/v1/models
```

## Test the skill adapter

From the text-to-compose repository:

```bash
python scripts/validate_song_spec.py examples/song-spec.json
python scripts/ace_step.py examples/song-spec.json --out outputs --print
```

That creates an inspectable ACE-Step request without generating audio.

To generate:

```bash
python scripts/ace_step.py examples/song-spec.json --out outputs --generate
```

The adapter submits SongSpec lyrics and musical direction to the local ACE-Step
REST API, polls the task, and saves the returned MP3 under `outputs/`.

## Environment variables

```
export ACESTEP_API_URL=http://127.0.0.1:8001
# Only needed if you configured ACE-Step with API-key authentication:
export ACESTEP_API_KEY=...
```

## Capability boundary

- full_song: yes
- vocals: yes
- lyrics: yes
- instrumentation/style: yes
- local REST API: yes
- hosted service required: no
- API key required: no, unless the local server is configured to require one
- commercial licensing: verify the current ACE-Step project/model license before commercial distribution

The adapter is intentionally thin. Creative intelligence stays in Text-to-Compose
and the canonical SongSpec; ACE-Step supplies audio generation.
=======
# ACE-Step provider

Status: implemented local API adapter (`scripts/ace_step.py`)

[ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) is an open-source music model that runs on the user's own machine. It generates full songs with sung vocals from a style caption and section-tagged lyrics. No account, API key or credits are needed; songs stay on local disk.

## Setup (once)

    git clone https://github.com/ace-step/ACE-Step-1.5.git
    cd ACE-Step-1.5
    uv sync

Start the REST API server (first start downloads about 8 GB of model weights):

    ./start_api_server_macos.sh   # Apple Silicon (MLX backend)
    ./start_api_server.sh         # Linux / Windows with an NVIDIA GPU

The server listens on `http://127.0.0.1:8001`. Set `ACESTEP_API_URL` to use another address.

## Use

Dry run (no server needed; writes `outputs/ace-step-request.json`):

    python scripts/ace_step.py song-spec.json --out outputs --print

Generate:

    python scripts/ace_step.py song-spec.json --out outputs --generate --seed 42

Options: `--steps` (default 8, turbo model), `--duration` (seconds, overrides the SongSpec), `--no-thinking` (skip ACE-Step's planning LM: faster, usually weaker).

## Mapping

SongSpec -> ACE-Step `/release_task`:

| SongSpec | ACE-Step |
|---|---|
| creative.style, instruments, vocals.singer, metadata.tags | `prompt` (compact caption; parentheticals and stage directions dropped) |
| lyrics.sections in arrangement order | `lyrics` with `[Intro]`, `[Verse]`, `[Interlude]`, `[Outro]`... tags |
| creative.tempo | `bpm` |
| creative.key_or_raga | `key_scale`; church modes fold to major/minor (Dorian -> minor). Ragas and free text are left to ACE-Step's LM |
| creative.time_signature | `time_signature` (numerator) |
| metadata.duration_seconds, else section beats / BPM | `audio_duration` (10-600 s) |
| vocals.language | `vocal_language` ISO code |

The adapter turns off ACE-Step's caption and language rewriting (`use_cot_caption`, `use_cot_language`) because the SongSpec already holds those decisions. `thinking` stays on so ACE-Step's planning LM still shapes the audio.

## What ACE-Step cannot do

- **Spoken narration.** It only sings. Sections marked `spoken` become instrumental `[Intro]`/`[Interlude]` slots, and the adapter reports their text as not rendered. Record the narrator separately (TTS or a person) and mix it over the intro if the piece needs it.
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
- runs offline: yes, after the model download
- cost: none beyond local compute

## Speed

On an M2 Pro with 16 GB the turbo model with the 0.6B planning LM took several minutes per song. The first request after a server start also loads the models. Measured numbers for the A/B test are in `evals/`.

## Licence

ACE-Step 1.5 is released under the MIT licence. Read the repository's licence and disclaimer section before commercial distribution of generated audio.
>>>>>>> ac11d31 (feat: add ACE-Step 1.5 local provider and A/B eval (v1.4.0))
