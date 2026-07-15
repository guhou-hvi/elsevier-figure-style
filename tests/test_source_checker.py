from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

import check_elsevier_figure_style as checker
from elsevier_plot_style import load_profile


def write_script(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("call", "family"),
    [
        ("ax.plot([1], [2])", "line"),
        ("ax.errorbar([1], [2])", "line"),
        ("ax.fill_between([1], [1], [2])", "line"),
        ("ax.imshow([[1]])", "heatmap"),
        ("ax.bar([1], [2])", "bar"),
        ("ax.barh([1], [2])", "bar"),
        ("ax.scatter([1], [2])", "scatter"),
    ],
)
def test_figure_family_detection(call: str, family: str) -> None:
    tree = ast.parse(f"import matplotlib.pyplot as plt\nfig, ax = plt.subplots()\n{call}\n")
    assert family in checker.figure_families(tree)


def test_comment_string_and_unused_import_do_not_pass_style_gate() -> None:
    comment = ast.parse("# elsevier_plot_style\nimport matplotlib.pyplot as plt\nplt.plot([1], [2])")
    string = ast.parse("note = 'elsevier_figure_style.json'\nimport matplotlib.pyplot as plt\nplt.plot([1], [2])")
    unused = ast.parse("import elsevier_plot_style\nimport matplotlib.pyplot as plt\nplt.plot([1], [2])")
    assert not checker.has_style_usage(comment)
    assert not checker.has_style_usage(string)
    assert not checker.has_style_usage(unused)


def test_actual_helper_call_passes_style_gate() -> None:
    tree = ast.parse(
        "from elsevier_plot_style import apply_journal_style\n"
        "import matplotlib.pyplot as plt\n"
        "spec = apply_journal_style()\n"
        "plt.plot([1], [2])\n"
    )
    assert checker.has_style_usage(tree)


def test_helper_module_alias_and_vendored_alias_pass_style_gate() -> None:
    module_alias = ast.parse(
        "import elsevier_plot_style as figure_style\n"
        "import matplotlib.pyplot as plt\n"
        "figure_style.apply_journal_style()\n"
        "plt.plot([1], [2])\n"
    )
    vendored_alias = ast.parse(
        "from figure_style import apply_journal_style as apply_style\n"
        "import matplotlib.pyplot as plt\n"
        "apply_style()\n"
        "plt.plot([1], [2])\n"
    )
    assert checker.has_style_usage(module_alias)
    assert checker.has_style_usage(vendored_alias)

    wildcard = ast.parse(
        "from figure_style import *\n"
        "import matplotlib.pyplot as plt\n"
        "apply_journal_style()\n"
        "plt.plot([1], [2])\n"
    )
    assert checker.has_style_usage(wildcard)


def test_fake_or_unrelated_helper_names_do_not_pass_style_gate() -> None:
    fake_local = ast.parse(
        "import matplotlib.pyplot as plt\n"
        "def apply_journal_style():\n"
        "    return None\n"
        "apply_journal_style()\n"
        "plt.plot([1], [2])\n"
    )
    unrelated_object = ast.parse(
        "import matplotlib.pyplot as plt\n"
        "class Loader:\n"
        "    def load_profile(self):\n"
        "        return None\n"
        "Loader().load_profile()\n"
        "plt.plot([1], [2])\n"
    )
    assert not checker.has_style_usage(fake_local)
    assert not checker.has_style_usage(unrelated_object)


def test_direct_manifest_load_passes_style_gate() -> None:
    tree = ast.parse(
        "import json\n"
        "from pathlib import Path\n"
        "import matplotlib.pyplot as plt\n"
        "profile_path = Path('journal_profile.json')\n"
        "profile = json.loads(profile_path.read_text())\n"
        "plt.plot([1], [2])\n"
    )
    assert checker.has_style_usage(tree)


def test_override_suppresses_only_matching_rule(tmp_path: Path, profile_path: Path) -> None:
    source = write_script(
        tmp_path / "override.py",
        "from elsevier_plot_style import apply_journal_style\n"
        "import matplotlib.pyplot as plt\n"
        "spec = apply_journal_style()\n"
        "fig, ax = plt.subplots()\n"
        "# figure-style: allow STYLE-01 - threshold color is semantic\n"
        "ax.plot([1], [2], color='red')\n"
        "ax.set_xlabel('X', fontsize=5)\n",
    )
    _, findings = checker.check_file(source, "editor", load_profile(profile_path))
    assert not any(item.rule_id == "STYLE-01" for item in findings)
    assert any(item.rule_id == "OFF-05" for item in findings)


def test_style_gate_cannot_be_overridden(tmp_path: Path, profile_path: Path) -> None:
    source = write_script(
        tmp_path / "gate_override.py",
        "import matplotlib.pyplot as plt\n"
        "# figure-style: allow STYLE-01 - local color is semantic\n"
        "plt.plot([1], [2])\n",
    )
    _, findings = checker.check_file(source, "editor", load_profile(profile_path))
    assert any(item.severity == "FAIL" and item.rule_id == "STYLE-01" for item in findings)


