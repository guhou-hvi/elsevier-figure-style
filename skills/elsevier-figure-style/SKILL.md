---
name: elsevier-figure-style
description: Generate, revise, and audit source-backed quantitative manuscript figures, and visually audit exported schematic/conceptual figures and graphical abstracts without redrawing them in v0.1. Use for Elsevier-style manuscript figure generation, matplotlib or ggplot2 result plots, line charts, heatmaps, bar charts, scatter or Pareto plots, artwork export checks, pre-submission figure QA, mechanism/workflow diagram audits, graphical-abstract audits, or equivalent Chinese-language requests for paper figures and submission checks.
---

# Elsevier Figure Style

## Purpose

Apply this unofficial, source-backed workflow while generating quantitative result figures and while auditing manuscript figure exports. Verify the target journal's current Guide for Authors before submission. Never claim that this skill guarantees acceptance.

Use two tracks:

- `result`: generate, revise, and audit line, heatmap, bar/barh, scatter, Pareto/frontier, ablation, and metric figures.
- `schematic`: visually audit principle, mechanism, workflow, conceptual, and graphical-abstract exports. In v0.1, do not redraw or edit these figures unless the user separately requests an editing workflow.

Match the report language to the user's language. Keep command names, field names, and rule IDs unchanged.

## Select the Profile

Use `assets/elsevier_figure_style.json` by default. It is the single manifest entry point for identity, resources, profiles, style values, export thresholds, and supported detectors.

Before first use of the bundled Python scripts, run `python scripts/check_environment.py`. The skills CLI copies Skill files but does not install Python packages. If dependencies are missing, ask before running the install command reported by the checker; do not modify the user's Python environment silently. R workflows require `ggplot2` and `jsonlite`.

- `official`: A-level official publisher and target-journal rules. Tool-input and style-integration findings use `STYLE-*` IDs and must not be described as official policy.
- `editor`: `official` plus authorized redacted revision evidence and core D-level visual QA. Use by default.
- `strict`: `editor` plus public cases and the complete visual QA checklist.

When the user supplies another manifest, pass it through `--config` or `config_path`. A new journal may reuse the built-in detectors without code changes; a genuinely new detector type still requires code.

Treat a manifest and its referenced files as one profile bundle. `bundle_root` defines the bundle boundary; schema and resource paths must be relative and remain inside it. Never weaken this boundary for an untrusted profile.

## Establish the Figure Contract

Record:

- Claim: the one-sentence conclusion the figure supports.
- Track: `result`, `schematic`, or `graphical-abstract`.
- Family: line, heatmap, bar, scatter, mixed, mechanism, workflow, graphical abstract, or R/ggplot2.
- Profile: official, editor, or strict.
- Target layout: minimal, single, one-half, double, or graphical abstract when known.
- Artwork type: line, combination, or halftone.
- Export target and target-journal overrides.

## Generate Result Figures

For Python/matplotlib, load the selected profile and use the helper functions:

```python
from elsevier_plot_style import apply_journal_style, figure_size, line_style_kwargs, style_axis, finalize_figure, save_figure

spec = apply_journal_style(config_path="path/to/profile.json")
fig, ax = plt.subplots(figsize=figure_size(spec=spec))
ax.plot(x, y, label="Model", **line_style_kwargs("model", spec=spec))
style_axis(ax, spec)
finalize_figure(fig, spec)
save_figure(fig, "figure_1", spec=spec, formats=("pdf", "tiff"), artwork_type="line")
```

For reproducible project-local imports, initialize a vendored module:

```bash
python scripts/init_figure_style_project.py --target <project> --config assets/elsevier_figure_style.json
```

Then import helpers from `figure_style` in the target project.

For R/ggplot2, source `scripts/elsevier_theme.R`, then use `theme_journal()`, `journal_palette()`, and `save_journal()`. The compatibility aliases `theme_elsevier()`, `elsevier_palette()`, and `save_elsevier()` remain available. R has no static checker in v0.1.

## Revise Result Figures

1. Load `references/python-workflow.md` or `references/r-workflow.md`.
2. Replace ad hoc fonts, colors, widths, markers, DPI, and export options with the selected profile.
3. Keep semantic overrides only when they encode meaning, such as thresholds, baselines, intervention windows, highlighted frontier points, or discrete classes.
4. Mark an intentional static-checker override on the same or preceding line:

```python
# figure-style: allow STYLE-01 - benchmark threshold must remain red
ax.axhline(limit, color="red")
```

5. Run the Python checker and inspect every remaining warning.

## Audit Figures

Load `references/submission-checklist.md`. When an export is available, also load `references/visual-audit-workflow.md`.

Run the Python source checker:

```bash
python scripts/check_elsevier_figure_style.py --path <script-or-dir> --config assets/elsevier_figure_style.json --profile editor
```

Run bitmap metadata checks with an explicit artwork type when known:

```bash
python scripts/check_exported_figure_metadata.py --path <figure-or-dir> --config assets/elsevier_figure_style.json --figure-type result --artwork-type combination --target-layout single --profile editor
```

Use `--format json` for machine-readable findings and `--fail-on warn` for a stricter CI gate. Both checkers fail by default on `FAIL` findings or invalid inputs. The source checker also returns an input error when Python files are present but no supported matplotlib figure calls are detected; do not interpret that case as a style `PASS`.

For visual QA:

1. Actually open or render the final export at the intended display size.
2. Do not report a visual `PASS` for any figure that was not viewed.
3. For PDF/SVG/EPS, render a preview when the environment cannot inspect the format directly; do not alter the original.
4. For result figures with code and exports, report source findings, metadata findings, then visual findings.
5. Report `FAIL`, then `WARN`, then notable `PASS` items with location, rule ID, and a concrete fix.

## Resources

- `assets/elsevier_figure_style.json`: default versioned manifest.
- `assets/journal_figure_profile.schema.json`: manifest schema.
- `scripts/elsevier_plot_style.py`: Python profile loader and plotting helpers.
- `scripts/elsevier_theme.R`: R profile loader and ggplot2 helpers.
- `scripts/check_elsevier_figure_style.py`: profile-aware Python static checker.
- `scripts/check_exported_figure_metadata.py`: bitmap and export metadata checker.
- `scripts/init_figure_style_project.py`: project-local helper/profile initializer.
- `scripts/check_environment.py`: Python version and runtime-dependency preflight.
- `requirements.txt`: runtime dependencies copied with the Skill.
- `references/submission-checklist.md`: profile-aware submission checklist.
- `references/visual-audit-workflow.md`: exported-figure visual QA workflow.
- `references/source-basis/rule-registry.md`: rule IDs, evidence levels, and implementation coverage.
