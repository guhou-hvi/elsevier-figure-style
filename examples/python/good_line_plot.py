from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "elsevier-figure-style"
sys.path.insert(0, str(SKILL / "scripts"))

from elsevier_plot_style import (  # noqa: E402
    apply_journal_style,
    band_style_kwargs,
    figure_size,
    finalize_figure,
    line_style_kwargs,
    save_figure,
    style_axis,
)


def main() -> None:
    spec = apply_journal_style(SKILL / "assets" / "elsevier_figure_style.json")
    data = np.genfromtxt(ROOT / "examples" / "data" / "training_metrics.csv", delimiter=",", names=True)
    fig, ax = plt.subplots(figsize=figure_size(spec=spec))

    train_style = line_style_kwargs("train", spec=spec, index=0)
    val_style = line_style_kwargs("validation", spec=spec, index=1)
    ax.plot(data["epoch"], data["train"], label="Train", **train_style)
    ax.plot(data["epoch"], data["validation"], label="Validation", **val_style)
    ax.fill_between(
        data["epoch"],
        data["train"] - data["train_std"],
        data["train"] + data["train_std"],
        **band_style_kwargs("train", spec=spec, index=0),
    )
    ax.fill_between(
        data["epoch"],
        data["validation"] - data["validation_std"],
        data["validation"] + data["validation_std"],
        **band_style_kwargs("validation", spec=spec, index=1),
    )
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.legend()
    style_axis(ax, spec)
    finalize_figure(fig, spec)
    save_figure(fig, ROOT / "examples" / "outputs" / "good_line_plot", spec=spec, formats=("pdf", "png"))
    plt.close(fig)


if __name__ == "__main__":
    main()