def test_comments_and_unrelated_strings_do_not_trigger_pattern_findings(
    tmp_path: Path,
    profile_path: Path,
) -> None:
    source = write_script(
        tmp_path / "comments.py",
        "from elsevier_plot_style import apply_journal_style\n"
        "import matplotlib.pyplot as plt\n"
        "apply_journal_style()\n"
        "# Do not call plt.style.use('ggplot') or save with dpi=72.\n"
        "note = 'rcParams.update and step1 are documentation only'\n"
        "plt.plot([1], [2])\n",
    )
    _, findings = checker.check_file(source, "strict", load_profile(profile_path))
    assert findings == []


def test_real_ast_calls_trigger_and_profile_values_do_not_look_hardcoded(
    tmp_path: Path,
    profile_path: Path,
) -> None:
    source = write_script(
        tmp_path / "ast_calls.py",
        "from elsevier_plot_style import apply_journal_style\n"
        "import matplotlib.pyplot as plt\n"
        "spec = apply_journal_style()\n"
        "plt.rcParams.update({'font.size': 8})\n"
        "plt.rcParams['axes.linewidth'] = 0.5\n"
        "fig, ax = plt.subplots()\n"
        "ax.plot([1], [2], color=spec['palette']['cycle'][0])\n"
        "ax.grid(True)\n"
        "fig.savefig('figure.png', dpi=72)\n",
    )
    _, findings = checker.check_file(source, "strict", load_profile(profile_path))
    messages = [item.message for item in findings]
    assert any("manual rcParams" in message for message in messages)
    assert any("manual rcParams assignment" in message for message in messages)
    assert any("grid enabled" in message for message in messages)
    assert any("export dpi" in message for message in messages)
    assert not any("hardcoded line style" in message for message in messages)


def test_editor_rule_is_not_applied_in_official_profile(tmp_path: Path, profile_path: Path) -> None:
    source = write_script(
        tmp_path / "minor.py",
        "from elsevier_plot_style import apply_journal_style\n"
        "import matplotlib.pyplot as plt\n"
        "spec = apply_journal_style()\n"
        "fig, ax = plt.subplots()\n"
        "ax.plot([1], [2])\n"
        "ax.minorticks_on()\n",
    )
    profile = load_profile(profile_path)
    _, official = checker.check_file(source, "official", profile)
    _, editor = checker.check_file(source, "editor", profile)
    assert not any(item.rule_id == "ED-02" for item in official)
    assert any(item.rule_id == "ED-02" for item in editor)


def test_bad_demo_exits_nonzero(root: Path, profile_path: Path) -> None:
    command = [
        sys.executable,
        str(root / "skills/elsevier-figure-style/scripts/check_elsevier_figure_style.py"),
        "--path",
        str(root / "examples/bad/non_compliant_plot.py"),
        "--config",
        str(profile_path),
        "--profile",
        "editor",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "[ED-02]" in result.stdout


def test_json_output_and_missing_path(root: Path, profile_path: Path, tmp_path: Path) -> None:
    script = root / "skills/elsevier-figure-style/scripts/check_elsevier_figure_style.py"
    good = subprocess.run(
        [sys.executable, str(script), "--path", str(root / "examples/python"), "--config", str(profile_path), "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert good.returncode == 0
    good_payload = json.loads(good.stdout)
    assert good_payload["summary"]["status"] == "PASS"
    assert all("allow_override" not in item for item in good_payload["findings"])
    missing = subprocess.run(
        [
            sys.executable,
            str(script),
            "--path",
            str(tmp_path / "missing.py"),
            "--config",
            str(profile_path),
            "--format",
            "json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert missing.returncode == 2
    assert json.loads(missing.stdout)["summary"]["error_type"] == "INPUT"


def test_syntax_error_and_empty_directory_are_failures(profile_path: Path, tmp_path: Path) -> None:
    profile = load_profile(profile_path)
    broken = write_script(tmp_path / "broken.py", "def broken(:\n")
    _, findings = checker.check_file(broken, "editor", profile)
    assert any(item.severity == "FAIL" and item.rule_id == "PYTHON" for item in findings)

    script = Path(checker.__file__)
    empty = tmp_path / "empty"
    empty.mkdir()
    result = subprocess.run(
        [sys.executable, str(script), "--path", str(empty), "--config", str(profile_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2


def test_python_files_without_supported_figures_are_input_error(
    root: Path,
    profile_path: Path,
    tmp_path: Path,
) -> None:
    source = write_script(tmp_path / "plain.py", "print('no figure')\n")
    script = root / "skills/elsevier-figure-style/scripts/check_elsevier_figure_style.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--path",
            str(source),
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
