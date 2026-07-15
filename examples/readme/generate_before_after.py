from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "elsevier-figure-style"
README_PREVIEW_SIZE_MM = (90.0, 60.0)
sys.path.insert(0, str(SKILL / "scripts"))

from elsevier_plot_style import (  # noqa: E402
    apply_journal_style,
    bar_style_kwargs,
    figure_size,
    finalize_figure,
    line_style_kwargs,
    save_figure,
    scatter_style_kwargs,
    style_axis,
)


def synthetic_results() -> dict[str, Any]:
    """Return one deterministic model-comparison story for all three plot types."""
    epochs = np.arange(1, 9)
    baseline_loss = 0.86 - 0.055 * np.log1p(epochs) + 0.012 * np.sin(epochs)
    proposed_loss = baseline_loss - 0.065 - 0.008 * np.cos(epochs)
    baseline_latency = np.array([31.0, 34.0, 38.0, 42.0])
    baseline_f1 = np.array([0.760, 0.775, 0.785, 0.792])
    proposed_latency = np.array([22.0, 25.0, 28.0, 31.0])
    proposed_f1 = np.array([0.810, 0.827, 0.840, 0.852])
    return {
        "epochs": epochs,
        "baseline_loss": baseline_loss,
        "proposed_loss": proposed_loss,
        "models": ["Model A", "Model B", "Model C", "Ours"],
        "model_ticks": ["A", "B", "C", "Ours"],
        "stages": ["Stage 1", "Stage 2"],
        "stage_1_f1": np.array([0.740, 0.770, 0.790, 0.820]),
        "stage_2_f1": np.array([0.770, 0.800, 0.830, 0.860]),
        "baseline_latency": baseline_latency,
        "baseline_f1": baseline_f1,
        "proposed_latency": proposed_latency,
        "proposed_f1": proposed_f1,
    }


def comparison_results(spec: dict[str, Any]) -> dict[str, Any]:
    data = synthetic_results()
    data["bar_colors"] = tuple(
        bar_style_kwargs(series, spec=spec, index=index)["color"]
        for index, series in enumerate(("stage_1", "stage_2"))
    )
    return data


def _style_ad_hoc_axis(
    ax: Axes,
    *,
    legend: bool = False,
    legend_loc: str = "best",
    legend_ncol: int = 1,
) -> None:
    ax.grid(True, color="#b8b8b8", linestyle="--", linewidth=0.65, alpha=0.75)
    ax.tick_params(axis="both", labelsize=3.5, width=0.4, length=2.0)
    for spine in ax.spines.values():
        spine.set_linewidth(0.4)
    if legend:
        ax.legend(frameon=True, fontsize=3.5, loc=legend_loc, ncol=legend_ncol)


def _set_line_limits(ax: Axes) -> None:
    ax.set_xlim(0.7, 8.3)
    ax.set_ylim(0.64, 0.88)


def _enforce_profiled_title_policy(ax: Axes, spec: dict[str, Any]) -> None:
    if not spec["axes"]["show_title"]:
        ax.set_title("")


def plot_ad_hoc_line(ax: Axes, data: dict[str, Any]) -> None:
    ax.plot(
        data["epochs"],
        data["baseline_loss"],
        color="#7189A8",
        linewidth=0.7,
        marker="o",
        markersize=2.7,
        label="Baseline",
    )
    ax.plot(
        data["epochs"],
        data["proposed_loss"],
        color="#86A0BD",
        linewidth=1.35,
        marker="o",
        markersize=3.2,
        label="Proposed",
    )
    ax.set_title("Training progress", fontsize=4.0)
    ax.set_xlabel("Epoch", fontsize=4.0)
    ax.set_ylabel("Validation loss, L_val", fontsize=4.0)
    ax.set_xticks(data["epochs"])
    _set_line_limits(ax)
    _style_ad_hoc_axis(ax, legend=True)


