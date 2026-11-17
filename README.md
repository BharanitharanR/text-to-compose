# Text to Song Composer

**Portable Agent Skill — v1.4.0**

Turn poems, stories, memories, diary entries, speeches, prayers, scenes, and other written text into an original song concept and playable musical artifacts.

## What this is

Text to Song Composer is an **Agent Skills-compatible skill package**. The product is the skill itself: its instructions, composition methodology, musical references, rendering scripts, and assets.

It is intentionally **agent-neutral**. A compatible AI agent should be able to load the package without requiring a particular model provider, application, API, or UI.

## Package

```
text-to-compose/
├── SKILL.md
├── VERSION
├── CHANGELOG.md
├── LICENSE
├── requirements.txt
├── schemas/
├── examples/
├── providers/
├── assets/
├── references/
└── scripts/
```

## Install

Copy or clone this directory into the skill directory supported by your AI agent. The exact installation location is host-specific.

## Optional local rendering

```bash
python -m pip install -r requirements.txt
python scripts/render.py song.json --out outputs/
python scripts/check_audio.py song.json outputs/song.wav --midi outputs/song.mid
```

## SongSpec and providers

SongSpec 1.0 is the canonical provider-neutral representation.

Validate:

```bash
python scripts/validate_song_spec.py examples/song-spec.json
```

### Suno MCP

Suno MCP is an optional hosted provider. The account/host must have Suno MCP access. The skill can compile a SongSpec into an inspectable request manifest:

```bash
python scripts/suno_mcp.py examples/song-spec.json --out outputs --print
```

If the host cannot access Suno MCP, use another provider rather than changing SongSpec.

### ACE-Step 1.5 — free/local

ACE-Step 1.5 is the main local full-song provider. It can run on macOS Apple Silicon using the upstream MLX launcher and exposes a local REST API.

Install the upstream engine:

```bash
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
chmod +x start_api_server_macos.sh
./start_api_server_macos.sh
```

Default API: `http://127.0.0.1:8001`.

From this repository, dry-run the adapter:

```bash
python scripts/ace_step.py examples/song-spec.json --out outputs --print
```

Generate an actual song:

```bash
python scripts/ace_step.py examples/song-spec.json --out outputs --generate
```

Environment variables:

```bash
export ACESTEP_API_URL=http://127.0.0.1:8001
# Only if your local ACE-Step server was configured with authentication:
export ACESTEP_API_KEY=...
```

See `providers/ace-step.md` for the full setup and troubleshooting path.

### Eleven Music

Eleven Music remains an optional paid/programmatic provider. The adapter supports dry-run and API generation when API access is configured.

```bash
python scripts/elevenlabs_music.py examples/song-spec.json --out outputs --print
```

See `providers/elevenlabs.md`.

## Provider philosophy

The skill separates:

1. **Capability** — can the engine make what the user asked for?
2. **Access** — can the host actually reach the engine?
3. **Payment** — is generation free, paid, or credit-based?
4. **Licensing** — can the resulting audio be used commercially?

The same SongSpec should move between providers without rewriting the composition logic.
