from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "elsevier-figure-style"
sys.path.insert(0, str(SKILL / "scripts"))

from elsevier_plot_style import (  # noqa: E402
    apply_elsevier_style,
    figure_size,
    finalize_figure,
    line_style_kwargs,
    save_figure,
    scatter_style_kwargs,
    style_axis,
)


def main() -> None:
    spec = apply_elsevier_style()
    rows = list(csv.DictReader((ROOT / "examples" / "data" / "scatter_tradeoff.csv").open(encoding="utf-8")))
    costs = np.array([float(row["cost"]) for row in rows])
    quality = np.array([float(row["quality"]) for row in rows])
    groups = np.array([row["group"] for row in rows])
    fig, ax = plt.subplots(figsize=figure_size(spec=spec))

    for idx, group in enumerate(["baseline", "proposed"]):
        mask = groups == group
        ax.scatter(costs[mask], quality[mask], label=group.title(), **scatter_style_kwargs(group, spec=spec, index=idx))

    order = np.argsort(costs)
    ax.plot(costs[order], quality[order], label="Frontier guide", **line_style_kwargs("reference", spec=spec, marker="None", linestyle="--"))
    ax.set_xlabel("Cost")
    ax.set_ylabel("Quality")
    ax.legend()
    style_axis(ax, spec)
    finalize_figure(fig, spec)
    save_figure(fig, ROOT / "examples" / "outputs" / "good_scatter", spec=spec, formats=("pdf", "png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
