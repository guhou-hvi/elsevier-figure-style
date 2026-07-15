from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


MINIMUM_PYTHON = (3, 10)
REQUIREMENTS_PATH = Path(__file__).resolve().parent.parent / "requirements.txt"
RUNTIME_MODULES = {
    "matplotlib": ("matplotlib", "3.7"),
    "numpy": ("numpy", "1.24"),
    "PIL": ("Pillow", "10"),
    "jsonschema": ("jsonschema", "4.18"),
}


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value)
    return tuple(int(part) for part in parts[:4])


def environment_report() -> dict[str, Any]:
    missing: list[str] = []
    outdated: dict[str, dict[str, str]] = {}
    versions: dict[str, str] = {}
    for module_name, (distribution_name, minimum_version) in RUNTIME_MODULES.items():
        if importlib.util.find_spec(module_name) is None:
            missing.append(distribution_name)
            continue
        try:
            installed_version = importlib.metadata.version(distribution_name)
            versions[distribution_name] = installed_version
            if _version_tuple(installed_version) < _version_tuple(minimum_version):
                outdated[distribution_name] = {
                    "installed": installed_version,
                    "minimum": minimum_version,
                }
        except importlib.metadata.PackageNotFoundError:
            versions[distribution_name] = "available"

    python_ok = sys.version_info >= MINIMUM_PYTHON
    requirements_ok = REQUIREMENTS_PATH.is_file()
    status = "PASS" if python_ok and requirements_ok and not missing and not outdated else "FAIL"
    return {
        "status": status,
        "python": {
            "version": ".".join(str(part) for part in sys.version_info[:3]),
            "minimum": ".".join(str(part) for part in MINIMUM_PYTHON),
            "ok": python_ok,
        },
        "requirements_path": REQUIREMENTS_PATH.as_posix(),
        "requirements_file_found": requirements_ok,
        "installed": versions,
        "missing": sorted(missing),
        "outdated": outdated,
        "install_command": f'"{sys.executable}" -m pip install -r "{REQUIREMENTS_PATH}"',
    }


def print_text(report: dict[str, Any]) -> None:
    python = report["python"]
    print(
        f"[{report['status']}] Python {python['version']} "
        f"(minimum {python['minimum']}); requirements={report['requirements_path']}"
    )
    for name, version in sorted(report["installed"].items()):
        print(f"[PASS] {name} {version}")
    for name in report["missing"]:
        print(f"[FAIL] missing Python distribution: {name}")
    for name, versions in sorted(report["outdated"].items()):
        print(f"[FAIL] {name} {versions['installed']} is below required {versions['minimum']}")
    if not report["requirements_file_found"]:
        print("[FAIL] bundled requirements.txt is missing")
    if not python["ok"]:
        print(f"[FAIL] Python {python['minimum']} or newer is required")
    if report["status"] == "FAIL":
        print(f"Install command: {report['install_command']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the Python runtime required by elsevier-figure-style.")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    args = parser.parse_args()
    report = environment_report()
    if args.output_format == "json":
        print(json.dumps(report, indent=2))
    else:
        print_text(report)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
