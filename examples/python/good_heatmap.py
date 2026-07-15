from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "elsevier-figure-style"
sys.path.insert(0, str(SKILL / "scripts"))

from elsevier_plot_style import (  # noqa: E402
    apply_elsevier_style,
    colorbar_kwargs,
    figure_size,
    finalize_figure,
    heatmap_kwargs,
    save_figure,
    style_axis,
    style_colorbar,
)


def main() -> None:
    spec = apply_elsevier_style()
    matrix = np.loadtxt(ROOT / "examples" / "data" / "heatmap_matrix.csv", delimiter=",")
    fig, ax = plt.subplots(figsize=figure_size(spec=spec))
    im = ax.imshow(matrix, **heatmap_kwargs(spec))
    cbar = fig.colorbar(im, ax=ax, **colorbar_kwargs(spec))
    cbar.set_label("Score")
    style_colorbar(cbar, spec)
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Condition")
    ax.set_xticks(np.arange(matrix.shape[1]), ["T1", "T2", "T3", "T4"])
    ax.set_yticks(np.arange(matrix.shape[0]), ["C1", "C2", "C3", "C4"])
    style_axis(ax, spec, set_major_locator=False)
    finalize_figure(fig, spec)
    save_figure(fig, ROOT / "examples" / "outputs" / "good_heatmap", spec=spec, formats=("pdf", "png"), artwork_type="combination")
    plt.close(fig)


if __name__ == "__main__":
    main()
