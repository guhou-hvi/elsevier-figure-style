from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "elsevier-figure-style"
sys.path.insert(0, str(SKILL / "scripts"))

from elsevier_plot_style import apply_elsevier_style, bar_style_kwargs, figure_size, finalize_figure, save_figure, style_axis  # noqa: E402


def main() -> None:
    spec = apply_elsevier_style()
    rows = list(csv.DictReader((ROOT / "examples" / "data" / "bar_scores.csv").open(encoding="utf-8")))
    labels = [row["model"] for row in rows]
    values = np.array([float(row["score"]) for row in rows])
    fig, ax = plt.subplots(figsize=figure_size(spec=spec))
    ax.bar(np.arange(len(labels)), values, **bar_style_kwargs("score", spec=spec))
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.0)
    ax.set_xticks(np.arange(len(labels)), labels, rotation=25, ha="right")
    style_axis(ax, spec, set_major_locator=False)
    finalize_figure(fig, spec)
    save_figure(fig, ROOT / "examples" / "outputs" / "good_bar", spec=spec, formats=("pdf", "png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
