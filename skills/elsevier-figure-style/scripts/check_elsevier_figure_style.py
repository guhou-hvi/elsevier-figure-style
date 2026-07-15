from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from elsevier_plot_style import DEFAULT_PROFILE_PATH, ProfileError, load_profile


FIGURE_CALLS = {
    "line": {
        "plot",
        "step",
        "errorbar",
        "fill_between",
        "semilogx",
        "semilogy",
        "loglog",
        "axhline",
        "axvline",
        "hlines",
        "vlines",
    },
    "heatmap": {"imshow", "matshow", "pcolormesh", "contourf"},
    "bar": {"bar", "barh"},
    "scatter": {"scatter"},
}
ALL_FIGURE_CALLS = set().union(*FIGURE_CALLS.values())
PLOTTING_MODULES = {"matplotlib", "seaborn"}
HELPER_MODULES = {
    "elsevier_plot_style",
    "figure_style",
    "figure_style.plot_style",
}
STYLE_HELPER_CALLS = {
    "apply_elsevier_style",
    "apply_journal_style",
    "load_profile",
    "load_style",
    "line_style_kwargs",
    "band_style_kwargs",
    "bar_style_kwargs",
    "scatter_style_kwargs",
    "heatmap_kwargs",
    "colorbar_kwargs",
    "style_axis",
    "style_colorbar",
    "annotate_panel",
    "save_figure",
}
STYLE_KWARGS = {
    "line": {"color", "c", "marker", "markersize", "linewidth", "lw", "alpha", "capsize"},
    "heatmap": {"cmap", "interpolation", "aspect"},
    "bar": {"color", "edgecolor", "linewidth", "lw", "alpha", "width", "height", "capsize"},
    "scatter": {"color", "c", "marker", "s", "alpha", "edgecolor", "edgecolors", "linewidth", "linewidths"},
}
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__", ".pytest_cache"}
DISPLAY_TEXT_CALLS = {
    "annotate",
    "set_label",
    "set_xlabel",
    "set_ylabel",
    "set_zlabel",
    "set_title",
    "set_xticklabels",
    "set_yticklabels",
    "set_xticks",
    "set_yticks",
    "suptitle",
    "text",
    "title",
    "xlabel",
    "ylabel",
}
UNIT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?(?:mm|cm|m|km|um|nm|s|ms|min|h|kg|g|mg|N|kN|Pa|kPa|MPa|GPa|Hz|kHz|MHz|GHz|V|A|W|J|K|degC)\b"
)
STEP_PATTERN = re.compile(r"\bstep\d+\b", re.IGNORECASE)
OVERRIDE_PATTERN = re.compile(
    r"#\s*figure-style:\s*allow\s+([A-Z]+-[A-Z0-9-]+)\s+-\s+(.+?)\s*$",
    re.IGNORECASE,
)


@dataclass
class Finding:
    severity: str
    path: str
    line: int
    rule_id: str
    message: str
    allow_override: bool = False


@dataclass
class ImportBindings:
    helper_functions: set[str]
    helper_modules: set[str]
    json_modules: set[str]
    json_load_functions: set[str]
    matplotlib_modules: set[str]
    pyplot_modules: set[str]
    helper_wildcard: bool = False


def profile_rank(profile: dict[str, Any], name: str) -> int:
    order = profile["profiles"]["order"]
    if name not in order:
        raise ProfileError(f"unknown profile {name!r}; expected one of {order}")
    return order.index(name)


def detector_enabled(profile: dict[str, Any], active: str, detector_name: str) -> bool:
    detector = profile["audit"]["detectors"][detector_name]
    return profile_rank(profile, active) >= profile_rank(profile, detector["minimum_profile"])


def detector_finding(
    profile: dict[str, Any],
    active: str,
    detector_name: str,
    path: Path,
    line: int,
    message: str,
    *,
    severity: str | None = None,
) -> Finding | None:
    if not detector_enabled(profile, active, detector_name):
        return None
    detector = profile["audit"]["detectors"][detector_name]
    return Finding(
        severity or detector["severity"],
        path.as_posix(),
        line,
        detector["rule_id"],
        message,
        bool(detector["allow_override"]),
    )


def parse_overrides(text: str) -> dict[int, set[str]]:
    overrides: dict[int, set[str]] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = OVERRIDE_PATTERN.search(line)
        if match:
            overrides.setdefault(line_number, set()).add(match.group(1).upper())
    return overrides


