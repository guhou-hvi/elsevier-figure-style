# Source Basis

This skill is Elsevier-style and unofficial. It is not affiliated with, endorsed by, or maintained by Elsevier. Use it as a formatting aid, then verify the target journal's current Guide for Authors.

Use the `source-basis/` directory as the skill's sources/evidence layer for rule provenance:

- `source-basis/source-levels.md`: source credibility levels and runtime profiles.
- `source-basis/official-elsevier-artwork.md`: official Elsevier artwork source IDs and derived rules.
- `source-basis/private-editor-comments-redacted.md`: redacted real editor/reviewer figure-format comments.
- `source-basis/public-format-cases.md`: public peer-review and reviewer-training examples used only by the `strict` profile.
- `source-basis/rule-registry.md`: rule IDs, profiles, sources, and implementation coverage.

Rule profiles are defined by the selected manifest:

- `official`: A-level official guidance plus target-journal instructions supplied by the user. `STYLE-*` tool-integrity findings may still appear and remain explicitly non-policy.
- `editor`: `official` plus authorized redacted revision evidence and core D-level visual QA. This is the default.
- `strict`: `editor` plus C-level public cases and the complete D-level visual checklist.

Do not present any source-basis rule as acceptance proof. Present it as a cited formatting rationale with the source level shown.
