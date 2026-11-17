# Changelog

## 1.4.0 — 2026-11-17

- Added ACE-Step 1.5 as a supported local full-song provider.
- Added a SongSpec-to-ACE-Step REST API adapter with dry-run and real generation modes.
- Added ACE-Step provider documentation and macOS Apple Silicon setup instructions.
- Added provider guidance for choosing local ACE-Step when hosted providers are unavailable.
- Kept provider-specific execution outside the canonical SongSpec.

## 1.3.0 — 2026-11-17

- Clarified Eleven Music Free website availability versus Music API access.
- Added PAYG-aware provider guidance for Eleven Music API access.
- Added an Eleven Music capability matrix.
- Updated provider-selection guidance to separate capability, access, payment, and licensing.
- Corrected the provider documentation so a paid subscription is not described as the only possible route to API access.

## 1.2.0 — 2026-11-17

- Added Eleven Music provider adapter targeting the Eleven Music v2.5 API.
- Added SongSpec-to-Eleven composition-plan translation.
- Added local dry-run request generation and optional real API execution via ELEVENLABS_API_KEY.
- Added Eleven Music provider documentation.
- Kept Suno MCP as an optional placeholder provider.

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
