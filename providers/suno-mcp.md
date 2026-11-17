# Suno MCP provider

Status: placeholder adapter

The skill does not depend on Suno. The canonical contract is SongSpec 1.0.

scripts/suno_mcp.py converts a SongSpec into an inspectable provider request manifest containing:

- title
- style / creative direction
- BPM and key/raga
- instruments
- narrator and singer description
- section-tagged lyrics
- requested provider capabilities

It intentionally does not make an HTTP request or require a Suno API key.

## Local test

Run:

    python scripts/validate_song_spec.py examples/song-spec.json
    python scripts/suno_mcp.py examples/song-spec.json --out outputs --print

The second command creates outputs/suno-mcp-request.json.

## Host integration

When the host agent has the official Suno MCP integration configured, the host can use the SongSpec-derived request as its input to the Suno MCP tools.

The adapter should remain a thin translation layer. Do not put Suno-specific creative logic into the core SongSpec or SKILL.md.

## Future implementation

When a supported MCP client/runtime is available inside the target host, replace the placeholder execution step with:

    SongSpec -> capability check -> Suno MCP tool call -> FullSong artifact

Keep the placeholder path for local development and for hosts that do not expose MCP execution.
