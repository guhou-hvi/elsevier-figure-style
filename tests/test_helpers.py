from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from elsevier_plot_style import (
    apply_elsevier_style,
    apply_journal_style,
    bar_style_kwargs,
    figure_size,
    figure_width,
    finalize_figure,
    load_profile,
    save_figure,
    savefig_kwargs,
    scatter_style_kwargs,
)


def test_generic_and_compatibility_api(profile_path: Path) -> None:
    generic = apply_journal_style(profile_path)
    compatibility = apply_elsevier_style(profile_path)
    assert generic["font"] == compatibility["font"]
    assert generic["font"]["size"] == pytest.approx(11.0)
    assert generic["font"]["label_size"] == pytest.approx(11.0)
    assert generic["font"]["tick_size"] == pytest.approx(10.0)
    assert generic["font"]["legend_size"] == pytest.approx(10.0)
    assert generic["line"]["linewidth"] == pytest.approx(1.0)
    assert generic["line"]["marker_size"] == pytest.approx(4.0)
    assert figure_width("single", generic) * 25.4 == pytest.approx(90.0)
    assert figure_width("one-half", generic) * 25.4 == pytest.approx(140.0)
    assert figure_width("double", generic) * 25.4 == pytest.approx(190.0)
    assert figure_width(spec=generic) == pytest.approx(figure_width("one-half", generic))
    width, height = figure_size(spec=generic)
    assert width * 25.4 == pytest.approx(140.0)
    assert width / height == pytest.approx(1.5)


def test_invalid_layout_and_orientation_raise(profile_path: Path) -> None:
    style = load_profile(profile_path)["style"]
    with pytest.raises(ValueError, match="unknown column"):
        figure_width("triple", style)
    with pytest.raises(ValueError, match="orientation"):
        bar_style_kwargs("score", spec=style, orientation="diagonal")
    with pytest.raises(ValueError, match="aspect_ratio"):
        figure_size(spec=style, aspect_ratio=0)


def test_scatter_uses_marker_cycle(profile_path: Path) -> None:
    style = load_profile(profile_path)["style"]
    first = scatter_style_kwargs("unknown-a", spec=style, index=0)["marker"]
    second = scatter_style_kwargs("unknown-b", spec=style, index=1)["marker"]
    assert first != second


def test_artwork_dpi(profile_path: Path) -> None:
    style = load_profile(profile_path)["style"]
    assert savefig_kwargs(style, artwork_type="halftone")["dpi"] == 300
    assert savefig_kwargs(style, artwork_type="combination")["dpi"] == 500
    assert savefig_kwargs(style, artwork_type="line")["dpi"] == 1000
    assert savefig_kwargs(style, artwork_type="line")["bbox_inches"] is None
    with pytest.raises(ValueError, match="artwork type"):
        savefig_kwargs(style, artwork_type="unknown")


def test_finalize_removes_single_data_axis_title_with_colorbar(profile_path: Path) -> None:
    style = load_profile(profile_path)["style"]
    fig, ax = plt.subplots()
    image = ax.imshow([[0, 1], [1, 0]])
    fig.colorbar(image, ax=ax)
    ax.set_title("Remove me")
    finalize_figure(fig, style)
    assert ax.get_title() == ""
    plt.close(fig)


def test_tiff_export_is_flattened_to_rgb(tmp_path: Path, profile_path: Path) -> None:
    from PIL import Image

    style = load_profile(profile_path)["style"]
    fig, ax = plt.subplots()
    ax.plot([1, 2], [2, 1])
    path = save_figure(
        fig,
        tmp_path / "figure",
        spec=style,
        formats=("tiff",),
        artwork_type="halftone",
    )[0]
    plt.close(fig)
    with Image.open(path) as image:
        assert image.mode == "RGB"
        assert image.info["dpi"][0] == pytest.approx(300, abs=0.5)


def test_default_export_keeps_exact_profile_canvas(tmp_path: Path, profile_path: Path) -> None:
    from PIL import Image

    style = load_profile(profile_path)["style"]
    width, height = figure_size(spec=style)
    fig, ax = plt.subplots(figsize=(width, height))
    ax.plot([1, 2], [2, 1])
    path = save_figure(fig, tmp_path / "exact", spec=style, formats=("tiff",), artwork_type="line")[0]
    plt.close(fig)
    with Image.open(path) as image:
        assert image.width / image.info["dpi"][0] * 25.4 == pytest.approx(140.0, abs=0.05)
