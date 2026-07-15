from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from elsevier_plot_style import DEFAULT_PROFILE_PATH, ProfileError, load_profile


@dataclass
class Finding:
    severity: str
    path: str
    rule_id: str
    message: str


def profile_rank(profile: dict[str, Any], name: str) -> int:
    order = profile["profiles"]["order"]
    if name not in order:
        raise ProfileError(f"unknown profile {name!r}; expected one of {order}")
    return order.index(name)


def detector_finding(
    profile: dict[str, Any],
    active: str,
    detector_name: str,
    path: Path,
    message: str,
    *,
    severity: str | None = None,
) -> Finding | None:
    detector = profile["audit"]["detectors"][detector_name]
    if profile_rank(profile, active) < profile_rank(profile, detector["minimum_profile"]):
        return None
    return Finding(
        severity or detector["severity"],
        path.as_posix(),
        detector["rule_id"],
        message,
    )


def add(findings: list[Finding], finding: Finding | None) -> None:
    if finding is not None:
        findings.append(finding)


def configured_extensions(profile: dict[str, Any], key: str) -> set[str]:
    return {value.lower() for value in profile["audit"]["file_formats"][key]}


def iter_figure_files(path: Path, profile: dict[str, Any]) -> list[Path]:
    supported = configured_extensions(profile, "bitmap") | configured_extensions(profile, "manual")
    if path.is_file():
        return [path] if path.suffix.lower() in supported else []
    return sorted(
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() in supported
    )


def dpi_from_image(image: Image.Image) -> tuple[float, float] | None:
    dpi = image.info.get("dpi")
    if not dpi or not hasattr(dpi, "__len__") or len(dpi) < 2:
        return None
    try:
        return float(dpi[0]), float(dpi[1])
    except (TypeError, ValueError):
        return None


def minimum_dpi(profile: dict[str, Any], artwork_type: str, figure_type: str) -> float:
    if figure_type == "graphical-abstract":
        return float(profile["audit"]["target_layouts"]["graphical-abstract"]["minimum_dpi"])
    if artwork_type == "auto":
        return 300.0
    return float(profile["audit"]["artwork_types"][artwork_type]["minimum_dpi"])


def check_file_size(
    path: Path,
    active_profile: str,
    profile: dict[str, Any],
    findings: list[Finding],
) -> None:
    size_mb = path.stat().st_size / (1024 * 1024)
    threshold = float(profile["audit"]["file_size_warn_mb"])
    if size_mb > threshold:
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "file_size",
                path,
                f"file size is {size_mb:.1f} MB; verify the target journal upload limit",
            ),
        )


def check_target_layout(
    path: Path,
    width: int,
    dpi: tuple[float, float] | None,
    artwork_type: str,
    target_layout: str,
    active_profile: str,
    profile: dict[str, Any],
    findings: list[Finding],
) -> None:
    layouts = profile["audit"]["target_layouts"]
    if target_layout == "auto":
        if dpi:
            physical_width_mm = width / dpi[0] * 25.4
            minimum_width = float(layouts["minimal"]["width_mm"])
            if physical_width_mm < minimum_width:
                add(
                    findings,
                    detector_finding(
                        profile,
                        active_profile,
                        "target_layout",
                        path,
                        f"embedded size is about {physical_width_mm:.1f} mm wide; generic minimum is {minimum_width:g} mm",
                        severity="WARN",
                    ),
                )
        return
    if target_layout == "graphical-abstract":
        return
    layout = layouts[target_layout]
    target_width_mm = float(layout["width_mm"])
    tolerance = float(profile["audit"]["layout_tolerance_fraction"])
    if dpi:
        physical_width_mm = width / dpi[0] * 25.4
        if abs(physical_width_mm - target_width_mm) <= target_width_mm * tolerance:
            return
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "target_layout",
                path,
                f"embedded width is about {physical_width_mm:.1f} mm; {target_layout} layout targets {target_width_mm:g} mm (tolerance {tolerance:.0%})",
            ),
        )
        return

    required_dpi = minimum_dpi(profile, artwork_type, "result")
    required_width = target_width_mm / 25.4 * required_dpi
    if width < required_width * (1.0 - tolerance):
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "target_layout",
                path,
                f"bitmap width is {width}px; without embedded DPI, {target_layout} layout needs about {required_width:.0f}px at {required_dpi:.0f} dpi",
            ),
        )


