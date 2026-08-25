# How to walk this map

## What it is

A record library of **nouns** (`objects/`), a short shelf of **verbs** (`processes/`), and a **change-impact index** (`effects/`). Cards are short on purpose: they say what a thing is, why it has the shape it has, and what a change to it reaches. Everything else stays in the workspace, cited.

The prose in `identity.md`, `governance.md`, `CONTEXT.md` and the stage contracts already answers *why* better than a map could. This answers the question none of them do: **what else moves.**

## Verified against

**The working tree on 2026-08-26**, not a commit. Twenty-six tracked files were modified and uncommitted at the time of the audit — the last commit, `9aa1f4e`, does not describe what is on disk. A card citing `path:line` cites that working tree.

## The three universes

| | Meaning |
|---|---|
| **live** | In force. Implement and cite against it. |
| **leftover** | Still present, no longer the main path. Touch only if that path is in scope. |
| **ghost** | Named or filed but not wired — a config key nothing reads, a documented file nothing has produced. **Do not implement against these**, and do not assume changing one has an effect. |

Ghosts here are not bugs by default. `caption_motion: none` is read by nothing and is still load-bearing as a written refusal. The distinction the map makes is only: *does changing this value change the output?*

## Card layout

1. **One sentence** — what it is, plus the file/type name if the product word differs
2. **Why this shape** — the load-bearing reason, not a field tour
3. **Shape** — the keys, files, or fields, cited
4. **Connected to** — owns / owned by / looks like but is not
5. **If you change this** — **Hits** and **Does not hit**, first-order only
6. **Surfaces** — who reads and writes it
7. **See** — the source file

`Does not hit` names the obvious *wrong* next thing, because that is the one an editor checks anyway.

## What this map is not

It does not restate a stage contract, copy behaviour out of a script, or hold any threshold. A number that appears in a card is quoted to identify a line, never to be read from here.
