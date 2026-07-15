from __future__ import annotations

import copy
import json
import re
import shutil
from pathlib import Path

import pytest

from elsevier_plot_style import ProfileError, load_profile, resolve_profile_resource, validate_profile


def test_default_profile_and_resources_are_valid(profile_path: Path) -> None:
    profile = load_profile(profile_path)
    assert profile["schema_version"] == 1
    assert profile["identity"]["version"] == "0.1.0"
    assert profile["profiles"]["default"] == "editor"
    assert profile["profiles"]["order"] == ["official", "editor", "strict"]
    for resource_name in profile["resources"]:
        assert resolve_profile_resource(profile, resource_name, config_path=profile_path).exists()


def test_detector_rule_ids_exist_in_registry(profile_path: Path) -> None:
    profile = load_profile(profile_path)
    registry = resolve_profile_resource(profile, "rule_registry", config_path=profile_path).read_text(encoding="utf-8")
    defined = set(re.findall(r"^\| ([A-Z]+-[A-Z0-9-]+) \|", registry, re.MULTILINE))
    configured = {item["rule_id"] for item in profile["audit"]["detectors"].values()}
    assert configured <= defined


def test_invalid_profile_gate_fails(profile_path: Path) -> None:
    profile = load_profile(profile_path)
    profile["audit"]["detectors"]["style_integration"]["minimum_profile"] = "missing"
    with pytest.raises(ProfileError, match="minimum_profile"):
        validate_profile(profile, config_path=profile_path)


def test_missing_resource_fails(profile_path: Path) -> None:
    profile = load_profile(profile_path)
    profile["resources"]["rule_registry"] = "missing.md"
    with pytest.raises(ProfileError, match="not found"):
        validate_profile(profile, config_path=profile_path)


def test_missing_style_field_fails_clearly(profile_path: Path) -> None:
    profile = load_profile(profile_path)
    del profile["style"]["font"]["size"]
    with pytest.raises(ProfileError, match="font.size"):
        validate_profile(profile, config_path=profile_path)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda profile: profile["style"]["line"].__setitem__("marker_size", -1), "marker_size"),
        (lambda profile: profile["style"]["heatmap"].__setitem__("cmap", 42), "cmap"),
        (lambda profile: profile["audit"]["target_layouts"].__setitem__("minimal", {}), "width_mm"),
        (lambda profile: profile["audit"]["detectors"]["font_official"].pop("threshold"), "threshold"),
        (lambda profile: profile["audit"]["detectors"].pop("manual_rcparams"), "manual_rcparams"),
        (lambda profile: profile["profiles"].__setitem__("default", "official"), "profiles.default"),
    ],
)
def test_invalid_manifest_values_fail_during_validation(
    profile_path: Path,
    mutation,
    message: str,
) -> None:
    profile = copy.deepcopy(load_profile(profile_path))
    mutation(profile)
    with pytest.raises(ProfileError, match=message):
        validate_profile(profile, config_path=profile_path)


def test_duplicate_dpi_and_graphical_fields_must_match(profile_path: Path) -> None:
    profile = load_profile(profile_path)
    profile["style"]["figure"]["line_art_dpi"] = 900
    with pytest.raises(ProfileError, match="line_art_dpi"):
        validate_profile(profile, config_path=profile_path)

    profile = load_profile(profile_path)
    profile["style"]["graphical_abstract"]["minimum_width_px"] = 1200
    with pytest.raises(ProfileError, match="minimum_width_px"):
        validate_profile(profile, config_path=profile_path)

    profile = load_profile(profile_path)
    profile["style"]["figure"]["single_column_width_in"] = 4.0
    with pytest.raises(ProfileError, match="single_column_width_in"):
        validate_profile(profile, config_path=profile_path)


def test_absolute_and_escaping_resource_paths_are_rejected(profile_path: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("synthetic", encoding="utf-8")

    profile = load_profile(profile_path)
    profile["resources"]["rule_registry"] = str(outside.resolve())
    with pytest.raises(ProfileError, match="must be relative"):
        validate_profile(profile, config_path=profile_path)

    profile = load_profile(profile_path)
    profile["resources"]["rule_registry"] = "../../../outside.md"
    with pytest.raises(ProfileError, match="escapes bundle_root"):
        validate_profile(profile, config_path=profile_path)

    profile = load_profile(profile_path)
    profile["bundle_root"] = "../.."
    with pytest.raises(ProfileError, match="bundle_root"):
        validate_profile(profile, config_path=profile_path)


def test_symlink_escape_is_rejected(skill: Path, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(skill, bundle)
    outside = tmp_path / "outside.md"
    outside.write_text("synthetic", encoding="utf-8")
    link = bundle / "references" / "outside-link.md"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is not available in this environment")

    manifest = bundle / "assets" / "elsevier_figure_style.json"
    profile = json.loads(manifest.read_text(encoding="utf-8"))
    profile["resources"]["rule_registry"] = "../references/outside-link.md"
    manifest.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(ProfileError, match="escapes bundle_root"):
        load_profile(manifest)


def test_manifest_cannot_replace_runtime_schema_with_permissive_schema(skill: Path, tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(skill, bundle)
    manifest = bundle / "assets" / "elsevier_figure_style.json"
    profile = json.loads(manifest.read_text(encoding="utf-8"))
    profile["style"]["line"]["marker_size"] = -1
    manifest.write_text(json.dumps(profile), encoding="utf-8")
    (bundle / "assets" / "journal_figure_profile.schema.json").write_text(
        json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"}),
        encoding="utf-8",
    )

    with pytest.raises(ProfileError, match="marker_size"):
        load_profile(manifest)
