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