def plot_profiled_line(ax: Axes, data: dict[str, Any], spec: dict[str, Any]) -> None:
    ax.plot(
        data["epochs"],
        data["baseline_loss"],
        label="Baseline",
        **line_style_kwargs("baseline", spec=spec, index=0),
    )
    ax.plot(
        data["epochs"],
        data["proposed_loss"],
        label="Proposed",
        **line_style_kwargs("proposed", spec=spec, index=1),
    )
    ax.set_title("Training progress")
    ax.set_xlabel("Epoch")
    ax.set_ylabel(r"Validation loss, $\mathcal{L}_{\mathrm{val}}$")
    ax.legend(loc="upper right")
    _set_line_limits(ax)
    style_axis(ax, spec)
    _enforce_profiled_title_policy(ax, spec)


def _set_bar_limits(ax: Axes, data: dict[str, Any]) -> None:
    model_centers = np.arange(len(data["models"])) * 2.0
    ax.set_xlim(-0.9, model_centers[-1] + 0.9)
    ax.set_ylim(0.70, 0.92)
    ax.set_xticks(model_centers, data["model_ticks"])


def plot_ad_hoc_bar(ax: Axes, data: dict[str, Any]) -> None:
    model_centers = np.arange(len(data["models"])) * 2.0
    width = 0.72
    ax.bar(
        model_centers - width / 2,
        data["stage_1_f1"],
        width=width,
        color=data["bar_colors"][0],
        label=data["stages"][0],
    )
    ax.bar(
        model_centers + width / 2,
        data["stage_2_f1"],
        width=width,
        color=data["bar_colors"][1],
        label=data["stages"][1],
    )
    ax.set_title("Model comparison", fontsize=4.0)
    ax.set_xlabel("Model", fontsize=4.0)
    ax.set_ylabel("Test F1 score", fontsize=4.0)
    _set_bar_limits(ax, data)
    _style_ad_hoc_axis(ax, legend=True, legend_loc="upper left", legend_ncol=2)


def plot_profiled_bar(ax: Axes, data: dict[str, Any], spec: dict[str, Any]) -> None:
    model_centers = np.arange(len(data["models"])) * 2.0
    for index, (series, values, label, direction) in enumerate(
        zip(
            ("stage_1", "stage_2"),
            (data["stage_1_f1"], data["stage_2_f1"]),
            data["stages"],
            (-1, 1),
            strict=True,
        )
    ):
        kwargs = bar_style_kwargs(series, spec=spec, index=index)
        width = float(kwargs["width"])
        ax.bar(model_centers + direction * width / 2, values, label=label, **kwargs)
    ax.set_title("Model comparison")
    ax.set_xlabel("Model")
    ax.set_ylabel("Test F1 score")
    ax.legend(loc="upper left", ncol=1)
    _set_bar_limits(ax, data)
    style_axis(ax, spec, set_major_locator=False)
    _enforce_profiled_title_policy(ax, spec)


def _set_scatter_limits(ax: Axes) -> None:
    ax.set_xlim(17.0, 55.0)
    ax.set_ylim(0.74, 0.87)


def plot_ad_hoc_scatter(ax: Axes, data: dict[str, Any]) -> None:
    ax.scatter(
        data["baseline_latency"],
        data["baseline_f1"],
        color="#7189A8",
        marker="o",
        s=16,
        label="Baseline",
    )
    ax.scatter(
        data["proposed_latency"],
        data["proposed_f1"],
        color="#86A0BD",
        marker="o",
        s=24,
        label="Proposed",
    )
    ax.set_title("Accuracy-latency trade-off", fontsize=4.0)
    ax.set_xlabel("Latency t (ms)", fontsize=4.0)
    ax.set_ylabel("Test F1 score", fontsize=4.0)
    _set_scatter_limits(ax)
    _style_ad_hoc_axis(ax, legend=True, legend_loc="upper right")


def plot_profiled_scatter(ax: Axes, data: dict[str, Any], spec: dict[str, Any]) -> None:
    ax.scatter(
        data["baseline_latency"],
        data["baseline_f1"],
        label="Baseline",
        **scatter_style_kwargs("baseline", spec=spec, index=0),
    )
    ax.scatter(
        data["proposed_latency"],
        data["proposed_f1"],
        label="Proposed",
        **scatter_style_kwargs("proposed", spec=spec, index=1),
    )
    ax.set_title("Accuracy-latency trade-off")
    ax.set_xlabel(r"Latency, $t$ (ms)")
    ax.set_ylabel("Test F1 score")
    ax.legend(
        loc="upper right",
        handletextpad=0.35,
        borderpad=0.25,
        labelspacing=0.25,
        handlelength=0.8,
        borderaxespad=0.35,
    )
    _set_scatter_limits(ax)
    style_axis(ax, spec)
    _enforce_profiled_title_policy(ax, spec)


