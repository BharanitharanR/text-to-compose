# Changelog

## 1.1.0 — 2026-11-17

- Added canonical provider-neutral SongSpec schema.
- Added SongSpec example and validator.
- Added local SongSpec-to-reference-renderer wrapper.
- Added Suno MCP placeholder adapter that produces an inspectable MCP request manifest without calling Suno.
- Documented the provider boundary: Suno MCP is optional and the skill remains agent/provider neutral.

## 1.0.0 — 2026-11-17

Initial commercial-ready portable release.

- Added explicit Agent Skills portability and host-agent boundary guidance.
- Added MIT license metadata to SKILL.md.
- Added package version metadata.
- Added installation and compatibility documentation.
- Added Python runtime dependency declaration.
- Clarified behavior when a host agent cannot execute local rendering scripts.
- Clarified that customer-specific data must not be stored in the skill package.
