from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_rgba
from matplotlib.mathtext import MathTextParser
from matplotlib.transforms import Bbox
from PIL import Image

import check_exported_figure_metadata as metadata_checker
from elsevier_plot_style import apply_journal_style, load_profile
from examples.readme.generate_before_after import (
    build_readme_cells,
    build_submission_samples,
    generate_outputs,
)


STATES = ("before", "after")
PLOT_KINDS = ("line", "bar", "scatter")


def _pairs(cells: dict[str, dict[str, tuple]]) -> dict[str, tuple]:
    return {
        kind: (cells["before"][kind][1], cells["after"][kind][1])
        for kind in PLOT_KINDS
    }


def _close_cells(cells: dict[str, dict[str, tuple]]) -> None:
    for state_cells in cells.values():
        for figure, _ in state_cells.values():
            plt.close(figure)


def test_readme_cells_are_six_independent_matching_figures(profile_path: Path) -> None:
    style = apply_journal_style(profile_path)
    cells = build_readme_cells(style)
    pairs = _pairs(cells)

    assert tuple(cells) == STATES
    assert all(tuple(cells[state]) == PLOT_KINDS for state in STATES)
    for state_cells in cells.values():
        for figure, axis in state_cells.values():
            assert figure.axes == [axis]
            assert figure.texts == []
            assert figure.get_figwidth() == pytest.approx(90.0 / 25.4)
            assert figure.get_figheight() == pytest.approx(60.0 / 25.4)

    before_line, after_line = pairs["line"]
    for before, after in zip(before_line.lines, after_line.lines, strict=True):
        np.testing.assert_allclose(before.get_xdata(), after.get_xdata())
        np.testing.assert_allclose(before.get_ydata(), after.get_ydata())

    before_bar, after_bar = pairs["bar"]
    assert len(before_bar.patches) == 8
    assert len(after_bar.patches) == 8
    np.testing.assert_allclose(
        [patch.get_height() for patch in before_bar.patches],
        [patch.get_height() for patch in after_bar.patches],
    )
    np.testing.assert_allclose(
        [patch.get_x() + patch.get_width() / 2 for patch in before_bar.patches],
        [patch.get_x() + patch.get_width() / 2 for patch in after_bar.patches],
    )
    np.testing.assert_allclose(
        [patch.get_width() for patch in before_bar.patches],
        [patch.get_width() for patch in after_bar.patches],
    )

    before_scatter, after_scatter = pairs["scatter"]
    for before, after in zip(before_scatter.collections, after_scatter.collections, strict=True):
        np.testing.assert_allclose(before.get_offsets(), after.get_offsets())

    for before, after in pairs.values():
        np.testing.assert_allclose(before.get_xlim(), after.get_xlim())
        np.testing.assert_allclose(before.get_ylim(), after.get_ylim())
    _close_cells(cells)

    samples = build_submission_samples(style)
    for figure, _ in samples.values():
        assert figure.get_figwidth() == pytest.approx(140.0 / 25.4)
        assert figure.get_figheight() == pytest.approx((140.0 / 1.5) / 25.4)
        plt.close(figure)


