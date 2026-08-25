# objects/ — the nouns

Three clusters, grouped by **how an editor asks**, not by where the files sit on disk.

| Cluster | The question it answers |
|---|---|
| `artifacts/` | "what is this file a run produced, and who reads it next" |
| `dials/` | "I want to change a value — which one, and what does it reach" |
| `engine/` | "how are the stages wired together, and what checks them" |

**Open `_index.md`, then one card.** Reading the folder is the thing the index exists to prevent.

A card is short by design. If you want the reasoning behind a value, the card points at the config comment or stage contract that holds it — those are better than anything a map would restate.
