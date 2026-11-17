# Eleven Music provider

Status: implemented API adapter

Eleven Music provides programmatic full-song generation through the ElevenLabs Music API. The current adapter targets `music_v2_5` and translates SongSpec section structure into an Eleven Music composition plan.

## Availability

Eleven Music generation is available in the ElevenLabs website's Free plan. **Music API access is not included in the Free subscription by itself.** ElevenLabs currently documents API access for paid subscribers, and its PAYG documentation says a Free account can unlock otherwise-disabled APIs, including Music, by adding PAYG balance.

For this skill, distinguish the two paths:

| Capability | Free website | API |
|---|---|---|
| Eleven Music generation | Yes | No, not from Free subscription alone |
| Full songs / vocals | Yes | Yes |
| Composition plans | Yes | Yes |
| API key required | No | Yes |
| Paid subscription required | No | Not necessarily if PAYG API access is enabled |
| Commercial rights | See current Music Terms / plan | See current Music Terms / API plan |

Official current documentation should be treated as authoritative because ElevenLabs changes plan and API availability over time.

## Local dry run

No account or API key is needed to inspect the request:

    python scripts/elevenlabs_music.py examples/song-spec.json --out outputs --print

This writes `outputs/elevenlabs-music-request.json`.

## Generate a real song

The adapter requires API access and an API key. A paid subscription is one supported route; ElevenLabs also documents PAYG as a way for Free users to unlock APIs that are otherwise disabled.

Set the key only in the process environment:

    export ELEVENLABS_API_KEY="..."
    python scripts/elevenlabs_music.py examples/song-spec.json --out outputs --generate

The generated audio is written to `outputs/elevenlabs-song.mp3`.

The adapter uses the official POST `/v1/music` endpoint with model_id `music_v2_5` and a structured composition_plan.

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

## Capability matrix

Current Eleven Music capabilities relevant to this skill:

- full_song: yes
- vocals: yes
- lyrics: yes
- instrumental: yes
- composition_plan: yes
- audio_reference: yes in the Eleven Music product; not yet exposed by this adapter
- inpainting: yes in the product/API ecosystem; not yet exposed by this adapter
- streaming: yes via the Music API; not yet exposed by this adapter
- stems: available on supported plans; not yet exposed by this adapter
- model: `music_v2_5`

The adapter intentionally exposes only the subset currently represented by SongSpec.

## Licensing note

ElevenLabs states that Music v2.5 is built with licensed music data and that usage rights depend on the applicable plan and Music Terms. Free-plan website generation and API/PAYG generation should not be treated as having identical commercial rights. Verify the current terms before commercial distribution.