def test_after_cells_use_profile_helpers_and_plain_f1(profile_path: Path) -> None:
    style = apply_journal_style(profile_path)
    cells = build_readme_cells(style)
    pairs = _pairs(cells)

    for before, after in pairs.values():
        assert before.xaxis.label.get_fontsize() == pytest.approx(4.0)
        assert before.yaxis.label.get_fontsize() == pytest.approx(4.0)
        assert before.title.get_fontsize() == pytest.approx(4.0)
        assert all(label.get_fontsize() == pytest.approx(3.5) for label in before.get_xticklabels())
        assert all(label.get_fontsize() == pytest.approx(3.5) for label in before.get_yticklabels())
        assert all(text.get_fontsize() == pytest.approx(3.5) for text in before.get_legend().get_texts())
        assert after.xaxis.label.get_fontsize() == pytest.approx(11.0)
        assert after.yaxis.label.get_fontsize() == pytest.approx(11.0)
        assert all(label.get_fontsize() == pytest.approx(10.0) for label in after.get_xticklabels())
        assert all(label.get_fontsize() == pytest.approx(10.0) for label in after.get_yticklabels())
        assert not any(line.get_visible() for line in after.get_xgridlines() + after.get_ygridlines())

    before_line, after_line = pairs["line"]
    assert before_line.get_title() == "Training progress"
    assert after_line.get_title() == ""
    assert before_line.get_ylabel() == "Validation loss, L_val"
    assert after_line.get_ylabel() == r"Validation loss, $\mathcal{L}_{\mathrm{val}}$"
    assert before_line.get_legend().get_frame_on()
    assert not after_line.get_legend().get_frame_on()
    assert all(line.get_linewidth() == pytest.approx(style["line"]["linewidth"]) for line in after_line.lines)
    assert all(line.get_markersize() == pytest.approx(style["line"]["marker_size"]) for line in after_line.lines)
    assert len({line.get_marker() for line in after_line.lines}) == len(after_line.lines)

    before_bar, after_bar = pairs["bar"]
    assert before_bar.get_title() == "Model comparison"
    assert after_bar.get_title() == ""
    assert before_bar.get_ylabel() == "Test F1 score"
    assert after_bar.get_ylabel() == "Test F1 score"
    assert "$F_1$" not in after_bar.get_ylabel()
    assert [label.get_text() for label in after_bar.get_xticklabels()] == ["A", "B", "C", "Ours"]
    assert [text.get_text() for text in after_bar.get_legend().get_texts()] == ["Stage 1", "Stage 2"]
    assert before_bar.get_legend().get_frame_on()
    assert not after_bar.get_legend().get_frame_on()
    assert all(patch.get_linewidth() == pytest.approx(style["bar"]["linewidth"]) for patch in after_bar.patches)
    assert all(patch.get_width() == pytest.approx(style["bar"]["width"]) for patch in after_bar.patches)
    assert all(patch.get_alpha() == pytest.approx(style["bar"]["alpha"]) for patch in after_bar.patches)
    expected_edge = to_rgba(style["bar"]["edgecolor"], alpha=style["bar"]["alpha"])
    assert all(patch.get_edgecolor() == pytest.approx(expected_edge) for patch in after_bar.patches)
    stage_colors = [after_bar.patches[0].get_facecolor(), after_bar.patches[4].get_facecolor()]
    before_stage_colors = [before_bar.patches[0].get_facecolor(), before_bar.patches[4].get_facecolor()]
    for before_color, after_color in zip(before_stage_colors, stage_colors, strict=True):
        np.testing.assert_allclose(before_color[:3], after_color[:3])
    np.testing.assert_allclose(before_stage_colors[0][:3], to_rgba("#0072B2")[:3])
    np.testing.assert_allclose(before_stage_colors[1][:3], to_rgba("#D55E00")[:3])

    before_scatter, after_scatter = pairs["scatter"]
    assert before_scatter.get_title() == "Accuracy-latency trade-off"
    assert after_scatter.get_title() == ""
    assert before_scatter.get_xlabel() == "Latency t (ms)"
    assert after_scatter.get_xlabel() == r"Latency, $t$ (ms)"
    assert before_scatter.get_ylabel() == "Test F1 score"
    assert after_scatter.get_ylabel() == "Test F1 score"
    assert "$F_1$" not in after_scatter.get_ylabel()
    assert before_scatter.get_legend().get_frame_on()
    assert not after_scatter.get_legend().get_frame_on()
    assert all(collection.get_sizes()[0] == pytest.approx(style["scatter"]["size"]) for collection in after_scatter.collections)
    first_marker = after_scatter.collections[0].get_paths()[0].vertices
    second_marker = after_scatter.collections[1].get_paths()[0].vertices
    assert not np.array_equal(first_marker, second_marker)

    parser = MathTextParser("path")
    parser.parse(after_line.get_ylabel())
    parser.parse(after_scatter.get_xlabel())
    assert plt.rcParams["mathtext.fontset"] == style["font"]["mathtext_fontset"]
    _close_cells(cells)


