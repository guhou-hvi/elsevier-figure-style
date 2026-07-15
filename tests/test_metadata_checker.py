from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

import check_exported_figure_metadata as checker
from elsevier_plot_style import load_profile


def save_image(path: Path, *, size: tuple[int, int] = (1600, 1000), mode: str = "RGB", dpi: int = 300) -> Path:
    color = (255, 255, 255, 255) if mode == "RGBA" else "white"
    Image.new(mode, size, color).save(path, dpi=(dpi, dpi))
    return path


def test_line_art_low_dpi_fails(tmp_path: Path, profile_path: Path) -> None:
    path = save_image(tmp_path / "line.tiff", dpi=300)
    findings = checker.check_bitmap(path, "result", "line", "auto", "official", load_profile(profile_path))
    assert any(item.severity == "FAIL" and item.rule_id == "OFF-07" for item in findings)


def test_graphical_abstract_dimensions_fail(tmp_path: Path, profile_path: Path) -> None:
    path = save_image(tmp_path / "ga.png", size=(900, 300), dpi=150)
    findings = checker.check_bitmap(
        path,
        "graphical-abstract",
        "auto",
        "graphical-abstract",
        "editor",
        load_profile(profile_path),
    )
    assert any(item.severity == "FAIL" and item.rule_id == "OFF-13" for item in findings)


def test_profile_gates_visual_heuristic(tmp_path: Path, profile_path: Path) -> None:
    path = save_image(tmp_path / "small.tiff", size=(200, 200), dpi=300)
    profile = load_profile(profile_path)
    official = checker.check_bitmap(path, "schematic", "halftone", "auto", "official", profile)
    editor = checker.check_bitmap(path, "schematic", "halftone", "auto", "editor", profile)
    assert not any(item.rule_id == "VIS-01" for item in official)
    assert any(item.rule_id == "VIS-01" for item in editor)


def test_png_and_alpha_warn(tmp_path: Path, profile_path: Path) -> None:
    path = tmp_path / "preview.png"
    Image.new("RGBA", (1600, 1000), (255, 255, 255, 128)).save(path, dpi=(1000, 1000))
    findings = checker.check_bitmap(path, "result", "line", "auto", "official", load_profile(profile_path))
    rule_ids = {item.rule_id for item in findings}
    assert "OFF-02" in rule_ids
    assert "OFF-09" in rule_ids


def test_jpeg_without_dpi_and_cmyk_warn(tmp_path: Path, profile_path: Path) -> None:
    path = tmp_path / "photo.jpg"
    Image.new("CMYK", (1200, 800), 0).save(path)
    findings = checker.check_bitmap(path, "result", "halftone", "auto", "official", load_profile(profile_path))
    messages = {item.rule_id: item.message for item in findings}
    assert "OFF-07" in messages
    assert "OFF-09" in messages


def test_target_layout_checks_pixel_width(tmp_path: Path, profile_path: Path) -> None:
    path = save_image(tmp_path / "narrow.tiff", size=(800, 600), dpi=300)
    findings = checker.check_bitmap(path, "result", "halftone", "single", "official", load_profile(profile_path))
    assert any(item.severity == "FAIL" and item.rule_id == "OFF-06" for item in findings)


def test_target_layout_checks_embedded_physical_width(tmp_path: Path, profile_path: Path) -> None:
    profile = load_profile(profile_path)
    exact = save_image(tmp_path / "exact.tiff", size=(1400, 900), dpi=254)
    oversized = save_image(tmp_path / "oversized.tiff", size=(1500, 900), dpi=254)
    exact_findings = checker.check_bitmap(exact, "result", "halftone", "one-half", "official", profile)
    oversized_findings = checker.check_bitmap(
        oversized, "result", "halftone", "one-half", "official", profile
    )
    assert not any(item.rule_id == "OFF-06" for item in exact_findings)
    assert any(item.severity == "FAIL" and item.rule_id == "OFF-06" for item in oversized_findings)


def test_opaque_alpha_channel_warns(tmp_path: Path, profile_path: Path) -> None:
    path = save_image(tmp_path / "opaque-alpha.tiff", mode="RGBA", dpi=300)
    findings = checker.check_bitmap(path, "result", "halftone", "auto", "official", load_profile(profile_path))
    assert any(item.rule_id == "OFF-09" and "opaque alpha channel" in item.message for item in findings)


def test_manual_eps_and_json_output(root: Path, profile_path: Path, tmp_path: Path) -> None:
    eps = tmp_path / "figure.eps"
    eps.write_text("%!PS-Adobe-3.0 EPSF-3.0\n", encoding="ascii")
    script = root / "skills/elsevier-figure-style/scripts/check_exported_figure_metadata.py"
    result = subprocess.run(
        [sys.executable, str(script), "--path", str(eps), "--config", str(profile_path), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["manual_files"] == 1
    assert any(item["rule_id"] == "STYLE-02" for item in payload["findings"])


def test_pdf_svg_and_eps_are_manual(profile_path: Path, tmp_path: Path) -> None:
    profile = load_profile(profile_path)
    for suffix in (".pdf", ".svg", ".eps"):
        path = tmp_path / f"figure{suffix}"
        path.write_text("synthetic fixture", encoding="utf-8")
    files = checker.iter_figure_files(tmp_path, profile)
    assert {path.suffix for path in files} == {".pdf", ".svg", ".eps"}
    for path in files:
        assert any(item.rule_id == "STYLE-02" for item in checker.check_manual(path, "official", profile))


def test_missing_path_is_input_error(root: Path, profile_path: Path, tmp_path: Path) -> None:
    script = root / "skills/elsevier-figure-style/scripts/check_exported_figure_metadata.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--path",
            str(tmp_path / "missing.png"),
            "--config",
            str(profile_path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["summary"]["error_type"] == "INPUT"