PLOTTERS = {
    "line": (plot_ad_hoc_line, plot_profiled_line),
    "bar": (plot_ad_hoc_bar, plot_profiled_bar),
    "scatter": (plot_ad_hoc_scatter, plot_profiled_scatter),
}


def build_readme_cells(spec: dict[str, Any]) -> dict[str, dict[str, tuple[Figure, Axes]]]:
    data = comparison_results(spec)
    preview_size = tuple(value / 25.4 for value in README_PREVIEW_SIZE_MM)
    cells: dict[str, dict[str, tuple[Figure, Axes]]] = {"before": {}, "after": {}}
    for kind, (before_plot, after_plot) in PLOTTERS.items():
        before_fig, before_ax = plt.subplots(figsize=preview_size)
        before_plot(before_ax, data)
        before_fig.tight_layout(pad=0.5)
        cells["before"][kind] = (before_fig, before_ax)

        after_fig, after_ax = plt.subplots(figsize=preview_size)
        after_plot(after_ax, data, spec)
        finalize_figure(after_fig, spec)
        cells["after"][kind] = (after_fig, after_ax)
    return cells


def build_submission_samples(spec: dict[str, Any]) -> dict[str, tuple[Figure, Axes]]:
    data = synthetic_results()
    samples: dict[str, tuple[Figure, Axes]] = {}
    for kind, (_, after_plot) in PLOTTERS.items():
        fig, ax = plt.subplots(figsize=figure_size(spec=spec))
        after_plot(ax, data, spec)
        finalize_figure(fig, spec)
        samples[kind] = (fig, ax)
    return samples


def save_readme_preview(fig: Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with BytesIO() as buffer:
        with plt.rc_context({"savefig.bbox": None, "savefig.pad_inches": 0}):
            # figure-style: allow OFF-07 - README preview; standalone TIFFs use line-art DPI.
            fig.savefig(
                buffer,
                format="png",
                dpi=300,
                bbox_inches=None,
                facecolor="white",
                transparent=False,
            )
        buffer.seek(0)
        with Image.open(buffer) as image:
            rgb = image.convert("RGB")
            rgb.save(path, format="PNG", dpi=(300, 300), optimize=True)
            rgb.close()
    return path


def generate_outputs(root: Path = ROOT) -> dict[str, Any]:
    spec = apply_journal_style(SKILL / "assets" / "elsevier_figure_style.json")
    cells = build_readme_cells(spec)

    preview_root = root / "docs" / "assets" / "comparison"
    previews: dict[str, dict[str, Path]] = {"before": {}, "after": {}}
    for state, state_cells in cells.items():
        for kind, (fig, _) in state_cells.items():
            previews[state][kind] = save_readme_preview(
                fig,
                preview_root / f"{state}-{kind}.png",
            )

    output_root = root / "examples" / "outputs" / "readme"
    outputs: dict[str, dict[str, Path]] = {}
    submission_samples = build_submission_samples(spec)
    for kind, (fig, _) in submission_samples.items():
        pdf = save_figure(
            fig,
            output_root / "vector" / f"after_{kind}",
            spec=spec,
            formats=("pdf",),
            artwork_type="line",
        )[0]
        tiff = save_figure(
            fig,
            output_root / "bitmap" / f"after_{kind}",
            spec=spec,
            formats=("tiff",),
            artwork_type="line",
        )[0]
        outputs[kind] = {"pdf": pdf, "tiff": tiff}
    for state_cells in cells.values():
        for fig, _ in state_cells.values():
            plt.close(fig)
    for fig, _ in submission_samples.values():
        plt.close(fig)
    return {"previews": previews, "samples": outputs}


def main() -> None:
    generate_outputs()


if __name__ == "__main__":
    main()