def is_overridden(overrides: dict[int, set[str]], rule_id: str, line: int) -> bool:
    rule_id = rule_id.upper()
    return rule_id in overrides.get(line, set()) or rule_id in overrides.get(line - 1, set())


def append_finding(
    findings: list[Finding],
    finding: Finding | None,
    overrides: dict[int, set[str]],
) -> None:
    if finding is None:
        return
    if finding.allow_override and is_overridden(overrides, finding.rule_id, finding.line):
        return
    findings.append(finding)


def iter_py_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() == ".py" else []
    return sorted(
        candidate
        for candidate in path.rglob("*.py")
        if candidate.is_file() and not any(part in SKIP_DIRS for part in candidate.parts)
    )


def iter_calls(tree: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return ""


def attribute_chain(node: ast.AST) -> tuple[str, ...]:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return tuple(reversed(parts))
    return ()


def _is_helper_module(module: str) -> bool:
    return module in HELPER_MODULES or module.endswith(".elsevier_plot_style")


def collect_import_bindings(tree: ast.AST) -> ImportBindings:
    bindings = ImportBindings(set(), set(), set(), set(), set(), set())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                if _is_helper_module(alias.name):
                    bindings.helper_modules.add(bound)
                if alias.name == "json":
                    bindings.json_modules.add(bound)
                if alias.name == "matplotlib":
                    bindings.matplotlib_modules.add(bound)
                elif alias.name == "matplotlib.pyplot":
                    if alias.asname:
                        bindings.pyplot_modules.add(bound)
                    else:
                        bindings.matplotlib_modules.add("matplotlib")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if _is_helper_module(node.module):
                for alias in node.names:
                    if alias.name == "*":
                        bindings.helper_wildcard = True
                    elif alias.name in STYLE_HELPER_CALLS:
                        bindings.helper_functions.add(alias.asname or alias.name)
            elif node.module == "json":
                for alias in node.names:
                    if alias.name in {"load", "loads"}:
                        bindings.json_load_functions.add(alias.asname or alias.name)
            elif node.module == "matplotlib":
                for alias in node.names:
                    if alias.name == "pyplot":
                        bindings.pyplot_modules.add(alias.asname or alias.name)
    return bindings


def _simple_path_bindings(tree: ast.AST) -> dict[str, set[str]]:
    values: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        target: ast.AST | None = None
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if not isinstance(target, ast.Name) or value is None:
            continue
        strings = set(_string_constants(value))
        if strings:
            values[target.id] = strings
    return values


def _looks_like_manifest_path(value: str) -> bool:
    lowered = value.lower().replace("\\", "/")
    if not lowered.endswith(".json"):
        return False
    name = lowered.rsplit("/", 1)[-1]
    return any(token in name for token in ("figure_style", "journal", "manifest", "profile"))


def _is_bound_helper_call(call: ast.Call, bindings: ImportBindings) -> bool:
    if isinstance(call.func, ast.Name):
        return call.func.id in bindings.helper_functions or (
            bindings.helper_wildcard and call.func.id in STYLE_HELPER_CALLS
        )
    chain = attribute_chain(call.func)
    return bool(
        len(chain) == 2
        and chain[0] in bindings.helper_modules
        and chain[1] in STYLE_HELPER_CALLS
    )


def _is_direct_profile_load(
    call: ast.Call,
    bindings: ImportBindings,
    path_bindings: dict[str, set[str]],
) -> bool:
    is_json_load = False
    if isinstance(call.func, ast.Name):
        is_json_load = call.func.id in bindings.json_load_functions
    else:
        chain = attribute_chain(call.func)
        is_json_load = bool(
            len(chain) == 2 and chain[0] in bindings.json_modules and chain[1] in {"load", "loads"}
        )
    if not is_json_load:
        return False

    candidates = set(_string_constants(call))
    for item in ast.walk(call):
        if isinstance(item, ast.Name):
            candidates.update(path_bindings.get(item.id, set()))
    return any(_looks_like_manifest_path(value) for value in candidates)


def has_plotting_import(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".", 1)[0] in PLOTTING_MODULES for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] in PLOTTING_MODULES:
                return True
    return False


def family_for_call(name: str) -> str:
    for family, names in FIGURE_CALLS.items():
        if name in names:
            return family
    return ""


def figure_families(tree: ast.AST) -> set[str]:
    if not has_plotting_import(tree):
        return set()
    return {
        family
        for call in iter_calls(tree)
        if (family := family_for_call(call_name(call)))
    }


