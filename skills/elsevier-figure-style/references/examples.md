# Example Tasks

## Generate a Line Figure

User request:

```text
Use $elsevier-figure-style to generate an Elsevier-style line plot from this training CSV.
```

Expected agent behavior:

- Run `scripts/check_environment.py` before first Python use.
- Load `references/python-workflow.md`.
- Use `apply_journal_style()` and `line_style_kwargs()` with the selected manifest.
- Use the `editor` profile unless the user requests the official profile or strict final QA.
- Save PDF and TIFF outputs.
- Avoid a visible chart title unless the user requires it.

## Revise a Heatmap

User request:

```text
Use $elsevier-figure-style to revise this matplotlib heatmap for publication formatting.
```

Expected agent behavior:

- Use `heatmap_kwargs()` and `colorbar_kwargs()`.
- Keep a domain-specific discrete colormap only if it encodes class meaning.
- Run the checker with the selected profile and report rule IDs.

## Audit Before Submission

User request:

```text
Use $elsevier-figure-style to audit this figure script before Elsevier submission.
```

Expected agent behavior:

- Load `references/submission-checklist.md`.
- Run `check_elsevier_figure_style.py --profile editor` by default; it exits nonzero on `FAIL`.
- List `FAIL` findings first.
- State that target-journal verification is still required.

## Audit a Schematic Figure

User request:

```text
Use $elsevier-figure-style to audit this mechanism diagram before Elsevier submission.
```

Expected agent behavior:

- Load `references/visual-audit-workflow.md`.
- Run `check_exported_figure_metadata.py` if the export is PNG/JPG/TIFF.
- Treat PDF/SVG/EPS as rendered/manual visual-audit inputs in v0.1.
- Actually view or render the export; never report visual `PASS` without viewing it.
- Report visual issues as `FAIL`/`WARN`/`PASS` with location, source/rule ID, and recommended fix.
- Do not redraw or edit the schematic unless the user separately asks for an edit workflow.

## Basic R Figure

User request:

```text
Use $elsevier-figure-style to make this ggplot2 figure more submission-ready.
```

Expected agent behavior:

- Source `scripts/elsevier_theme.R`.
- Apply `theme_journal()` from the selected manifest.
- Export with `save_journal()`.
- Use the checklist for final audit.
