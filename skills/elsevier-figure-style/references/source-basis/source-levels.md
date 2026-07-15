# Source Levels and Rule Profiles

This project is unofficial. A target journal's current Guide for Authors always overrides the bundled profile.

## Source Levels

| Level | Source type | Runtime use |
| --- | --- | --- |
| A | Official publisher pages, support pages, or target-journal instructions | Enabled in every profile |
| B | Authorized, redacted editor/reviewer revision evidence | Enabled in `editor` and `strict` |
| C | Public peer-review reports, reviewer training, or public author cases | Enabled only in `strict` |
| D | Practical visual QA heuristics and implementation defaults | Core checks in `editor`; complete visual QA in `strict`; never present as official policy |

## Rule Profiles

- `official`: apply A-level official guidance. Tool-input and integration findings can still be reported with `STYLE-*` IDs, but they are implementation findings rather than publisher policy; D-level visual judgments are disabled.
- `editor`: apply `official`, authorized B-level evidence, and core D-level checks for readability, overlap, alignment, panel labels, and clutter. Use by default.
- `strict`: apply `editor`, C-level public cases, and the full D-level visual checklist. Use for final pre-submission polishing.

The selected manifest defines the profile order and detector gates. Report each substantive finding with a rule ID from `rule-registry.md` and keep the source level visible when explaining why it applies.
