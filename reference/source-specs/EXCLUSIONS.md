# Excluded on record — spec values that are deliberately not in the config

Values present in the two source specs beside this file and deliberately **not**
extracted into `_config/edit-defaults.yaml`. Silent omission is what removed the
reading-speed ceiling the build notes asked for, so nothing is left out quietly.

This is provenance. No script reads it, and `edit-defaults.yaml` points here so
that the file a caption task loads stays down to its operative values.

---

## Removed 2026-07-29, when the cutting moved to CapCut by hand

Nothing in this workspace cuts anything any more, so these had no reader. A
config value nothing reads is worse than a missing one: it reads as a setting
you could change. Kept here with their reasoning intact.

| Value | Was | Note |
|---|---|---|
| `cutting.remove_silence_over_ms` | 250 | edit-spec, marked (e) — an ESTIMATE, and named there as "the main lever". Was overridable from `memory/preferences.md`. |
| `cutting.filler_sounds` | `["uhm", "um", "uh", "ehh", "eh", "er", "erm", "ah", "hmm", "mmm", "like um"]` | NOT from either spec — the PRD names "uhm, ehh, and similar". |
| `cutting.transition` | `hard_cut` | edit-spec section 3 |
| `cutting.align_cuts_to_caption_boundaries` | `false` | edit-spec section 3 |
| `cutting.cut_at_clause_boundary` | `true` | edit-spec section 3 |
| `breaks` | — | trim at a clip break, never mark one, never split a caption there, never merge across. The person's burst-filming method, which governed more of the old build than anything in the specs. It now governs CapCut instead: by the time the export reaches this pipeline the joins are invisible. |
| `min/target/max_shot_length_s` | 1.5 / 3.5 / 6.0 | edit-spec, reported-only diagnostics. Measured on CONTINUOUS LONG TAKES; never transferred to clips a few seconds long. With no cuts there are no shots to measure. |

The wider story of that removal — what went, what survived, and why the
cut-proposal loop cannot come back — is in `BUILD-NOTES.md`.

## Excluded at extraction time

| Value | Why not extracted |
|---|---|
| `max_chars_per_line: 26` | edit-spec s2. Does not fit the frame at the specified font size. Derived instead — see `geometry.chars_per_line_derived`. |
| `overlay_rules` | edit-spec s3. B-roll overlays — DEFERRED PHASE, parked by the person. Do not build. |
| opener card | edit-spec s4 + typography-spec rows, both of which call it the *hook*. DEFERRED PHASE. Do not build. **Called the opener here on purpose:** in this workspace *hook* means the thing in `.claude/hooks/` that runs the checks after an edit. |
| `HOOK_SIZE`, `SUBTITLE_SIZE`, opener/subtitle placement | typography-spec constants — belong to the deferred phase, nothing in this build renders them. |
| `font_hook_alt: Poppins` | deferred phase. The opener's alternate font. |
| target length 60-95s | an observation of the reference reels. This build neither enforces nor suggests a length; the ~2min target is the person's, used at selection. |
| `reframe_between_cuts` | a RECORDING instruction, not something a script can enforce. Stated in `CLAUDE.md` as the person's constraint to hold. |
| `z_order: aroll < overlay < subtitle` | the overlay half is deferred. The surviving half — subtitles topmost — is in `typography.subtitles_topmost`. |