def check_bitmap(
    path: Path,
    figure_type: str,
    artwork_type: str,
    target_layout: str,
    active_profile: str,
    profile: dict[str, Any],
) -> list[Finding]:
    findings: list[Finding] = []
    check_file_size(path, active_profile, profile, findings)
    try:
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
            dpi = dpi_from_image(image)
            has_transparency = False
            has_alpha_channel = "A" in image.getbands()
            if has_alpha_channel:
                alpha_min, _ = image.getchannel("A").getextrema()
                has_transparency = alpha_min < 255
            elif mode == "P" and "transparency" in image.info:
                has_transparency = True
    except Exception as exc:  # noqa: BLE001 - report unreadable images without crashing the audit.
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "corrupt_bitmap",
                path,
                f"could not read bitmap metadata: {exc}",
            ),
        )
        return findings

    suffix = path.suffix.lower()
    if suffix in configured_extensions(profile, "preview_only"):
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "png_preview",
                path,
                f"{suffix.upper().lstrip('.')} is useful for preview/QA but is not a generic preferred Elsevier submission format",
            ),
        )

    graphical = profile["audit"]["target_layouts"]["graphical-abstract"]
    if figure_type == "graphical-abstract" or target_layout == "graphical-abstract":
        if width < graphical["minimum_width_px"] or height < graphical["minimum_height_px"]:
            add(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "graphical_dimensions",
                    path,
                    f"graphical abstract is {width}x{height}px; expected at least {graphical['minimum_width_px']}x{graphical['minimum_height_px']}px",
                ),
            )
        ratio = width / height if height else 0.0
        if ratio and abs(ratio - graphical["aspect_ratio"]) > graphical["aspect_tolerance"]:
            add(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "graphical_ratio",
                    path,
                    f"graphical abstract aspect ratio is {ratio:.2f}; configured guidance uses about {graphical['aspect_ratio']:.2f}",
                ),
            )
    elif min(width, height) < int(profile["audit"]["minimum_bitmap_side_warn_px"]):
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "small_bitmap",
                path,
                f"bitmap is only {width}x{height}px; verify readability at final size",
            ),
        )

    if artwork_type == "auto" and figure_type != "graphical-abstract":
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "unknown_artwork_type",
                path,
                "artwork type is auto; 500/1000 dpi requirements cannot be verified conclusively",
            ),
        )

    if dpi is None:
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "missing_dpi",
                path,
                "embedded DPI is missing; verify export resolution manually",
            ),
        )
    else:
        required_dpi = minimum_dpi(profile, artwork_type, figure_type)
        tolerance = float(profile["audit"]["dpi_tolerance"])
        x_dpi, y_dpi = dpi
        if x_dpi < required_dpi - tolerance or y_dpi < required_dpi - tolerance:
            add(
                findings,
                detector_finding(
                    profile,
                    active_profile,
                    "low_dpi",
                    path,
                    f"embedded DPI is {x_dpi:.0f}x{y_dpi:.0f}; {artwork_type} artwork requires at least {required_dpi:.0f} dpi",
                ),
            )

    check_target_layout(
        path,
        width,
        dpi,
        artwork_type,
        target_layout,
        active_profile,
        profile,
        findings,
    )

    if mode == "CMYK":
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "color_mode",
                path,
                "image mode is CMYK; the selected profile prefers RGB color artwork",
            ),
        )
    elif has_alpha_channel and not has_transparency:
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "color_mode",
                path,
                f"image mode is {mode} with an opaque alpha channel; flatten it to RGB or grayscale for a simpler submission file",
            ),
        )
    elif mode not in {"1", "L", "LA", "P", "RGB", "RGBA"}:
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "color_mode",
                path,
                f"image mode is {mode}; verify target-journal compatibility",
            ),
        )
    if has_transparency:
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "transparency",
                path,
                "image contains an alpha channel; flatten transparency unless the target journal accepts it",
            ),
        )
    return findings


