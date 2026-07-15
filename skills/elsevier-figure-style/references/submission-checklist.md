# Pre-Submission Figure Checklist

Choose the selected manifest and profile before auditing:

- `official`: A-level official rules; explicitly labeled `STYLE-*` input/integration findings can still be reported as non-policy tool checks.
- `editor`: official rules, authorized redacted revision evidence, and core visual QA. Default.
- `strict`: editor rules, public cases, and the complete visual QA checklist.

Use `source-basis/rule-registry.md` for provenance and `visual-audit-workflow.md` whenever an exported figure is available.

## Official Profile

- Check the current target-journal Guide for Authors; it overrides generic defaults. Source: OFF-01.
- Use accepted submission formats. Prefer EPS/PDF for vector charts and TIFF/JPEG for appropriate bitmap artwork; treat PNG/SVG as preview formats unless the journal accepts them. Source: OFF-02, OFF-03.
- Set the intended final dimensions; use 30/90/140/190 mm only as generic minimum/single/1.5-column/double references. Source: OFF-06.
- Match bitmap resolution to artwork type: 300 dpi halftone, 500 dpi combination, 1000 dpi line art. Do not upsample a low-quality image as a substitute for regeneration. Source: OFF-07.
- Keep normal final lettering around 7 pt and explicit text at least 6 pt; use supported fonts and embed them in vector exports. Source: OFF-04, OFF-05.
- The bundled manifest uses a readability-first 11 pt default for labels and 10 pt for ticks and legends on an exact 140 mm canvas. These are project defaults, not a claim that every Elsevier journal requires these values.
- Keep line weights printable and prominent plot lines clearly reproducible. Source: OFF-08.
- Prefer RGB color, verify transparency handling, and avoid relying on color alone. Source: OFF-09, OFF-10.
- Supply captions separately or at manuscript level; avoid relying on in-image titles. Source: OFF-11.
- Do not selectively enhance, obscure, move, remove, or introduce image features. Source: OFF-12.
- For a graphical abstract, follow the target-journal instructions and check separate upload, concise content, at least 1328 x 531 px at 300 dpi, 500:200 ratio, supported large fonts, little clutter, and no unnecessary heading or whitespace. Source: OFF-13.
- Name and number artwork files consistently, upload them separately when required, cite them in sequence, and verify every caption/figure reference. Source: OFF-14.
- Clear third-party permissions and verify the current journal policy before using generative-AI material in a graphical abstract. Source: OFF-15.

## Editor Profile Additions

- Keep the graphical abstract readable at reduced display size rather than poster-like. Source: ED-01, VIS-01, VIS-05.
- Remove minor ticks unless a scientific or journal-specific reason is documented. Source: ED-02.
- Manually justify explicit text below 7 pt and verify it at final size. Source: ED-03, VIS-01.
- Use readable spacing such as `step 1` and `10 mm` unless discipline conventions differ. Source: ED-04, ED-05.
- Put panel labels at the top-left when practical and keep explanatory text visually separate. Source: ED-06, ED-07, VIS-04.
- Make captions sufficiently self-contained to decode symbols, units, groups, colors, and comparisons. Source: ED-08.
- Verify that labels, arrows, panels, legends, colorbars, and marks do not overlap. Source: VIS-02.
- Verify intentional alignment, spacing, margins, and visual hierarchy. Source: VIS-03.

## Strict Profile Additions

- Keep axis labels, legends, fonts, language, and panel treatment consistent. Source: PUB-01.
- Align legend order, panel order, and caption order with the visual layout. Source: PUB-02.
- Explain heatmap scales, matrix axes, scatter encodings, symbols, and colorbars. Source: PUB-02.
- Keep panel labels high-contrast, ordered, and consistently placed. Source: PUB-03.
- Remove excessive software headers, decorative grids, legends, axis labels, and non-informative decoration. Source: PUB-04, VIS-05.

## Python Source Audit

```bash
python scripts/check_elsevier_figure_style.py --path <script-or-dir> --config assets/elsevier_figure_style.json --profile editor
```

- The checker exits nonzero on `FAIL` by default.
- Use `--fail-on warn` for a stricter CI gate or `--fail-on never` for report-only use.
- Use `--format json` for machine-readable findings.
- Mark a justified semantic override with `# figure-style: allow <RULE-ID> - <reason>` on the same or preceding line.
- The style-integration gate itself is not overridable; an override can justify a local visual choice but cannot replace loading the selected profile.

## Export Metadata Audit

```bash
python scripts/check_exported_figure_metadata.py --path <figure-or-dir> --config assets/elsevier_figure_style.json --figure-type result --artwork-type combination --target-layout single --profile editor
```

- Select `line`, `combination`, or `halftone` whenever known; `auto` can only enforce a conservative floor and must warn about ambiguity.
- Use `--figure-type schematic` for conceptual figures and `--figure-type graphical-abstract` for graphical abstracts.
- PDF, SVG, and EPS require rendering and manual visual audit in v0.1.

## Manual Visual QA

- Actually view the final export at intended size; do not report visual `PASS` without viewing it.
- For result figures, merge source, metadata, and visual findings in that order.
- Verify every panel label, legend, tick label, colorbar, annotation, box, and arrow for readability and overlap.
- Verify units, abbreviations, thresholds, reference lines, and highlighted points are explained in the figure or caption.
- Preserve source data or generation scripts for quantitative panels.
