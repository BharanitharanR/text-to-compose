# Text to Song Composer

**Portable Agent Skill — v1.0.0**

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
├── README.md
├── requirements.txt
├── assets/
├── references/
└── scripts/
```

## Install

Copy or clone this directory into the skill directory supported by your AI agent.

The exact installation location is host-specific. The skill package itself does not assume Claude, ChatGPT, Codex, Adiyan, or another particular agent.

For an Agent Skills-compatible runtime:

1. Make the `text-to-compose` directory available to the runtime's skills directory.
2. Ensure `SKILL.md` is discoverable by the runtime.
3. The agent should load the skill when the user's request matches its description.

## Optional local rendering

The composition workflow can produce MIDI and WAV artifacts when the host agent permits local script execution.

Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Then:

```bash
python scripts/render.py song.json --out outputs/
python scripts/check_audio.py song.json outputs/song.wav --midi outputs/song.mid
```

FluidSynth and a General MIDI SoundFont are optional. If unavailable, `render.py` uses its built-in synthesizer.

If the host agent cannot execute scripts, the skill still works for composition, score generation, arrangement, and generation-prompt creation; the agent should report that binary audio artifacts were not rendered.

## Product boundary

The portable package contains:

- composition instructions in `SKILL.md`
- musical/cultural references
- voice and mood guidance
- rendering and verification scripts
- templates/assets

The host agent provides:

- the language model
- conversation/UI
- file permissions
- optional code execution
- optional music-generation or singing tools

This separation is intentional so the skill can be distributed to multiple compatible agent runtimes.

## Versioning

The package follows semantic versioning.

- `VERSION` contains the current package version.
- `CHANGELOG.md` records user-visible changes.
- Releases should be tagged in Git as `vMAJOR.MINOR.PATCH`.

## License

MIT. See `LICENSE`.

## Commercial distribution

The MIT license permits commercial use, modification, and redistribution subject to its terms. If you distribute proprietary additions, services, hosted APIs, or premium reference content alongside this package, license those components separately and make the boundary explicit.

## Compatibility

This package targets the Agent Skills directory format and keeps runtime-specific assumptions out of the skill instructions.

Compatibility with a particular agent depends on that agent supporting the Agent Skills format and on its own policies around script execution, file access, and external tools.
