# Rule Registry

Use this registry to explain why a rule was applied. Profiles are cumulative: `editor` includes `official`; `strict` includes `editor`.

| Rule ID | Profile | Rule | Source ID | Implementation |
| --- | --- | --- | --- | --- |
| OFF-01 | official | Target-journal instructions override this generic profile. | OFF-SIZING, OFF-FAQ | Checklist |
| OFF-02 | official | Use accepted submission formats and verify journal-specific file-size limits. PNG/SVG may be useful previews but are not generic preferred submission formats. | OFF-OVERVIEW, OFF-FORMATS, OFF-FAQ | Manifest; metadata checker; checklist |
| OFF-03 | official | Prefer vector-first exports for charts and graphs. | OFF-OVERVIEW, OFF-TYPES | Checklist; `save_figure()` supports vector export |
| OFF-04 | official | Use supported fonts where possible and embed fonts in vector output. | OFF-OVERVIEW, OFF-TYPES | Manifest rcParams; checklist |
| OFF-05 | official | Keep normal final text around 7 pt and no explicit text below 6 pt. | OFF-SIZING | Manifest; source checker |
| OFF-06 | official | Use intended final widths when known: 30 mm minimum, 90 mm single, 140 mm 1.5-column, and 190 mm double. | OFF-SIZING | Manifest; metadata checker; checklist |
| OFF-07 | official | Use 300/500/1000 dpi for halftone/combination/line-art bitmap exports. | OFF-SIZING, OFF-TYPES, OFF-FAQ | Manifest; source and metadata checkers |
| OFF-08 | official | Keep line weights within a reproducible range and make prominent plot lines clear. | OFF-TYPES, OFF-FAQ | Manifest; source checker warns on hardcoded values |
| OFF-09 | official | Prefer RGB color and verify transparency compatibility. | OFF-FORMATS, OFF-TYPES, OFF-FAQ | Metadata checker; checklist |
| OFF-10 | official | Use colorblind-aware design and avoid color-only encoding when it matters. | OFF-MAIN | Manifest palette; checklist |
| OFF-11 | official | Supply captions separately or at manuscript level; do not rely on an in-image title. | OFF-FORMATS, OFF-FAQ | Source checker; checklist |
| OFF-12 | official | Do not selectively manipulate image features. | OFF-MAIN | Checklist |
| OFF-13 | official | Follow graphical-abstract instructions: concise content, separate upload, at least 1328 x 531 px at 300 dpi, 500:200 ratio, large supported fonts, and little clutter. | OFF-GA | Manifest; metadata checker; checklist |
| OFF-14 | official | Name, number, upload, and cite figure files consistently; provide each artwork file separately when required. | OFF-OVERVIEW, OFF-FORMATS | Checklist |
| OFF-15 | official | Clear third-party rights and follow current journal policies for generative-AI use in graphical abstracts. | OFF-FORMATS, OFF-GA | Checklist |
| ED-01 | editor | Keep the graphical abstract readable at its reduced display size and avoid poster-like density. | ED-2026-01 | Checklist; visual audit |
| ED-02 | editor | Remove minor ticks unless a scientific or journal-specific reason is documented. | ED-2026-01 | `style_axis()`; source checker |
| ED-03 | editor | Ensure figure text remains legible at final size. | ED-2026-01, OFF-SIZING | Manifest; source checker; visual audit |
| ED-04 | editor | Put a space between `step` and its number. | ED-2026-01 | Source checker |
| ED-05 | editor | Put a space between numbers and physical units when the discipline permits. | ED-2026-01 | Source checker |
| ED-06 | editor | Put panel labels at the top-left corner of each panel when practical. | ED-2026-01 | `annotate_panel()`; visual audit |
| ED-07 | editor | Do not visually fuse explanatory text with a panel label. | ED-2026-01 | Visual audit |
| ED-08 | editor | Make captions self-explanatory enough to decode the figure. | ED-2026-01 | Checklist |
| PUB-01 | strict | Keep axis labels, legends, fonts, and language consistent. | PUB-MDPI-FORMAT-CAPTIONS | Checklist |
| PUB-02 | strict | Explain legends, colorbars, symbols, matrices, and axes where needed. | PUB-PLOS-PANEL-LABELS | Checklist |
| PUB-03 | strict | Keep panel labels visible, high-contrast, ordered, and consistently placed. | PUB-PLOS-PANEL-LABELS | `annotate_panel()`; visual audit |
| PUB-04 | strict | Remove excessive legend material, software headers, decorative grids, and unnecessary axis labels. | PUB-ELSEVIER-REVIEW | Source checker; checklist |
| STYLE-01 | all | Route Python styling through an actual helper/profile call; document intentional semantic overrides. | Skill implementation rule | Source checker |
| STYLE-02 | all | Route bitmap metadata through the metadata checker; render PDF/SVG/EPS for manual visual audit. | Skill implementation rule | Metadata checker; visual audit |
| STYLE-03 | all | Validate the selected versioned manifest and every referenced resource before use. | Skill implementation rule | Profile loader; JSON Schema |
| VIS-01 | editor | Text must be readable at final intended display size. | D-level visual QA | Visual audit |
| VIS-02 | editor | Text, arrows, data marks, legends, colorbars, and panels must not overlap important content. | D-level visual QA | Visual audit |
| VIS-03 | editor | Panels, arrows, boxes, labels, and margins should be intentionally aligned and spaced. | D-level visual QA | Visual audit |
| VIS-04 | editor | Panel labels should be easy to locate, high-contrast, and distinct from explanatory text. | D-level visual QA | Visual audit |
| VIS-05 | editor | Schematic figures and graphical abstracts should avoid unnecessary clutter and decoration. | D-level visual QA | Visual audit |