def check_manual(
    path: Path,
    active_profile: str,
    profile: dict[str, Any],
) -> list[Finding]:
    findings: list[Finding] = []
    check_file_size(path, active_profile, profile, findings)
    suffix = path.suffix.lower()
    if suffix in configured_extensions(profile, "preview_only"):
        add(
            findings,
            detector_finding(
                profile,
                active_profile,
                "png_preview",
                path,
                f"{suffix.upper().lstrip('.')} is not a generic preferred Elsevier submission format; verify the target journal",
            ),
        )
    add(
        findings,
        detector_finding(
            profile,
            active_profile,
            "manual_metadata",
            path,
            f"{suffix.upper().lstrip('.')} internals are not parsed in v0.1; render and use the visual/manual audit workflow",
        ),
    )
    return findings


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
    return sorted(findings, key=lambda item: (severity_rank[item.severity], item.path, item.message))


def print_text(findings: list[Finding], summary: dict[str, Any]) -> None:
    for finding in ordered_findings(findings):
        print(f"[{finding.severity}] {finding.path} [{finding.rule_id}] - {finding.message}")
    print(
        f"[{summary['status']}] profile={summary['profile']} figure_type={summary['figure_type']} "
        f"artwork_type={summary['artwork_type']} target_layout={summary['target_layout']} "
        f"scanned_files={summary['scanned_files']} bitmap_files={summary['bitmap_files']} "
        f"manual_files={summary['manual_files']} fails={summary['fails']} warns={summary['warns']}"
    )


def print_cli_error(output_format: str, category: str, message: str) -> None:
    if output_format == "json":
        payload = {
            "summary": {"status": "FAIL", "error_type": category},
            "findings": [
                {
                    "severity": "FAIL",
                    "path": "",
                    "rule_id": category,
                    "message": message,
                }
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"[FAIL] [{category}] - {message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check exported figure metadata with a journal figure profile.")
    parser.add_argument("--path", required=True, help="Figure file or directory to scan.")
    parser.add_argument("--config", default=str(DEFAULT_PROFILE_PATH), help="Journal figure profile manifest.")
    parser.add_argument("--figure-type", choices=("schematic", "result", "graphical-abstract"), default="result")
    parser.add_argument("--artwork-type", choices=("auto", "line", "combination", "halftone"), default="auto")
    parser.add_argument("--target-layout", default="auto", help="auto or a target layout from the manifest.")
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
        layouts = {"auto", *profile["audit"]["target_layouts"].keys()}
        if args.target_layout not in layouts:
            raise ProfileError(f"unknown target layout {args.target_layout!r}; expected one of {sorted(layouts)}")
    except ProfileError as exc:
        print_cli_error(args.output_format, "CONFIG", str(exc))
        return 2

    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        print_cli_error(args.output_format, "INPUT", f"path does not exist: {target.as_posix()}")
        return 2
    files = iter_figure_files(target, profile)
    if not files:
        print_cli_error(args.output_format, "INPUT", f"no supported figure exports found: {target.as_posix()}")
        return 2

    findings: list[Finding] = []
    bitmap_count = 0
    manual_count = 0
    bitmap_extensions = configured_extensions(profile, "bitmap")
    for file in files:
        if file.suffix.lower() in bitmap_extensions:
            bitmap_count += 1
            findings.extend(
                check_bitmap(
                    file,
                    args.figure_type,
                    args.artwork_type,
                    args.target_layout,
                    active_profile,
                    profile,
                )
            )
        else:
            manual_count += 1
            findings.extend(check_manual(file, active_profile, profile))

    summary = {
        "status": status_for(findings),
        "profile": active_profile,
        "profile_id": profile["identity"]["id"],
        "figure_type": args.figure_type,
        "artwork_type": args.artwork_type,
        "target_layout": args.target_layout,
        "scanned_files": len(files),
        "bitmap_files": bitmap_count,
        "manual_files": manual_count,
        "fails": sum(item.severity == "FAIL" for item in findings),
        "warns": sum(item.severity == "WARN" for item in findings),
    }
    if args.output_format == "json":
        print(json.dumps({"summary": summary, "findings": [asdict(item) for item in ordered_findings(findings)]}, indent=2))
    else:
        print_text(findings, summary)
    return 1 if should_fail(findings, fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
