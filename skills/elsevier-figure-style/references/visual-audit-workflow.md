# Visual Audit Workflow

Use this workflow only after an exported manuscript figure has actually been opened or rendered. It applies to schematic/conceptual and quantitative/result figures.

## Route the Figure

- `schematic`: principle, mechanism, workflow, and conceptual figures. Audit only in v0.1.
- `result`: line, heatmap, bar/barh, scatter, Pareto/frontier, ablation, and other quantitative figures.
- `graphical-abstract`: schematic-like audit plus graphical-abstract metadata and policy checks.

Do not redraw or edit a schematic in this workflow. Do not claim that an issue was fixed unless the user separately requested an editing workflow.

## Establish Valid Visual Input

- Prefer the final PNG, JPEG, TIFF, PDF, SVG, or EPS export.
- Open a bitmap directly with the available vision tool.
- Render PDF/SVG/EPS to a temporary preview if the environment cannot inspect it directly; preserve the original unchanged.
- Inspect the figure both at intended display size and at useful zoom for local defects.
- Treat PPT, AI, Figma, Draw.io, and similar source files as optional context.
- Do not report visual `PASS` for a figure or region that was not viewed.

Run the metadata checker for bitmap exports. For a result figure with Python source, run the source checker first.

## Inspect

- Readability: labels, legends, annotations, and panel labels remain legible at final size. Source: OFF-05, ED-03, VIS-01.
- Overlap: text, arrows, panels, legends, colorbars, and marks do not obscure one another. Source: VIS-02.
- Alignment: panels, arrows, boxes, internal labels, and margins are intentionally aligned and spaced. Source: VIS-03.
- Panel labels: labels are visible, high-contrast, consistently placed, and top-left when practical. Source: ED-06, PUB-03, VIS-04.
- Clutter: schematic figures and graphical abstracts avoid decorative or redundant content. Source: OFF-13, ED-01, VIS-05.
- Encoding: colors, symbols, line styles, arrows, legends, and colorbars are explained. Source: OFF-10, PUB-02.
- Export context: format, dimensions, DPI, color mode, and artwork type match the selected manifest and target journal. Source: OFF-02, OFF-06, OFF-07, OFF-09.

## Report

Match the report language to the user's language. Keep rule IDs unchanged.

| Severity | Location | Issue | Source/Rule | Recommended fix |
| --- | --- | --- | --- | --- |
| FAIL/WARN/PASS | Panel or region | Observable finding | Rule ID | Concrete action |

- Report `FAIL`, then `WARN`, then notable `PASS` confirmations.
- Use precise locations such as `panel (a), top-left`, `center workflow arrow`, or `right colorbar`.
- Keep fixes actionable: increase label size, move the legend, separate arrows, improve contrast, or regenerate at the required resolution.
- Do not present D-level visual heuristics as official publisher requirements.

## Combine Result-Figure Findings

1. Report Python source findings when source exists.
2. Report metadata findings for the final export.
3. Report visual findings from the viewed or rendered export.
4. Preserve rule IDs and distinguish official, editor-derived, public-case, and D-level evidence.
5. End with target-journal checks that remain manual; never state that acceptance is guaranteed.
