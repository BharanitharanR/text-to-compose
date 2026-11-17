# Eleven Music provider

Status: implemented API adapter

Eleven Music provides programmatic full-song generation through the ElevenLabs Music API. The current adapter targets music_v2_5 and translates SongSpec section structure into an Eleven Music composition plan.

## Local dry run

No account or API key is needed to inspect the request:

    python scripts/elevenlabs_music.py examples/song-spec.json --out outputs --print

This writes outputs/elevenlabs-music-request.json.

## Generate a real song

The Music API requires a paid ElevenLabs subscription/API access.

Set the key only in the process environment:

    export ELEVENLABS_API_KEY="..."
    python scripts/elevenlabs_music.py examples/song-spec.json --out outputs --generate

The generated audio is written to outputs/elevenlabs-song.mp3.

The adapter uses the official POST /v1/music endpoint with model_id music_v2_5 and a structured composition_plan.

## Mapping

SongSpec -> Eleven Music:

- creative.style -> positive styles
- creative.tempo -> BPM style
- creative.key_or_raga -> tonal direction
- creative.instruments -> positive styles
- creative.vocals -> vocal/language/technique styles
- lyrics.sections + arrangement.sections -> composition-plan chunks
- section start_beat / end_beat -> chunk duration using BPM
- section purpose/instruments -> local positive styles

The adapter is intentionally thin. SongSpec remains provider-neutral.

## Licensing note

ElevenLabs states that Music API access is available to paid subscribers and that commercial rights depend on the applicable subscription/tier and Music Terms. Customers should verify the current terms before using generated music commercially.
