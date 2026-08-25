# Node types — closed set

Every file under `objects/` and `processes/` carries this frontmatter. Nothing else is a node.

```yaml
---
name: kebab-case-slug          # unique across the map; the [[link]] target
type: object | process
cluster: artifacts | dials | engine | —      # objects only
universe: live | leftover | ghost
status: verified | stub | stale
verified: 2026-08-26           # required when status is verified
---
```

- **`type: object`** — a noun: a file a run produces, a value a change targets, a piece of shared machinery.
- **`type: process`** — a verb: a movement that actually runs. Input → Movement → Output, with `consumes` / `produces` linking to object cards.

`status: verified` requires a date and citations in the body. `stale` is allowed and honest. A confident wrong date is not.

Links are `[[name]]`, matching the `name:` field. A link with no target yet marks a card worth writing, not an error.
