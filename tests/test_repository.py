from __future__ import annotations

from pathlib import Path

import yaml


def test_readmes_are_utf8_and_link_each_other(root: Path) -> None:
    english = (root / "README.md").read_text(encoding="utf-8")
    chinese = (root / "README.zh-CN.md").read_text(encoding="utf-8")
    assert "README.zh-CN.md" in english
    assert "README.md" in chinese
    assert "<owner>" not in english + chinese
    assert "D:\\PROGRAM" not in english + chinese
    assert "check_environment.py" in english + chinese
    assert "after the repository is published" not in english
    assert "GitHub 仓库发布后" not in chinese


def test_readmes_use_the_six_image_comparison_table(root: Path) -> None:
    english = (root / "README.md").read_text(encoding="utf-8")
    chinese = (root / "README.zh-CN.md").read_text(encoding="utf-8")
    links = (
        "before-line.png",
        "before-bar.png",
        "before-scatter.png",
        "after-line.png",
        "after-bar.png",
        "after-scatter.png",
    )
    for link in links:
        assert link in english
        assert link in chinese
    assert "| **Before / ad hoc** |" in english
    assert "| **After / profile-backed** |" in english
    assert "| **修改前 / 临时格式** |" in chinese
    assert "| **修改后 / profile 驱动** |" in chinese
    english_capabilities = (
        "Final-size readability",
        "Titles and formulas",
        "Layout and styling",
        "Series and legends",
        "Export checks",
    )
    chinese_capabilities = (
        "最终尺寸可读性",
        "标题与公式",
        "版式与样式",
        "系列与图例",
        "导出检查",
    )
    assert all(capability in english for capability in english_capabilities)
    assert all(capability in chinese for capability in chinese_capabilities)
    assert "before-after.png" not in english + chinese
    assert not (root / "docs/assets/before-after.png").exists()


def test_readme_hero_covers_eight_figure_workflow_pain_points(root: Path) -> None:
    english = (root / "README.md").read_text(encoding="utf-8")
    chinese = (root / "README.zh-CN.md").read_text(encoding="utf-8")
    english_scenarios = (
        "At the first plot",
        "On every new figure",
        "Months into writing",
        "When revisiting old figures",
        "At final export",
        "Across a team and toolchain",
        "After editorial feedback",
        "After changing journals",
    )
    chinese_scenarios = (
        "刚开始画图时",
        "每次新画一张图时",
        "写作几个月后",
        "重新修改旧图时",
        "最终导出时",
        "多人和多工具协作时",
        "收到编辑或审稿意见后",
        "更换目标期刊时",
    )
    assert all(scenario in english for scenario in english_scenarios)
    assert all(scenario in chinese for scenario in chinese_scenarios)
    assert "especially when you are new to research" in english
    assert "刚开始科研时" in chinese
    for unsupported_claim in ("guarantees compliance", "only for graduate students", "保证合规", "仅适用于研究生"):
        assert unsupported_claim not in english + chinese


def test_runtime_requirements_ship_with_skill(root: Path) -> None:
    skill_requirements = root / "skills/elsevier-figure-style/requirements.txt"
    root_requirements = (root / "requirements.txt").read_text(encoding="utf-8")
    assert skill_requirements.is_file()
    assert "skills/elsevier-figure-style/requirements.txt" in root_requirements
    assert (root / "SECURITY.md").is_file()


def test_yaml_files_parse(root: Path) -> None:
    paths = [
        root / ".github/workflows/ci.yml",
        root / ".github/ISSUE_TEMPLATE/figure-format-comment.yml",
        root / "skills/elsevier-figure-style/agents/openai.yaml",
        root / "CITATION.cff",
        root / ".github/dependabot.yml",
    ]
    for path in paths:
        assert yaml.safe_load(path.read_text(encoding="utf-8"))


def test_citation_and_license_are_consistent(root: Path) -> None:
    citation = yaml.safe_load((root / "CITATION.cff").read_text(encoding="utf-8"))
    english = (root / "README.md").read_text(encoding="utf-8")
    chinese = (root / "README.zh-CN.md").read_text(encoding="utf-8")
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    bibtex = """@software{ji_elsevier_figure_style_2026,
  author  = {Ji, Peng},
  title   = {elsevier-figure-style},
  version = {0.1.0},
  year    = {2026},
  url     = {https://github.com/guhou-hvi/elsevier-figure-style},
  license = {MIT}
}"""

    assert citation["authors"] == [{"given-names": "Peng", "family-names": "Ji"}]
    assert citation["type"] == "software"
    assert citation["version"] == "0.1.0"
    assert citation["repository-code"] == "https://github.com/guhou-hvi/elsevier-figure-style"
    assert citation["license"] == "MIT"
    assert "doi" not in citation
    assert "date-released" not in citation
    assert bibtex in english
    assert bibtex in chinese
    assert "## Citation\n" in english and "## License\n" in english
    assert "## 引用\n" in chinese and "## 许可\n" in chinese
    assert "Copyright (c) 2026 Peng Ji and contributors" in license_text
    assert "Copyright © 2026 Peng Ji and contributors" in english
    assert "Copyright © 2026 Peng Ji and contributors" in chinese
    assert "<ZENODO" not in english + chinese


def test_visual_audit_fixture_has_required_report_fields(root: Path) -> None:
    report = (root / "examples/schematic/expected_bad_visual_audit.md").read_text(encoding="utf-8")
    for field in ("Severity", "Location", "Source/Rule", "Recommended fix"):
        assert field in report
    assert "VIS-02" in report
