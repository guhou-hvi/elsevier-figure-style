from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from elsevier_plot_style import DEFAULT_PROFILE_PATH, ProfileError, load_profile, resolve_profile_resource


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR_NAME = "figure_style"


def _relative_to(path: Path, parent: Path) -> Path | None:
    try:
        return path.relative_to(parent)
    except ValueError:
        return None


def plan_resources(
    profile: dict[str, Any],
    config_path: Path,
) -> tuple[dict[str, str], list[tuple[Path, Path]]]:
    """Return rewritten resource paths and unique source/destination copies."""
    resolved = {
        name: resolve_profile_resource(profile, name, config_path=config_path)
        for name in profile["resources"]
    }
    directory_mappings: dict[Path, Path] = {}
    copies: dict[Path, Path] = {}
    destinations: dict[Path, Path] = {}

    def register_copy(source: Path, destination: Path) -> None:
        existing = destinations.get(destination)
        if existing is not None and existing != source:
            raise ProfileError(
                f"profile resources collide at {destination.as_posix()}: {existing} and {source}"
            )
        destinations[destination] = source
        copies[source] = destination

    for name, source in resolved.items():
        if source.is_dir():
            destination = Path("references") / source.name
            directory_mappings[source] = destination
            register_copy(source, destination)

    rewritten: dict[str, str] = {}
    for name, source in resolved.items():
        mapped_destination: Path | None = None
        for source_dir, destination_dir in directory_mappings.items():
            relative = _relative_to(source, source_dir)
            if relative is not None:
                mapped_destination = destination_dir / relative
                break
        if mapped_destination is None:
            mapped_destination = Path("references") / source.name
            register_copy(source, mapped_destination)
        rewritten[name] = mapped_destination.as_posix()
    return rewritten, sorted(copies.items(), key=lambda item: item[1].as_posix())


def _copy_bundle(
    staging_dir: Path,
    profile: dict[str, Any],
    config_path: Path,
    rewritten_resources: dict[str, str],
    resource_copies: list[tuple[Path, Path]],
) -> None:
    schema_path = (config_path.parent / profile["$schema"]).resolve()
    planned = [
        (SCRIPT_DIR / "elsevier_plot_style.py", Path("plot_style.py")),
        (SCRIPT_DIR / "elsevier_theme.R", Path("elsevier_theme.R")),
        (SCRIPT_DIR.parent / "requirements.txt", Path("requirements.txt")),
        (schema_path, Path("journal_figure_profile.schema.json")),
    ]
    planned.extend(resource_copies)

    for source, relative_destination in planned:
        destination = staging_dir / relative_destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

    vendored_profile = dict(profile)
    vendored_profile["$schema"] = "./journal_figure_profile.schema.json"
    vendored_profile["bundle_root"] = "."
    vendored_profile["resources"] = rewritten_resources
    (staging_dir / "profile.json").write_text(
        json.dumps(vendored_profile, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (staging_dir / "__init__.py").write_text(
        '"""Project-local journal figure style helpers."""\n\nfrom .plot_style import *  # noqa: F401,F403\n',
        encoding="utf-8",
    )
    load_profile(staging_dir / "profile.json")


def initialize_project(
    target: Path,
    config_path: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> Path:
    profile = load_profile(config_path)
    target_root = target.expanduser().resolve()
    output_dir = target_root / OUTPUT_DIR_NAME
    if output_dir.parent != target_root or output_dir.name != OUTPUT_DIR_NAME:
        raise ProfileError(f"unsafe output directory: {output_dir}")
    if output_dir.is_symlink():
        raise ProfileError(f"refusing to replace symlinked output directory: {output_dir}")
    if output_dir.exists() and not output_dir.is_dir():
        raise ProfileError(f"output path exists and is not a directory: {output_dir}")
    if output_dir.exists() and not force:
        raise FileExistsError(f"{output_dir} already exists; use --force to replace it")

    rewritten_resources, resource_copies = plan_resources(profile, config_path)
    for source, _ in resource_copies:
        if source.is_dir() and target_root.is_relative_to(source):
            raise ProfileError(
                f"target project is inside profile resource directory and cannot be copied safely: {source}"
            )

    if dry_run:
        print(f"Would create {output_dir}")
        planned = [
            (SCRIPT_DIR / "elsevier_plot_style.py", Path("plot_style.py")),
            (SCRIPT_DIR / "elsevier_theme.R", Path("elsevier_theme.R")),
            (SCRIPT_DIR.parent / "requirements.txt", Path("requirements.txt")),
            ((config_path.parent / profile["$schema"]).resolve(), Path("journal_figure_profile.schema.json")),
            *resource_copies,
        ]
        for source, destination in planned:
            print(f"  {source} -> {output_dir / destination}")
        print(f"  {config_path} -> {output_dir / 'profile.json'}")
        return output_dir

    target_root.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=".figure_style-staging-", dir=target_root))
    backup_dir: Path | None = None
    try:
        _copy_bundle(staging_dir, profile, config_path, rewritten_resources, resource_copies)
        if output_dir.exists():
            backup_dir = target_root / f".figure_style-backup-{uuid.uuid4().hex}"
            output_dir.rename(backup_dir)
        try:
            staging_dir.rename(output_dir)
        except Exception:
            if backup_dir is not None and backup_dir.exists() and not output_dir.exists():
                backup_dir.rename(output_dir)
            raise
        if backup_dir is not None:
            shutil.rmtree(backup_dir, ignore_errors=True)
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)

    print(f"Initialized project-local figure style at {output_dir}")
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Vendor a journal figure profile into a project.")
    parser.add_argument("--target", required=True, help="Project root that will receive figure_style/.")
    parser.add_argument("--config", default=str(DEFAULT_PROFILE_PATH), help="Journal figure profile manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned files without writing them.")
    parser.add_argument("--force", action="store_true", help="Replace an existing figure_style directory.")
    args = parser.parse_args()
    try:
        initialize_project(
            Path(args.target),
            Path(args.config).expanduser().resolve(),
            dry_run=args.dry_run,
            force=args.force,
        )
    except (FileExistsError, OSError, ProfileError) as exc:
        print(f"[FAIL] {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
