from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import init_figure_style_project as initializer
from elsevier_plot_style import load_profile
from init_figure_style_project import initialize_project


def test_initializer_creates_importable_bundle(tmp_path: Path, profile_path: Path) -> None:
    output = initialize_project(tmp_path, profile_path)
    assert (output / "profile.json").is_file()
    assert (output / "requirements.txt").is_file()
    assert (output / "references/source-basis/rule-registry.md").is_file()
    assert load_profile(output / "profile.json")["bundle_root"] == "."
    result = subprocess.run(
        [sys.executable, "-c", "from figure_style import apply_journal_style; print(apply_journal_style()['font']['size'])"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "11.0"


def test_initializer_refuses_overwrite_and_supports_dry_run(tmp_path: Path, profile_path: Path) -> None:
    output = initialize_project(tmp_path, profile_path)
    with pytest.raises(FileExistsError):
        initialize_project(tmp_path, profile_path)
    initialize_project(tmp_path, profile_path, force=True)
    assert output.is_dir()

    dry_target = tmp_path / "dry"
    initialize_project(dry_target, profile_path, dry_run=True)
    assert not (dry_target / "figure_style").exists()


def test_force_keeps_existing_bundle_when_staging_fails(
    tmp_path: Path,
    profile_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = initialize_project(tmp_path, profile_path)
    marker = output / "keep.txt"
    marker.write_text("original", encoding="utf-8")

    def fail_copy(staging_dir: Path, *args, **kwargs) -> None:
        (staging_dir / "partial.txt").write_text("partial", encoding="utf-8")
        raise OSError("synthetic copy failure")

    monkeypatch.setattr(initializer, "_copy_bundle", fail_copy)
    with pytest.raises(OSError, match="synthetic copy failure"):
        initializer.initialize_project(tmp_path, profile_path, force=True)

    assert marker.read_text(encoding="utf-8") == "original"
    assert not list(tmp_path.glob(".figure_style-staging-*"))
    assert not list(tmp_path.glob(".figure_style-backup-*"))


def test_force_restores_existing_bundle_when_final_rename_fails(
    tmp_path: Path,
    profile_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = initialize_project(tmp_path, profile_path)
    marker = output / "keep.txt"
    marker.write_text("original", encoding="utf-8")
    original_rename = Path.rename

    def fail_staging_rename(self: Path, target: Path):
        if self.name.startswith(".figure_style-staging-") and Path(target).name == "figure_style":
            raise OSError("synthetic final rename failure")
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", fail_staging_rename)
    with pytest.raises(OSError, match="synthetic final rename failure"):
        initialize_project(tmp_path, profile_path, force=True)

    assert marker.read_text(encoding="utf-8") == "original"
    assert not list(tmp_path.glob(".figure_style-staging-*"))
    assert not list(tmp_path.glob(".figure_style-backup-*"))


def test_resource_destination_collisions_fail(skill: Path, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(skill, bundle)
    first = bundle / "references" / "first" / "common.md"
    second = bundle / "references" / "second" / "common.md"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")

    manifest = bundle / "assets" / "elsevier_figure_style.json"
    profile_data = json.loads(manifest.read_text(encoding="utf-8"))
    profile_data["resources"]["first"] = "../references/first/common.md"
    profile_data["resources"]["second"] = "../references/second/common.md"
    manifest.write_text(json.dumps(profile_data), encoding="utf-8")

    profile = load_profile(manifest)
    with pytest.raises(initializer.ProfileError, match="collide"):
        initializer.plan_resources(profile, manifest)


def test_target_inside_resource_directory_is_rejected(skill: Path, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(skill, bundle)
    manifest = bundle / "assets" / "elsevier_figure_style.json"
    profile_data = json.loads(manifest.read_text(encoding="utf-8"))
    profile_data["resources"]["source_basis"] = ".."
    manifest.write_text(json.dumps(profile_data), encoding="utf-8")

    with pytest.raises(initializer.ProfileError, match="inside profile resource"):
        initialize_project(bundle, manifest)