def test_cell_content_fits_the_source_canvas_before_table_scaling(profile_path: Path) -> None:
    style = apply_journal_style(profile_path)
    cells = build_readme_cells(style)

    for state_cells in cells.values():
        for figure, axis in state_cells.values():
            figure.set_dpi(300)
            figure.canvas.draw()
            renderer = figure.canvas.get_renderer()
            width, height = figure.canvas.get_width_height()
            canvas_box = Bbox.from_bounds(0, 0, width, height)
            texts = [
                axis.title,
                axis.xaxis.label,
                axis.yaxis.label,
                *axis.get_legend().get_texts(),
            ]
            for text in texts:
                if text.get_visible() and text.get_text():
                    bbox = text.get_window_extent(renderer)
                    assert canvas_box.contains(bbox.x0, bbox.y0)
                    assert canvas_box.contains(bbox.x1, bbox.y1)
            legend_box = axis.get_legend().get_window_extent(renderer)
            assert canvas_box.contains(legend_box.x0, legend_box.y0)
            assert canvas_box.contains(legend_box.x1, legend_box.y1)

    after_bar = cells["after"]["bar"][1]
    renderer = cells["after"]["bar"][0].canvas.get_renderer()
    bar_legend_box = after_bar.get_legend().get_window_extent(renderer)
    assert not any(bar_legend_box.overlaps(patch.get_window_extent(renderer)) for patch in after_bar.patches)

    before_scatter = cells["before"]["scatter"][1]
    after_scatter = cells["after"]["scatter"][1]
    assert before_scatter.get_xlim() == pytest.approx((17.0, 55.0))
    assert after_scatter.get_xlim() == pytest.approx((17.0, 55.0))
    renderer = cells["after"]["scatter"][0].canvas.get_renderer()
    legend_box = after_scatter.get_legend().get_window_extent(renderer).padded(4.0)
    for collection in after_scatter.collections:
        display_points = after_scatter.transData.transform(np.asarray(collection.get_offsets()))
        assert not any(legend_box.contains(x, y) for x, y in display_points)
    _close_cells(cells)


def test_readme_outputs_have_web_and_submission_contracts(
    tmp_path: Path,
    profile_path: Path,
) -> None:
    outputs = generate_outputs(tmp_path)

    assert tuple(outputs["previews"]) == STATES
    for state in STATES:
        assert tuple(outputs["previews"][state]) == PLOT_KINDS
        for kind, preview_path in outputs["previews"][state].items():
            assert preview_path.parent.name == "comparison"
            assert preview_path.stem == f"{state}-{kind}"
            with Image.open(preview_path) as preview:
                assert preview.mode == "RGB"
                assert preview.size[0] == pytest.approx(1063, abs=1)
                assert preview.size[1] == pytest.approx(709, abs=1)
                assert preview.info["dpi"][0] == pytest.approx(300, abs=0.5)

    assert tuple(outputs["samples"]) == PLOT_KINDS
    profile = load_profile(profile_path)
    for kind, sample in outputs["samples"].items():
        assert sample["pdf"].parent.name == "vector"
        assert sample["tiff"].parent.name == "bitmap"
        assert sample["pdf"].stem == f"after_{kind}"
        assert sample["tiff"].stem == f"after_{kind}"

        with Image.open(sample["tiff"]) as tiff:
            assert tiff.mode == "RGB"
            assert tiff.info["dpi"][0] == pytest.approx(1000, abs=0.5)
            width_mm = tiff.width / tiff.info["dpi"][0] * 25.4
            assert width_mm == pytest.approx(140, abs=0.05)

        findings = metadata_checker.check_bitmap(
            sample["tiff"],
            "result",
            "line",
            "one-half",
            "editor",
            profile,
        )
        assert not any(finding.severity == "FAIL" for finding in findings)

        pdf = sample["pdf"].read_bytes()
        assert pdf.startswith(b"%PDF")
        assert b"/FontFile2" in pdf
        media_box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)", pdf)
        assert media_box is not None
        width_mm = float(media_box.group(1)) / 72 * 25.4
        assert width_mm == pytest.approx(140, abs=0.05)
