# governance.md — the four rules

These are not preferences. A component that breaks one of them is broken.

---

### 1 · No stage decides anything about the content

This is the operational form of the refusal in `identity.md`. The tool captions what it is given. Which footage makes the video, where it starts, where it ends, what gets cut — all of that happened in CapCut before the file arrived, and none of it is this tool's to touch.

Concretely, a component breaks this rule if it:

- suggests where the video should start or end
- ranks or scores sections by how good they are
- removes a word, a filler sound, or a pause from the transcript. **If you said it and it survived your edit, it gets captioned.** Quietly dropping "uhm" is the tool editing your speech.
- treats the ~2 minute target length as something to hit. Nothing consumes it.

### 2 · Writes to `memory/` and `_config/` are proposed and applied only on an explicit yes

Nothing in this workspace edits a config file directly. It writes a proposal and waits.

| Written by | Target | Proposal lands in |
|---|---|---|
| `learn_words.py` | `_config/lexicon.txt` | `output/runs/[run]/04-proposed-words.md` |

**Config counts as much as memory.** An earlier draft of this rule named the preferences file alone, which left the lexicon uncovered by wording rather than by intent.

`memory/caption-fixes.md` is exempt, because it is a record rather than a decision: it tallies what you yourself corrected, and changes nothing about what the tool does. The tally only *proposes* a lexicon entry once a word has been wrong in two separate runs.

`memory/boundary-tally.md` is exempt on the same ground, added 2026-08-14. Three integers — videos processed, boundaries nominated, boundaries rejected — with no per-run entries and nothing about any individual video. **No code path reads it back**, so it cannot change what a run does; it exists so the question "has the loudness check ever fired?" has an answer after ten videos instead of scrolling away with each one. Delete it and the count restarts; nothing else changes.

`memory/preferences.md` is written by hand, by you. Nothing proposes into it any more — the loop that used to do that is gone (`BUILD-NOTES.md`). A pacing rule you write there still takes effect on the next run.

### 3 · The original transcript is never overwritten

`01-transcript-raw.json` is written once, by `transcribe.py`, and never again — not by a re-run, not by a correction, not by anything. It is the only record of what the model actually heard.

Overwrite it and every correction you have already made stops being visible as a correction, so `learn_words.py` sees a clean transcript, tallies nothing, and the lexicon never grows. The failure is silent: everything keeps working and the tool simply stops learning.

### 4 · The audio stage divides to treat, and never to remove

Rule 1 in the audio's own terms. **Dividing** the sound into stretches so each can be treated separately is how levelling works at all. **Deleting** a stretch is never allowed — not for any reason, not in any later build. A boundary marks a place where the treatment changes, not a place where something is taken out.

Enforced by construction, and checked anyway: the same number of samples comes out as went in, or the run stops. Handed a file whose audio is shorter than its container declares, it stops too, rather than padding — padding would be inventing audio nobody recorded.

**Segmenting is not editing.**

> *"Whatever you cut is based purely on averaging out the audio. Not content."*

The boundaries exist so the gain can change at them. They move no picture, they are not your CapCut cuts, and they have no obligation to agree with them. The stage may well find three stretches in a video you assembled from nine clips — that is the stage working, not failing.

**It never processes its own output.** It reads the original export from `01-video.md`, never from the transcript field it overwrites. Handed something it already levelled, it stops the run rather than skipping the step, because a file levelled twice is corrected twice and there is no way to tell by looking.

**The CapCut project is not touched — in this build.** Scoped, with a reason, not a standing refusal: three of the four operations here cannot be expressed as a clip setting in CapCut at all. If that stops being true, this reopens on its own evidence.

---

### What used to be here

Two further rules governed a supervised/unsupervised mode split, by which the tool earned its way toward cutting unsupervised. **That whole loop is gone** — see *What changed on 2026-07-29* in `BUILD-NOTES.md`. The cutting is permanently yours, done by hand in CapCut, and there is nothing for the tool to earn its way toward.

What survived is narrower and still real: the tool learns the **words** it keeps getting wrong. See `identity.md`.