def first_figure_line(tree: ast.AST) -> int:
    lines = [
        getattr(call, "lineno", 1)
        for call in iter_calls(tree)
        if call_name(call) in ALL_FIGURE_CALLS
    ]
    return min(lines) if lines else 1


def _string_constants(node: ast.AST) -> list[str]:
    return [
        item.value
        for item in ast.walk(node)
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    ]


def has_style_usage(tree: ast.AST) -> bool:
    """Return true only for an actual helper call or direct profile load call."""
    bindings = collect_import_bindings(tree)
    path_bindings = _simple_path_bindings(tree)
    return any(
        _is_bound_helper_call(call, bindings) or _is_direct_profile_load(call, bindings, path_bindings)
        for call in iter_calls(tree)
    )


def constant_number(node: ast.AST) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = constant_number(node.operand)
        return -value if value is not None else None
    return None


def keyword_number(call: ast.Call, name: str) -> float | None:
    for keyword in call.keywords:
        if keyword.arg == name:
            return constant_number(keyword.value)
    return None


def is_plot_title_call(call: ast.Call) -> bool:
    if isinstance(call.func, ast.Attribute):
        if call.func.attr == "set_title":
            return True
        if call.func.attr == "title" and isinstance(call.func.value, ast.Name):
            return call.func.value.id in {"plt", "pyplot"}
    return isinstance(call.func, ast.Name) and call.func.id == "title"


def _explicit_true(call: ast.Call, *keyword_names: str) -> bool:
    if call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value is True:
        return True
    return any(
        keyword.arg in keyword_names
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is True
        for keyword in call.keywords
    )


def _is_manual_rcparams_call(call: ast.Call, bindings: ImportBindings) -> bool:
    chain = attribute_chain(call.func)
    return bool(
        len(chain) == 3
        and chain[0] in bindings.pyplot_modules | bindings.matplotlib_modules
        and chain[1:] == ("rcParams", "update")
    )


def _is_manual_style_call(call: ast.Call, bindings: ImportBindings) -> bool:
    chain = attribute_chain(call.func)
    return bool(
        len(chain) == 3
        and chain[0] in bindings.pyplot_modules | bindings.matplotlib_modules
        and chain[1:] == ("style", "use")
    )


def _is_rcparams_target(node: ast.AST, bindings: ImportBindings) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    chain = attribute_chain(node.value)
    return bool(
        len(chain) == 2
        and chain[0] in bindings.pyplot_modules | bindings.matplotlib_modules
        and chain[1] == "rcParams"
    )


def check_ast_calls(
    path: Path,
    tree: ast.AST,
    active_profile: str,
    profile: dict[str, Any],
    overrides: dict[int, set[str]],
) -> list[Finding]:
    findings: list[Finding] = []
    bindings = collect_import_bindings(tree)
    halftone_floor = float(profile["audit"]["artwork_types"]["halftone"]["minimum_dpi"])
    combination_floor = float(profile["audit"]["artwork_types"]["combination"]["minimum_dpi"])
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        if any(_is_rcparams_target(target, bindings) for target in targets):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "manual_rcparams",
                    path,
                    getattr(node, "lineno", 0),
                    "manual rcParams assignment; prefer apply_journal_style()",
                ),
                overrides,
            )
    for call in iter_calls(tree):
        line_number = getattr(call, "lineno", 0)
        name = call_name(call)
        if _is_manual_rcparams_call(call, bindings):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "manual_rcparams",
                    path,
                    line_number,
                    "manual rcParams update; prefer apply_journal_style()",
                ),
                overrides,
            )
        if _is_manual_style_call(call, bindings):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "manual_rcparams",
                    path,
                    line_number,
                    "manual style sheet use; prefer the selected journal profile",
                ),
                overrides,
            )
        if name == "grid" and _explicit_true(call, "visible", "b"):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "grid",
                    path,
                    line_number,
                    "grid enabled; verify it improves readability and is not default decoration",
                ),
                overrides,
            )

        if name == "savefig":
            dpi = keyword_number(call, "dpi")
            if dpi is not None and dpi < halftone_floor:
                append_finding(
                    findings,
                    detector_finding(
                        profile,
                        active_profile,
                        "low_dpi",
                        path,
                        line_number,
                        f"export dpi below {halftone_floor:g}; check artwork-type requirements",
                    ),
                    overrides,
                )
            elif dpi is not None and dpi < combination_floor:
                append_finding(
                    findings,
                    detector_finding(
                        profile,
                        active_profile,
                        "low_dpi",
                        path,
                        line_number,
                        "dpi may be low for combination or line art; classify the artwork type",
                        severity="WARN",
                    ),
                    overrides,
                )

        if name == "minorticks_on":
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "minor_ticks",
                    path,
                    line_number,
                    "minor ticks enabled; the editor profile expects them removed unless justified",
                ),
                overrides,
            )
        if name == "tick_params" and any(
            keyword.arg == "which"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "minor"
            for keyword in call.keywords
        ):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "minor_tick_style",
                    path,
                    line_number,
                    "minor-tick styling detected; verify the intentional override",
                ),
                overrides,
            )
    return findings


