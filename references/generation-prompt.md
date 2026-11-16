# The generation prompt

Music-generation models (Suno, Udio, Google Lyria, Stable Audio, ElevenLabs Music and similar) take a style description plus lyrics with section tags. They are the most realistic path to a sung performance today, so write this prompt with the same care as the score. Save it as `generation-prompt.md` in the outputs and show it in the reply.

Most tools have two fields: a **style / description** box with a character limit (often 200 to 1000 characters) and a **lyrics** box that accepts section tags in square brackets. Produce both, plus a longer "director's note" for tools that accept free text.

## Style field (short, dense, under ~400 characters)

Order matters: genre or tradition first, then instruments, then voice, then tempo and key, then mood words. Models weight the opening words most.

Template:

```
<tradition or fusion>, <2-4 named instruments>, <narrator description> spoken intro, <singer description> vocals, <BPM> bpm, <key or raga>, <3 mood words>, cinematic, <ending type>
```

Example (pathos version of the "none special like you" text):

```
Slow country-folk ballad with Carnatic violin, pedal steel, tanpura drone, soft brushed drums; warm older male Tamil narrator spoken intro; breathy female alto vocals with light late-onset vibrato; 62 bpm, D minor; grieving, tender, luminous; cinematic; ends on a sustained open fifth fading to river ambience
```

## Lyrics field

Use section tags the models recognise. Put the narration in the prelude as spoken text in parentheses so the model speaks rather than sings it. Mark instrumental passages explicitly.

```
[Intro: ambient river sounds, solo tanpura drone, 20 seconds]

[Spoken narration, warm older Tamil male voice]
(The backdrop story, 2-5 sentences, in the text's language)

[Instrumental: violin enters, settles into tempo]

[Verse 1]
<the user's lines, exactly as approved>

[Chorus]
<...>

[Bridge]
<...>

[Outro: motif returns on solo violin, slower; ambience returns; fade on sustained fifth]
```

Rules:
- Lyrics are the user's approved words. Do not add filler lines the model might sing.
- Keep narration short; long spoken sections tend to get sung or garbled.
- If the piece is in Tamil or another non-Latin-script language, give the lyrics in the script the user wrote them in, and add a transliteration in a second copy of the prompt in case the tool handles one better.
- Wordless passages: write `[Vocables: "aa", "ee"]` or `[Throat singing passage]` rather than inventing syllables.

## Director's note (free text, for tools that accept it or for a human producer)

Five to eight lines: the world in one sentence, the turn and where the peak note sits, the meet-then-move plan (where the prelude starts emotionally and where the conclusion lands), the fusion and its reason, what to avoid (e.g. "no drum kit", "no reverb wash on the narrator").

## Fit check

Before shipping the prompt, confirm it names: tradition, every instrument in the arrangement, narrator voice, singer voice, BPM, key or raga, the three sections, the ending. If a music tool is attached to the session and the user has asked for the audio, submit the prompt there; otherwise deliver it for the user to paste.
