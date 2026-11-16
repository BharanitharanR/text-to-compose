# Casting voices: narrator and singer

Two characters, both standing inside the backdrop world. Write each as a short spec. The spec feeds the generation prompt, any local singing or TTS engine, and the mix.

## Narrator spec

```
narrator:
  who: <a person, creature, machine or presence that belongs in the scene>
  age_and_gender: <or "none" for a robot/ghost>
  language: <the text's language unless the user asked otherwise>
  accent: <specific: "Madurai Tamil", "Glasgow", "Russian-accented British English", "none / synthetic">
  timbre: <warm, dry, gravelled, bright, whispered, metallic>
  pace: <slow and spacious / conversational / urgent>
  relationship_to_singer: <same person, older relative, stranger, the land itself, a machine observing>
  why: <one line tying the choice to the backdrop>
```

The narrator is any voice the world can hold: a grandmother on a river step, a station announcer, a child, a ship's AI, the wind given words. Contrast with the singer is a legitimate tool: a Tamil narrator handing off to a Russian-accented English singer makes a listener sit up, if the backdrop explains the pairing (a migrant kitchen, a port, a dream). Unexplained contrast is a gimmick; explained contrast is cinema.

Narration length: two to five sentences, spoken over the prelude's instrument entry, finishing before the singer's first breath. Mark pauses with line breaks.

## Singer spec

```
singer:
  speaker: <who sings: lover, elder, child, mourner, crowd, narrator-turned-singer>
  range: <"A3 to E5">   # keep melody within it; peak note at the turn
  register_weight: <chest / mixed / head>
  timbre: <breathy, bright, dark, nasal, warm, raspy>
  technique: <see table>
  language: <the text's>
  accent: <specific>
  vibrato: <none / light / wide, with onset "late" for classical Indian, "immediate" for Western pop>
  why: <one line>
```

### Technique vocabulary and what it asks of a model

| Technique | Tradition | What to write in the prompt or drive in an engine |
|---|---|---|
| Gamaka | Carnatic | oscillating slides between adjacent notes; the note is approached, not struck. Prompt: "Carnatic gamaka ornamentation, notes approached by slides" |
| Meend / andolan | Hindustani | long glides between notes; slow oscillation on a held note |
| Melisma | many | several notes on one syllable; use on the turn word only |
| Khoomei / sygyt | Mongolian | low fundamental drone with a whistled overtone melody above it. Prompt: "Mongolian throat singing, sygyt overtone whistle over a low drone" |
| Cante jondo | Flamenco | bent notes, cracked attack, long melisma on "ay" |
| Sean-nós | Irish | unaccompanied, heavily ornamented, free rhythm, no vibrato |
| Belting | pop, musical | full chest voice on high notes; only for anthems |
| Falsetto / head voice | many | light, airy top; good for lullabies and endings |
| Portamento | Western classical, jazz | smooth slide into a note |
| Vocables | Aboriginal, Mongolian, Carnatic swara passages | wordless syllables carrying melody; mark which lines |

## Fit between voice and melody

- Keep the melody inside the stated range; the top note belongs to the turn.
- Open vowels (ah, oh, ai) on sustained peaks; avoid consonant clusters on long high notes.
- Tamil and other mora-timed or syllable-timed languages sit better on even note values; English stress-timing wants dotted rhythms and syncopation.
- A breathy voice needs lighter accompaniment under it; a belted voice can sit over brass.

## When a sung voice can actually be produced

Check, in this order, and say in the render note which applied:

1. A local singing synthesizer or neural TTS on the user's own machine (they may have their own fine-tuned voice). Drive it from the singer spec, lyrics and the pitch track exported by `scripts/render.py --pitch-track`.
2. A music-generation model via the generation prompt (`references/generation-prompt.md`). This is the usual path to a real performance.
3. Nothing: ship MIDI and instrumental, and say the voice is not rendered. Do not substitute a formant or vowel synthesizer and call it a singer; the gap between that and the brief's promise is exactly what breaks immersion.