def check_string_literals(
    path: Path,
    tree: ast.AST,
    active_profile: str,
    profile: dict[str, Any],
    overrides: dict[int, set[str]],
) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[int] = set()
    for call in iter_calls(tree):
        name = call_name(call)
        nodes: list[ast.AST] = []
        if name in DISPLAY_TEXT_CALLS:
            nodes.extend(call.args)
            nodes.extend(keyword.value for keyword in call.keywords)
        elif family_for_call(name):
            nodes.extend(keyword.value for keyword in call.keywords if keyword.arg == "label")
        for container in nodes:
            for node in ast.walk(container):
                if id(node) in seen or not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                    continue
                seen.add(id(node))
                line = getattr(node, "lineno", 0)
                value = node.value
                if UNIT_PATTERN.search(value):
                    append_finding(
                        findings,
                        detector_finding(
                            profile,
                            active_profile,
                            "unit_spacing",
                            path,
                            line,
                            f"possible missing space between number and unit in displayed text {value!r}",
                        ),
                        overrides,
                    )
                if STEP_PATTERN.search(value):
                    append_finding(
                        findings,
                        detector_finding(
                            profile,
                            active_profile,
                            "step_spacing",
                            path,
                            line,
                            f"possible missing space between 'step' and number in displayed text {value!r}",
                        ),
                        overrides,
                    )
    return findings


def is_literal_style_value(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return is_literal_style_value(node.operand)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(is_literal_style_value(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or is_literal_style_value(key)) and is_literal_style_value(value)
            for key, value in zip(node.keys, node.values)
        )
    return False


def check_call_styles(
    path: Path,
    tree: ast.AST,
    active_profile: str,
    profile: dict[str, Any],
    overrides: dict[int, set[str]],
) -> list[Finding]:
    findings: list[Finding] = []
    for call in iter_calls(tree):
        name = call_name(call)
        family = family_for_call(name)
        if family:
            for keyword in call.keywords:
                if keyword.arg in STYLE_KWARGS[family] and is_literal_style_value(keyword.value):
                    line = getattr(keyword.value, "lineno", getattr(call, "lineno", 0))
                    append_finding(
                        findings,
                        detector_finding(
                            profile,
                            active_profile,
                            "hardcoded_style",
                            path,
                            line,
                            f"hardcoded {family} style keyword {keyword.arg!r}; use the helper or document the override",
                        ),
                        overrides,
                    )

        fontsize = keyword_number(call, "fontsize")
        official = profile["audit"]["detectors"]["font_official"]
        editor = profile["audit"]["detectors"]["font_editor"]
        if fontsize is not None and fontsize < float(official["threshold"]):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "font_official",
                    path,
                    getattr(call, "lineno", 0),
                    f"fontsize {fontsize:g} pt is below the configured 6 pt lower bound",
                ),
                overrides,
            )
        elif fontsize is not None and fontsize < float(editor["threshold"]):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "font_editor",
                    path,
                    getattr(call, "lineno", 0),
                    f"fontsize {fontsize:g} pt may be too small at final size",
                ),
                overrides,
            )

        if is_plot_title_call(call):
            append_finding(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "plot_title",
                    path,
                    getattr(call, "lineno", 0),
                    "visible plot title detected; prefer a manuscript-level caption",
                ),
                overrides,
            )
    return findings


