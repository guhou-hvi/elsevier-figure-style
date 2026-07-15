# Python Workflow

Use `scripts/elsevier_plot_style.py` with a versioned journal profile. The default profile is `assets/elsevier_figure_style.json`.

Run `python scripts/check_environment.py` before first use. If dependencies are missing, install `requirements.txt` only after the user approves changing the active Python environment.

## Persistent Project Setup

Vendor a self-contained helper/profile bundle into the target project:

```bash
python scripts/init_figure_style_project.py --target <project> --config assets/elsevier_figure_style.json
```

The command creates `<project>/figure_style/`. It refuses to replace an existing directory unless `--force` is explicit; use `--dry-run` to inspect the copy plan. The copied bundle includes its runtime requirements and rejects manifest resources outside the declared `bundle_root`.

## Minimal Pattern

```python
import matplotlib.pyplot as plt
from figure_style import apply_journal_style, figure_size, line_style_kwargs, style_axis, finalize_figure, save_figure

spec = apply_journal_style()
fig, ax = plt.subplots(figsize=figure_size(spec=spec))
ax.plot(x, y, label="Series", **line_style_kwargs("series", spec=spec))
ax.set_xlabel("X label")
ax.set_ylabel("Y label")
ax.legend()
style_axis(ax, spec)
finalize_figure(fig, spec)
save_figure(fig, "figure", spec=spec, formats=("pdf", "tiff"), artwork_type="line")
```

Use `config_path="path/to/profile.json"` with `apply_journal_style()` to select another manifest without changing helper code.

## Helpers

- `load_profile()`: validate and load the complete manifest.
- `load_style()`: load only its style section.
- `apply_journal_style()`: apply rcParams; `apply_elsevier_style()` is a compatibility alias.
- `figure_width()`, `figure_size()`, and `graphical_abstract_size()`: configured size presets. With the bundled profile, the no-argument result-figure default is an exact 140 mm-wide, 3:2 canvas.
- `line_style_kwargs()`, `band_style_kwargs()`, `bar_style_kwargs()`, `scatter_style_kwargs()`, and `heatmap_kwargs()`: family-specific styles.
- `colorbar_kwargs()` and `style_colorbar()`: colorbar placement and typography.
- `annotate_panel()`: top-left panel labels.
- `style_axis()` and `finalize_figure()`: axes, title policy, and layout.
- `save_figure()`: profile-backed vector/bitmap export.

The bundled profile uses 11 pt labels, 10 pt ticks/legends, and a 140 mm default canvas as readability-first project defaults. Elsevier's generic sizing guidance remains the evidence source: normal finished text is around 7 pt, sub/superscripts should not be below 6 pt, and some artwork may require about 10 pt. Always let the target journal override the bundled defaults.

## Overrides

Keep intentional overrides when they encode scientific meaning. Add a reason for the checker:

```python
# figure-style: allow STYLE-01 - red denotes the regulatory risk threshold
ax.axhline(risk_limit, color="red")
```

The `STYLE-01` integration gate cannot be overridden. A semantic override applies only to the local rule finding on that line.

## Audit

```bash
python scripts/check_elsevier_figure_style.py --path <script-or-dir> --config assets/elsevier_figure_style.json --profile editor
```

The checker exits nonzero on `FAIL` by default. Use `--format json`, `--fail-on warn`, or `--fail-on never` when needed.
