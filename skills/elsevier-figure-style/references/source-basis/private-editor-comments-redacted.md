# Private Editor/Reviewer Revision Comments, Redacted

Source level: B.

This file summarizes revision evidence that the maintainer is authorized to publish as redacted paraphrases. The original correspondence is not redistributed, the manuscript topic is omitted, and only reusable figure-format requirements are retained. Treat these rules as practical editor/reviewer rework prevention, not as universal Elsevier policy.

Contributions at this level must carry the same authorization: publish only an authorized paraphrase, never the original private correspondence.

Source ID: `ED-2026-01`.

Extraction date: 2026-07-03.

## Redacted Figure-Format Requirements

- Graphical abstract must be readable at 5 cm high x 13 cm wide on a regular screen; it should provide a clear at-a-glance summary rather than look like a busy poster. This overlaps with official graphical abstract guidance in `OFF-GA`.
- Remove minor ticks from all plots and from the graphical abstract.
- Make figure text legible at final size; increase too-small fonts.
- Put a space between `step` and the number, for example `step 1` rather than `step1`.
- Put a space between numbers and physical units, for example `10 mm` rather than `10mm`, unless the target journal or discipline convention says otherwise.
- In multi-panel figures, put panel labels such as `(a)` and `(b)` at the top-left corner of each panel.
- Do not place extra explanatory text immediately next to the panel label.
- Make figure captions self-explanatory; expand captions that require manuscript body text to decode the figure.

## Checker Coverage

- `minor ticks`: static checker flags `minorticks_on()` as `FAIL` in `editor` and `strict` profiles.
- `step` spacing: static checker warns on string literals like `step1`.
- `number-unit` spacing: static checker warns on string literals like `10mm`.
- `font legibility`: static checker fails explicit `fontsize < 6` and warns on explicit `fontsize < 7` in `editor` and `strict` profiles.
- `panel labels`: helper `annotate_panel()` defaults to the top-left panel corner; final placement still requires visual inspection.
- `captions` and graphical-abstract clarity: checklist-only because they depend on manuscript context.
