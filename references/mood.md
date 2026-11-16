# Reading mood: the text, the turn, and the listener

## The turn

A text's mood is fixed by its turn, the line where meaning tips. Read the whole text before deciding anything, then find the line that, if removed, would change the world the song lives in.

Worked example:

> All around the world, there was none special like you.

Alone, this is praise addressed to someone present. Pep, warmth, a country or pop-folk world, major key, mid tempo, a bright voice.

> All around the world, there was none special like you.
> Maybe that's why you went to heaven to be with people like you.

The second line is the turn. Now the first line is spoken to someone gone. Pathos, slow, minor or a mournful raga, a voice with air in it, the high note on "heaven" and a conclusion that does not fully resolve.

Signals that a turn is present: a shift in tense (was / is), a change of addressee, a word of departure or arrival, a question after statements, a sudden concrete detail after abstraction, an "and yet", "maybe", "still", "but".

## When the text is two-faced

Sometimes the text ends before its turn: two lines that could honestly live in two different worlds. Do not pick one by coin-flip and do not ask "what mood are you in". Ask the **fork question**: name both worlds as vivid, concrete choices. The precision of the question is the point; a good fork question feels like the composer already half-knows.

Shapes that work:

- Addressee: "Is this sung across a dinner table, or to someone who isn't here anymore?"
- Scale: "One voice alone at night, or a crowd singing it back?"
- Time: "Is this the morning after, or the night before?"
- Register: "A lullaby someone is whispering, or an anthem a stadium is shouting?"
- Place: "Does this live in a temple courtyard or a train platform?"

Offer two, at most three. Make each answer imply a complete world so the user's pick settles key, tempo, voice and instruments at once. If the user replies with something that is neither, take that as the world.

Ask only when the text truly has two faces. If a turn is present, trust it even when the user is cheerful in the chat; the song is about the text.

## The listener

Separate three things:

| Layer | What it decides | Where it comes from | Strength |
|---|---|---|---|
| Mood of the text | the destination: what the song is about and where it lands | the text and its turn | strong, always used |
| Mood of the listener now | the starting point: where the prelude meets them | explicit statements; the conversation's prior subject; profile notes on what lifts or sits with them | use only when strong |
| Standing taste | instruments, voices, languages, worlds they love or avoid | `listener-profile.yaml`; things said in chat | stable, always consulted |

Weak signals (hour of day, message length, punctuation) may nudge tempo by a few BPM or the prelude's dynamic level. They never change the world, the key or the voice.

**Meet, then move.** Open the prelude where the listener is, then lead them along the text's arc. Low listener plus grieving text: open low, hold it in the verse, lift one step in the conclusion. Bright listener plus grieving text: warmer prelude, the fall comes in the verse, the conclusion consoles. Low listener plus joyful text: a quiet, slow prelude that earns the brightness rather than starting there.

State the assumed starting mood in the brief in one neutral clause ("starting mood assumed: quiet, reflective"). Never describe the user's feelings to them ("you seem sad"). Let them correct the assumption.

## The profile

`listener-profile.yaml` lives beside the skill, in the project, or in the working directory. Read it before composing. After the user reacts to a song, offer one line to add. Record only what they said or confirmed:

- "the morin khuur one was the favourite" → `instruments_loved: [morin khuur]`, `past_songs[...]: reaction: "favourite so far"`
- "too fast" → `past_songs[...]: reaction: "too fast"` and a note under `tempo_notes`
- nothing said → nothing written

Do not record inferred moods, and do not record anything under health or hard personal circumstances; the song can meet those without the file remembering them.
