# terminology.md — what the words mean here

Small file, load-bearing. Most of the ways this build could go wrong start with one of these words drifting.

---

### Captioning vs editing

**Captioning** — working out what was said and when, grouping it into readable cards, and putting them on the video. The tool does this.

**Editing** — deciding what is in the video at all: what gets cut, where it starts, where it ends. You do this, by hand, in CapCut, before anything reaches this workspace.

The line between them is not stylistic. Anything that ranks, scores, recommends, removes, or picks between alternatives is editing wearing captioning's clothes. `governance.md` rule 1 lists the specific forms.

---

### Session · clip · export

**Session** — everything recorded for one video.

**Clip** — one file from the phone, a few seconds long. **Not a take and not a scene.** You film in bursts because you forget your text past a few seconds, so one continuous stream of speech comes out as dozens of clips, and a sentence routinely starts in one and finishes in the next.

**Export** — the single file CapCut produces once you have assembled and cut those clips. **This is the only thing the pipeline ever sees.** The joins between clips are baked into it and invisible, which is why nothing in this workspace knows about clips at all.

---

### Card · line · the two limits

**Card** — one caption as it appears on screen: a phrase, held for a set time, replaced by the next one.

**Line** — one row of text inside a card. **A card is one row**, since 2026-07-30: two rows read as a block to be scanned rather than a line to be read. `caption.max_lines` and `typography.caption_size_px` move together — see the note on both values in `_config/edit-defaults.yaml`.

**The ceiling** is a rule: no card is on screen longer than 2.5s. It is also what stops a caption sitting through a long pause — cards are stretched to meet the next one so they do not flicker between phrases, and the ceiling is where that stretching stops.

**The floor** — 0.6s — is a rule only where it can be met. Cards run wall-to-wall, so a card cannot be held past the one after it; the only way to lift a short card over the floor is to join it into the card before, and that fails when the joined text overruns the row. What is guaranteed is narrower and worth stating exactly: **every under-floor card that could be joined, was.** The rest are reported, not treated as bugs. Since 2026-07-31.

---

### Rules vs diagnostics

In `_config/edit-defaults.yaml`. A **rule** is enforced and a violation is a bug. A **diagnostic** is measured, printed, and acted on by nothing.

The distinction exists because four caption values could not all be true at once, and a flat list let them sit together looking equally binding. **Card duration is a rule. Words per card and reading speed are diagnostics** — they cannot all be rules, because captions track speech exactly, so a card's duration is words divided by how fast you talk rather than a free choice.

---

### Lexicon · correction · promotion

**Lexicon** — `_config/lexicon.txt`. The terms handed to the transcriber before it starts, so it leans toward them. Proper nouns, brand names, acronyms — the words that carry the meaning and that speech-to-text reliably mangles.

**Correction** — a word you changed in `01-transcript.json` after seeing it come out wrong. The tool finds it by comparing your version against `01-transcript-raw.json`, which nothing ever edits.

**Promotion** — a corrected word reaching two separate runs, at which point it is *proposed* for the lexicon. **Counted in runs, never in occurrences:** a word you fixed six times in one video was still only wrong once, and counting the occurrences would promote it off the back of a single take.

---

### Words that mean two things

Each of these named two different objects in this workspace at once. The second
column is what the word means **here**; the rest is what someone would otherwise
reach for.

**Script** — the words you say in a take. That is the default meaning and the
only one you have to say plainly. A Python file under `stages/*/scripts/` is a
**python script**, said with the word "python" in front of it, or it is not
about this workflow at all.

**Hook** — the thing in `.claude/hooks/` that runs `tools/sync.py` after every
edit. Nothing else. The big text card at the top of a reel — Inter 800 at
85–110 px, the Poppins variant, `HOOK_SIZE = 96` — is the **opener**, it is a
deferred phase, and `reference/source-specs/EXCLUSIONS.md` says do not build it.
The two source specs beside that file still call it the hook; they are a record
of someone else's reels analysed frame by frame and are left as written.

**Clip** — one file off the phone, as under *Session · clip · export* above.
A **segment** is a stretch `01b_calibrate` found for itself by measuring, and
the two need not match: the stage may find three segments in a video you
assembled from nine clips (`governance.md` rule 4). `between_segment_correction`
and `within_segment_correction` act on segments. Reading `kept 3 of 14` as
"found 3 of my 9 clips" is the mistake this prevents.

**Render** — three things, and only the first is a place in this workspace:
`stages/03_render`, which burns the cards on; the finished file you post; and
the `render:` block in `_config/edit-defaults.yaml`. When a video comes out
wrong the fault is usually upstream of the render stage — in the transcript, the
cards, or the levelling — so "the render is wrong" is a symptom, not an address.

**Rule** — a value under `rules:` in `_config/edit-defaults.yaml`, or one of the
four in `governance.md` that no component may break. What you write by hand in
`memory/preferences.md` is an **override**: it replaces one `edit-defaults.yaml`
value for this deployment, and the line is written `**Override:**`.

**Animation** — not a word this workspace uses. The caption setting is
`caption_motion: none` (`_config/edit-defaults.yaml`), meaning cards do not pop,
highlight word by word, or type themselves on. The separate, unstarted project
of drawing visuals into videos is the one called animation, and it is not here.
Deleting "everything about animation" must not touch `caption_motion`.