def check_file(
    path: Path,
    active_profile: str,
    profile: dict[str, Any],
) -> tuple[set[str], list[Finding]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return set(), [Finding("FAIL", path.as_posix(), exc.lineno or 0, "PYTHON", f"syntax error: {exc.msg}")]

    families = figure_families(tree)
    overrides = parse_overrides(text)
    findings = check_ast_calls(path, tree, active_profile, profile, overrides)
    findings.extend(check_string_literals(path, tree, active_profile, profile, overrides))
    findings.extend(check_call_styles(path, tree, active_profile, profile, overrides))

    if families and not has_style_usage(tree):
        append_finding(
            findings,
            detector_finding(
                profile,
                active_profile,
                "style_integration",
                path,
                first_figure_line(tree),
                "matplotlib figure detected without an actual journal-style helper or profile load call",
            ),
            overrides,
        )
    return families, findings


def status_for(findings: list[Finding]) -> str:
    if any(item.severity == "FAIL" for item in findings):
        return "FAIL"
    if any(item.severity == "WARN" for item in findings):
        return "WARN"
    return "PASS"


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    if fail_on == "never":
        return False
    if fail_on == "warn":
        return any(item.severity in {"FAIL", "WARN"} for item in findings)
    return any(item.severity == "FAIL" for item in findings)


def ordered_findings(findings: list[Finding]) -> list[Finding]:
    severity_rank = {"FAIL": 0, "WARN": 1}
    return sorted(
        findings,
        key=lambda item: (severity_rank.get(item.severity, 9), item.path, item.line, item.message),
    )


def finding_payload(finding: Finding) -> dict[str, Any]:
    payload = asdict(finding)
    payload.pop("allow_override", None)
    return payload


def print_text(findings: list[Finding], summary: dict[str, Any]) -> None:
    for finding in ordered_findings(findings):
        line = f":{finding.line}" if finding.line else ""
        print(f"[{finding.severity}] {finding.path}{line} [{finding.rule_id}] - {finding.message}")
    family_summary = " ".join(f"{name}={count}" for name, count in summary["families"].items())
    print(
        f"[{summary['status']}] profile={summary['profile']} scanned_files={summary['scanned_files']} "
        f"figure_files={summary['figure_files']} {family_summary} "
        f"fails={summary['fails']} warns={summary['warns']}"
    )


def print_cli_error(output_format: str, category: str, message: str) -> None:
    if output_format == "json":
        payload = {
            "summary": {"status": "FAIL", "error_type": category},
            "findings": [
                {
                    "severity": "FAIL",
                    "path": "",
                    "line": 0,
                    "rule_id": category,
                    "message": message,
                }
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"[FAIL] [{category}] - {message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Static-check Python figure scripts with a journal figure profile.")
    parser.add_argument("--path", required=True, help="Python file or directory to scan.")
    parser.add_argument("--config", default=str(DEFAULT_PROFILE_PATH), help="Journal figure profile manifest.")
    parser.add_argument("--profile", default=None, help="Rule profile from the selected manifest.")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    parser.add_argument("--fail-on", choices=("fail", "warn", "never"), default="fail")
    parser.add_argument("--strict", action="store_true", help="Deprecated compatibility alias for --fail-on fail.")
    args = parser.parse_args()
    fail_on = "fail" if args.strict else args.fail_on

    try:
        profile = load_profile(args.config)
        active_profile = args.profile or profile["profiles"]["default"]
        profile_rank(profile, active_profile)
    except ProfileError as exc:
        print_cli_error(args.output_format, "CONFIG", str(exc))
        return 2

    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print_cli_error(args.output_format, "INPUT", f"path does not exist: {target.as_posix()}")
        return 2
    files = iter_py_files(target)
    if not files:
        print_cli_error(args.output_format, "INPUT", f"no Python files found: {target.as_posix()}")
        return 2

    findings: list[Finding] = []
    family_counts = {family: 0 for family in FIGURE_CALLS}
    figure_files = 0
    for file in files:
        families, file_findings = check_file(file, active_profile, profile)
        if families:
            figure_files += 1
        for family in families:
            family_counts[family] += 1
        findings.extend(file_findings)

    if figure_files == 0 and not any(item.rule_id == "PYTHON" for item in findings):
        print_cli_error(
            args.output_format,
            "INPUT",
            f"no supported matplotlib figure calls found: {target.as_posix()}",
        )
        return 2

    summary = {
        "status": status_for(findings),
        "profile": active_profile,
        "profile_id": profile["identity"]["id"],
        "scanned_files": len(files),
        "figure_files": figure_files,
        "families": family_counts,
        "fails": sum(item.severity == "FAIL" for item in findings),
        "warns": sum(item.severity == "WARN" for item in findings),
    }
    if args.output_format == "json":
        print(
            json.dumps(
                {"summary": summary, "findings": [finding_payload(item) for item in ordered_findings(findings)]},
                indent=2,
            )
        )
    else:
        print_text(findings, summary)
    return 1 if should_fail(findings, fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
