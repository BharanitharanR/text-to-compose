# Carnatic (South Indian classical)

Reach for it: Tamil, Telugu, Kannada or Malayalam text; devotion, longing, lyric poetry, dawn and dusk rituals, a grandmother's voice, temple and river settings.

## Melodic logic: raga, not key

A raga is a scale plus rules of movement and ornament. Pick one by mood, state its arohana (ascent) and avarohana (descent) in the brief, and keep the melody inside them. Western letter names below assume Sa = C; transpose Sa to suit the singer's range.

| Raga | Scale (Sa=C) | Mood it carries |
|---|---|---|
| Mohanam | C D E G A (pentatonic major) | joy, open sky, children, festival |
| Kalyani | C D E F# G A B (Lydian) | brightness with longing, evening hope |
| Shankarabharanam | C D E F G A B (major) | grandeur, calm devotion |
| Kharaharapriya | C D Eb F G A Bb (Dorian) | tenderness, gentle sorrow |
| Hindolam | C Eb F Ab Bb | night, mystery, stillness |
| Shubhapantuvarali | C Db Eb F# G Ab B | deep pathos, loss |
| Sindhu Bhairavi | C Db Eb F G Ab Bb (with chromatic touches) | yearning, folk devotion, closing pieces |
| Revati | C Db F G Bb | prayer at dawn, austerity |
| Amritavarshini | C E F# G B | rain, relief, release |

Rules of movement: some ragas skip notes in ascent and not in descent (vakra or zig-zag phrases). When unsure, write smooth stepwise motion and one characteristic leap.

## Ornament: gamaka

Notes are approached, not struck. Write the melody plainly, then mark gamaka on long notes and on the turn word: an oscillation between the note and its upper or lower neighbour. In the generation prompt say "Carnatic gamaka ornamentation". In MIDI, `scripts/render.py` can add pitch-bend oscillation to notes tagged `"gamaka": true`.

## Rhythm: tala

| Tala | Beats | Use |
|---|---|---|
| Adi | 8 (4+2+2) | default; most songs |
| Rupaka | 6 (2+4) or 3 | lighter, lilting |
| Misra Chapu | 7 (3+4) | urgency, devotion with drive |
| Khanda Chapu | 5 (2+3) | folk energy |

Tempo (kalam): slow 50 to 70 BPM for pathos and prayer, medium 80 to 110 for narrative, fast above 120 for festival.

## Form

- **Alap** (free rhythm, no drum) introduces the raga: ideal for the prelude.
- **Pallavi** (refrain) then **anupallavi** (second section, higher) then **charanam** (verse) returning to the pallavi. The pallavi is where the user's turn line often belongs.
- Close with the pallavi one last time, slower, over the drone.

## Instruments

- **Tanpura**: constant drone on Sa and Pa (root and fifth). Always present; it is the floor of the world.
- Melody: **veena** (plucked, grave), **violin** (held upright, sliding), **venu** (bamboo flute, breathy), **nadaswaram** (loud double reed, outdoors, weddings and temples).
- Rhythm: **mridangam** (double-headed drum), **ghatam** (clay pot), **kanjira** (small frame drum), **morsing** (jaw harp).
- Fusion partners that sit well: cello doubling the veena, a soft electric piano on Sa-Pa, Celtic fiddle trading phrases with Carnatic violin.

## What outsiders get wrong

- Adding chord progressions. Carnatic music is modal over a drone; harmony is implied, not played. A single drone plus melody is correct; a I-IV-V progression is not.
- Immediate wide vibrato. Carnatic voices use gamaka, not Western vibrato.
- Drum kit. Use mridangam or ghatam.
- Ending on a dominant chord. End on Sa, usually held over the drone.
- Treating a bhajan or a devotional text casually: keep the setting respectful, and say in the brief that it is an original composition, not a traditional kriti.
