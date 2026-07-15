from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Sequence

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator


MODULE_DIR = Path(__file__).resolve().parent
SKILL_PROFILE_PATH = MODULE_DIR.parent / "assets" / "elsevier_figure_style.json"
VENDORED_PROFILE_PATH = MODULE_DIR / "profile.json"
DEFAULT_PROFILE_PATH = VENDORED_PROFILE_PATH if VENDORED_PROFILE_PATH.exists() else SKILL_PROFILE_PATH
SKILL_SCHEMA_PATH = MODULE_DIR.parent / "assets" / "journal_figure_profile.schema.json"
VENDORED_SCHEMA_PATH = MODULE_DIR / "journal_figure_profile.schema.json"
DEFAULT_SCHEMA_PATH = VENDORED_SCHEMA_PATH if VENDORED_SCHEMA_PATH.exists() else SKILL_SCHEMA_PATH
STYLE_PATH = DEFAULT_PROFILE_PATH


class ProfileError(ValueError):
    """Raised when a journal figure profile is invalid or incomplete."""


REQUIRED_STYLE_PATHS = (
    "font.family",
    "font.sans_serif",
    "font.mathtext_fontset",
    "font.mathtext_default",
    "font.size",
    "font.title_size",
    "font.label_size",
    "font.tick_size",
    "font.legend_size",
    "figure.dpi",
    "figure.save_dpi",
    "figure.halftone_dpi",
    "figure.combination_dpi",
    "figure.line_art_dpi",
    "figure.facecolor",
    "figure.save_bbox",
    "figure.pad_inches",
    "figure.default_layout",
    "figure.default_aspect_ratio",
    "figure.single_column_width_in",
    "figure.one_half_column_width_in",
    "figure.double_column_width_in",
    "graphical_abstract.target_width_cm",
    "graphical_abstract.target_height_cm",
    "axes.facecolor",
    "axes.edgecolor",
    "axes.labelcolor",
    "axes.linewidth",
    "axes.titlepad",
    "axes.show_title",
    "ticks.color",
    "ticks.major_size",
    "ticks.major_width",
    "ticks.minor_visible",
    "ticks.major_n_locator.default",
    "grid.visible",
    "grid.color",
    "grid.alpha",
    "grid.linestyle",
    "grid.linewidth",
    "legend.frameon",
    "line.linewidth",
    "line.marker_size",
    "line.fill_alpha",
    "line.errorbar_capsize",
    "bar.width",
    "bar.height",
    "bar.alpha",
    "bar.edgecolor",
    "bar.linewidth",
    "scatter.size",
    "scatter.alpha",
    "scatter.edgecolor",
    "scatter.linewidth",
    "heatmap.cmap",
    "heatmap.interpolation",
    "heatmap.aspect",
    "annotation.fontsize",
    "annotation.panel_label_fontsize",
    "annotation.panel_label_fontweight",
    "annotation.color",
    "colorbar.fraction",
    "colorbar.pad",
    "colorbar.label_size",
    "colorbar.tick_size",
    "markers.cycle",
    "markers.series",
    "palette.cycle",
    "palette.series",
)


def _profile_path(config_path: str | Path | None = None) -> Path:
    return (Path(config_path) if config_path else DEFAULT_PROFILE_PATH).expanduser().resolve()


def _looks_absolute(path_value: str) -> bool:
    return (
        Path(path_value).is_absolute()
        or PurePosixPath(path_value).is_absolute()
        or PureWindowsPath(path_value).is_absolute()
    )


def _profile_bundle_root(profile: dict[str, Any], config_path: Path) -> Path:
    raw_root = profile.get("bundle_root")
    if not isinstance(raw_root, str) or not raw_root:
        raise ProfileError("profile must define a non-empty relative bundle_root")
    if _looks_absolute(raw_root):
        raise ProfileError("profile bundle_root must be relative to the manifest")
    if raw_root not in {".", ".."}:
        raise ProfileError("profile bundle_root must be '.' or '..'")
    bundle_root = (config_path.parent / raw_root).resolve()
    if not bundle_root.is_dir():
        raise ProfileError(f"profile bundle_root is not a directory: {bundle_root}")
    return bundle_root


def _resolve_bundle_member(
    profile: dict[str, Any],
    config_path: Path,
    raw_path: str,
    *,
    label: str,
) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise ProfileError(f"{label} must be a non-empty relative path")
    if _looks_absolute(raw_path):
        raise ProfileError(f"{label} must be relative to the manifest: {raw_path}")
    bundle_root = _profile_bundle_root(profile, config_path)
    resolved = (config_path.parent / raw_path).resolve()
    if not resolved.is_relative_to(bundle_root):
        raise ProfileError(f"{label} escapes bundle_root {bundle_root}: {resolved}")
    return resolved


def _validate_symlink_boundaries(path: Path, bundle_root: Path, *, label: str) -> None:
    candidates = [path]
    if path.is_dir():
        candidates.extend(path.rglob("*"))
    for candidate in candidates:
        if not candidate.is_symlink():
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise ProfileError(f"{label} contains a broken symlink: {candidate}") from exc
        if not resolved.is_relative_to(bundle_root):
            raise ProfileError(f"{label} contains a symlink that escapes bundle_root: {candidate} -> {resolved}")


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ProfileError(f"{label} not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProfileError(f"could not read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProfileError(f"{label} must contain a JSON object: {path}")
    return value


def resolve_profile_resource(
    profile: dict[str, Any],
    resource_name: str,
    *,
    config_path: str | Path | None = None,
) -> Path:
    """Resolve a manifest resource relative to the manifest location."""
    resources = profile.get("resources", {})
    if resource_name not in resources:
        raise ProfileError(f"profile does not define resource {resource_name!r}")
    path = _profile_path(config_path)
    return _resolve_bundle_member(
        profile,
        path,
        resources[resource_name],
        label=f"profile resource {resource_name!r}",
    )


def validate_profile(
    profile: dict[str, Any],
    *,
    config_path: str | Path | None = None,
    validate_resources: bool = True,
) -> None:
    """Validate schema, profile ordering, detector gates, and resource paths."""
    path = _profile_path(config_path)
    bundle_root = _profile_bundle_root(profile, path)
    schema_ref = profile.get("$schema")
    if not isinstance(schema_ref, str) or not schema_ref:
        raise ProfileError("profile must define a local $schema path")
    if "://" in schema_ref:
        raise ProfileError("remote profile schemas are not loaded at runtime; use a local $schema path")
    schema_path = _resolve_bundle_member(profile, path, schema_ref, label="profile schema")
    _load_json(schema_path, label="profile schema")
    schema = _load_json(DEFAULT_SCHEMA_PATH.resolve(), label="runtime profile schema")
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ProfileError("jsonschema is required to validate journal figure profiles") from exc

    errors = sorted(Draft202012Validator(schema).iter_errors(profile), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        path_parts = [str(part) for part in first.path]
        if first.validator == "required":
            missing = str(first.message).split("'", 2)
            if len(missing) >= 2:
                path_parts.append(missing[1])
        location = ".".join(path_parts) or "<root>"
        raise ProfileError(f"invalid profile at {location}: {first.message}")

    profiles = profile["profiles"]
    order = profiles["order"]
    definitions = profiles["definitions"]
    if profiles["default"] not in order:
        raise ProfileError("profiles.default must appear in profiles.order")
    if set(order) != set(definitions):
        raise ProfileError("profiles.order and profiles.definitions must contain the same profile names")
    for detector_name, detector in profile["audit"]["detectors"].items():
        if detector["minimum_profile"] not in order:
            raise ProfileError(
                f"detector {detector_name!r} references unknown profile {detector['minimum_profile']!r}"
            )

    style = profile["style"]
    for dotted_path in REQUIRED_STYLE_PATHS:
        current: Any = style
        for key in dotted_path.split("."):
            if not isinstance(current, dict) or key not in current:
                raise ProfileError(f"profile style is missing required field {dotted_path!r}")
            current = current[key]
    if not style["palette"]["cycle"] or not style["markers"]["cycle"]:
        raise ProfileError("palette.cycle and markers.cycle must not be empty")
    positive_fields = (
        style["font"]["size"],
        style["figure"]["save_dpi"],
        style["figure"]["single_column_width_in"],
        style["line"]["linewidth"],
        style["bar"]["width"],
        style["scatter"]["size"],
    )
    if any(not isinstance(value, (int, float)) or value <= 0 for value in positive_fields):
        raise ProfileError("profile style size, DPI, width, and marker values must be positive numbers")

    locator = style["ticks"]["major_n_locator"]
    if not locator["min"] <= locator["default"] <= locator["max"]:
        raise ProfileError("ticks.major_n_locator must satisfy min <= default <= max")

    dpi_pairs = {
        "halftone": "halftone_dpi",
        "combination": "combination_dpi",
        "line": "line_art_dpi",
    }
    for artwork_type, style_key in dpi_pairs.items():
        audit_dpi = float(profile["audit"]["artwork_types"][artwork_type]["minimum_dpi"])
        export_dpi = float(style["figure"][style_key])
        if audit_dpi != export_dpi:
            raise ProfileError(
                f"style.figure.{style_key} ({export_dpi:g}) must match "
                f"audit.artwork_types.{artwork_type}.minimum_dpi ({audit_dpi:g})"
            )
    if float(style["figure"]["save_dpi"]) < max(
        float(item["minimum_dpi"]) for item in profile["audit"]["artwork_types"].values()
    ):
        raise ProfileError("style.figure.save_dpi must be at least the largest artwork minimum DPI")

    width_pairs = {
        "single": "single_column_width_in",
        "one-half": "one_half_column_width_in",
        "double": "double_column_width_in",
    }
    for layout_name, style_key in width_pairs.items():
        audit_width = float(profile["audit"]["target_layouts"][layout_name]["width_mm"])
        style_width = float(style["figure"][style_key]) * 25.4
        if abs(audit_width - style_width) > 0.2:
            raise ProfileError(
                f"style.figure.{style_key} ({style_width:.2f} mm) must match "
                f"audit.target_layouts.{layout_name}.width_mm ({audit_width:g} mm)"
            )

    official_font = float(profile["audit"]["detectors"]["font_official"]["threshold"])
    editor_font = float(profile["audit"]["detectors"]["font_editor"]["threshold"])
    if editor_font < official_font:
        raise ProfileError("font_editor.threshold must be greater than or equal to font_official.threshold")

    audit_graphical = profile["audit"]["target_layouts"]["graphical-abstract"]
    style_graphical = style["graphical_abstract"]
    graphical_pairs = {
        "minimum_width_px": "minimum_width_px",
        "minimum_height_px": "minimum_height_px",
        "minimum_dpi": "minimum_resolution_dpi",
    }
    for audit_key, style_key in graphical_pairs.items():
        if float(audit_graphical[audit_key]) != float(style_graphical[style_key]):
            raise ProfileError(
                f"style.graphical_abstract.{style_key} must match "
                f"audit.target_layouts.graphical-abstract.{audit_key}"
            )

    if validate_resources:
        for resource_name in profile["resources"]:
            resource_path = resolve_profile_resource(profile, resource_name, config_path=path)
            if not resource_path.exists():
                raise ProfileError(f"profile resource {resource_name!r} not found: {resource_path}")
            _validate_symlink_boundaries(
                resource_path,
                bundle_root,
                label=f"profile resource {resource_name!r}",
            )


def load_profile(
    config_path: str | Path | None = None,
    *,
    validate_resources: bool = True,
) -> dict[str, Any]:
    """Load and validate a versioned journal figure profile manifest."""
    path = _profile_path(config_path)
    profile = _load_json(path, label="figure profile")
    validate_profile(profile, config_path=path, validate_resources=validate_resources)
    return profile


def load_style(style_path: str | Path | None = None) -> dict[str, Any]:
    """Load the style section from a journal figure profile."""
    return load_profile(style_path)["style"]


def _style(spec: dict[str, Any] | None = None) -> dict[str, Any]:
    if spec is None:
        return load_style()
    if "style" in spec and "identity" in spec:
        return spec["style"]
    return spec


def _series_color(series: str, spec: dict[str, Any], index: int = 0) -> str:
    palette = spec["palette"]
    cycle = palette["cycle"]
    return palette["series"].get(series, cycle[index % len(cycle)])


def _series_marker(series: str, spec: dict[str, Any], index: int = 0) -> str:
    markers = spec["markers"]
    cycle = markers["cycle"]
    return markers["series"].get(series, cycle[index % len(cycle)])


def apply_journal_style(config_path: str | Path | None = None) -> dict[str, Any]:
    """Apply rcParams from a journal profile and return its style section."""
    spec = load_style(config_path)
    font = spec["font"]
    figure = spec["figure"]
    axes = spec["axes"]
    ticks = spec["ticks"]
    legend = spec["legend"]
    plt.rcParams.update(
        {
            "figure.dpi": figure["dpi"],
            "savefig.dpi": figure["save_dpi"],
            "figure.facecolor": figure["facecolor"],
            "savefig.facecolor": figure["facecolor"],
            "savefig.bbox": None if figure["save_bbox"] == "standard" else figure["save_bbox"],
            "savefig.pad_inches": figure["pad_inches"],
            "axes.facecolor": axes["facecolor"],
            "axes.edgecolor": axes["edgecolor"],
            "axes.labelcolor": axes["labelcolor"],
            "axes.linewidth": axes["linewidth"],
            "axes.labelsize": font["label_size"],
            "axes.titlesize": font["title_size"],
            "axes.titlepad": axes["titlepad"],
            "xtick.color": ticks["color"],
            "ytick.color": ticks["color"],
            "xtick.labelsize": font["tick_size"],
            "ytick.labelsize": font["tick_size"],
            "xtick.major.size": ticks["major_size"],
            "ytick.major.size": ticks["major_size"],
            "xtick.major.width": ticks["major_width"],
            "ytick.major.width": ticks["major_width"],
            "font.family": font["family"],
            "font.sans-serif": font["sans_serif"],
            "font.size": font["size"],
            "mathtext.fontset": font["mathtext_fontset"],
            "mathtext.default": font["mathtext_default"],
            "legend.fontsize": font["legend_size"],
            "legend.frameon": legend["frameon"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    return spec


def apply_elsevier_style(style_path: str | Path | None = None) -> dict[str, Any]:
    """Compatibility alias for the default Elsevier profile."""
    return apply_journal_style(style_path)


def figure_width(column: str | None = None, spec: dict[str, Any] | None = None) -> float:
    """Return a configured figure width in inches."""
    figure = _style(spec)["figure"]
    if column is None:
        column = figure["default_layout"]
    aliases = {
        "single": "single_column_width_in",
        "one-half": "one_half_column_width_in",
        "one_half": "one_half_column_width_in",
        "1.5": "one_half_column_width_in",
        "double": "double_column_width_in",
    }
    if column not in aliases:
        raise ValueError(f"unknown column layout {column!r}; expected one of {sorted(aliases)}")
    return float(figure[aliases[column]])


def figure_size(
    column: str | None = None,
    spec: dict[str, Any] | None = None,
    *,
    aspect_ratio: float | None = None,
) -> tuple[float, float]:
    """Return an exact profile-backed canvas size in inches."""
    figure = _style(spec)["figure"]
    width = figure_width(column, spec)
    ratio = float(figure["default_aspect_ratio"] if aspect_ratio is None else aspect_ratio)
    if ratio <= 0:
        raise ValueError("aspect_ratio must be positive")
    return width, width / ratio


def graphical_abstract_size(spec: dict[str, Any] | None = None) -> tuple[float, float]:
    """Return the configured graphical-abstract size in inches."""
    graphical = _style(spec)["graphical_abstract"]
    return float(graphical["target_width_cm"]) / 2.54, float(graphical["target_height_cm"]) / 2.54


def line_style_kwargs(
    series: str,
    *,
    spec: dict[str, Any] | None = None,
    index: int = 0,
    marker: str | None = None,
    linewidth: float | None = None,
    linestyle: str = "-",
) -> dict[str, Any]:
    spec = _style(spec)
    return {
        "color": _series_color(series, spec, index),
        "linewidth": spec["line"]["linewidth"] if linewidth is None else linewidth,
        "marker": _series_marker(series, spec, index) if marker is None else marker,
        "markersize": spec["line"]["marker_size"],
        "linestyle": linestyle,
    }


def band_style_kwargs(
    series: str,
    *,
    spec: dict[str, Any] | None = None,
    index: int = 0,
) -> dict[str, Any]:
    """Return fill_between kwargs for uncertainty bands."""
    spec = _style(spec)
    return {
        "color": _series_color(series, spec, index),
        "alpha": spec["line"]["fill_alpha"],
        "linewidth": 0,
    }


def bar_style_kwargs(
    series: str,
    *,
    spec: dict[str, Any] | None = None,
    index: int = 0,
    orientation: str = "vertical",
    alpha: float | None = None,
) -> dict[str, Any]:
    spec = _style(spec)
    if orientation not in {"vertical", "horizontal"}:
        raise ValueError("orientation must be 'vertical' or 'horizontal'")
    bar = spec["bar"]
    kwargs: dict[str, Any] = {
        "color": _series_color(series, spec, index),
        "edgecolor": bar["edgecolor"],
        "linewidth": bar["linewidth"],
        "alpha": bar["alpha"] if alpha is None else alpha,
    }
    kwargs["height" if orientation == "horizontal" else "width"] = bar[
        "height" if orientation == "horizontal" else "width"
    ]
    return kwargs


def scatter_style_kwargs(
    series: str,
    *,
    spec: dict[str, Any] | None = None,
    index: int = 0,
    marker: str | None = None,
    size: float | None = None,
) -> dict[str, Any]:
    spec = _style(spec)
    scatter = spec["scatter"]
    return {
        "color": _series_color(series, spec, index),
        "s": scatter["size"] if size is None else size,
        "alpha": scatter["alpha"],
        "edgecolors": scatter["edgecolor"],
        "linewidths": scatter["linewidth"],
        "marker": _series_marker(series, spec, index) if marker is None else marker,
    }


def heatmap_kwargs(
    spec: dict[str, Any] | None = None,
    *,
    cmap: str | None = None,
) -> dict[str, Any]:
    heatmap = _style(spec)["heatmap"]
    return {
        "cmap": cmap or heatmap["cmap"],
        "interpolation": heatmap["interpolation"],
        "aspect": heatmap["aspect"],
    }


def colorbar_kwargs(spec: dict[str, Any] | None = None) -> dict[str, Any]:
    colorbar = _style(spec)["colorbar"]
    return {"fraction": colorbar["fraction"], "pad": colorbar["pad"]}


def style_colorbar(colorbar: Colorbar, spec: dict[str, Any] | None = None) -> None:
    colorbar_spec = _style(spec)["colorbar"]
    colorbar.ax.tick_params(labelsize=colorbar_spec["tick_size"])
    colorbar.ax.yaxis.label.set_size(colorbar_spec["label_size"])


def style_axis(
    ax: Axes,
    spec: dict[str, Any] | None = None,
    *,
    set_major_locator: bool = True,
) -> None:
    spec = _style(spec)
    axes = spec["axes"]
    ticks = spec["ticks"]
    grid = spec["grid"]
    for spine in ax.spines.values():
        spine.set_color(axes["edgecolor"])
        spine.set_linewidth(axes["linewidth"])
    ax.tick_params(
        axis="both",
        which="major",
        colors=ticks["color"],
        width=ticks["major_width"],
        length=ticks["major_size"],
    )
    if not ticks["minor_visible"]:
        ax.minorticks_off()
    if set_major_locator:
        ax.xaxis.set_major_locator(MaxNLocator(nbins=ticks["major_n_locator"]["default"]))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=ticks["major_n_locator"]["default"]))
    if grid["visible"]:
        ax.grid(
            True,
            color=grid["color"],
            alpha=grid["alpha"],
            linestyle=grid["linestyle"],
            linewidth=grid["linewidth"],
        )
    else:
        ax.grid(False)


def _is_colorbar_axis(ax: Axes) -> bool:
    return ax.get_label() == "<colorbar>" or hasattr(ax, "_colorbar")


def finalize_figure(fig: Figure, spec: dict[str, Any] | None = None) -> None:
    spec = _style(spec)
    data_axes = [ax for ax in fig.axes if not _is_colorbar_axis(ax)]
    if not spec["axes"]["show_title"] and len(data_axes) == 1:
        data_axes[0].set_title("")
    fig.tight_layout(pad=0.5)


def savefig_kwargs(
    spec: dict[str, Any] | None = None,
    *,
    artwork_type: str = "line",
) -> dict[str, Any]:
    figure = _style(spec)["figure"]
    dpi_keys = {
        "halftone": "halftone_dpi",
        "combination": "combination_dpi",
        "line": "line_art_dpi",
    }
    if artwork_type not in dpi_keys:
        raise ValueError(f"unknown artwork type {artwork_type!r}; expected one of {sorted(dpi_keys)}")
    return {
        "dpi": figure[dpi_keys[artwork_type]],
        "bbox_inches": None if figure["save_bbox"] == "standard" else figure["save_bbox"],
        "pad_inches": figure["pad_inches"],
        "facecolor": figure["facecolor"],
    }


def save_figure(
    fig: Figure,
    output_base: str | Path,
    *,
    spec: dict[str, Any] | None = None,
    formats: Sequence[str] = ("pdf", "tiff"),
    artwork_type: str = "line",
) -> list[Path]:
    """Save a figure with profile-backed export settings."""
    spec = _style(spec)
    base = Path(output_base)
    base.parent.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for fmt in formats:
        path = base.with_suffix(f".{fmt.lstrip('.')}")
        export_kwargs = savefig_kwargs(spec, artwork_type=artwork_type)
        if path.suffix.lower() in {".tif", ".tiff", ".jpg", ".jpeg"}:
            _save_opaque_bitmap(fig, path, export_kwargs, spec["figure"]["facecolor"])
        else:
            fig.savefig(path, **export_kwargs)
        saved.append(path)
    return saved


def _save_opaque_bitmap(
    fig: Figure,
    path: Path,
    export_kwargs: dict[str, Any],
    facecolor: str,
) -> None:
    from io import BytesIO

    from PIL import Image

    with BytesIO() as buffer:
        fig.savefig(buffer, format="png", **export_kwargs)
        buffer.seek(0)
        with Image.open(buffer) as image:
            rgba = image.convert("RGBA")
        flattened = Image.new("RGB", rgba.size, facecolor)
        flattened.paste(rgba, mask=rgba.getchannel("A"))
    save_kwargs: dict[str, Any] = {"dpi": (export_kwargs["dpi"], export_kwargs["dpi"])}
    if path.suffix.lower() in {".tif", ".tiff"}:
        save_kwargs["compression"] = "tiff_lzw"
    else:
        save_kwargs["quality"] = 95
    flattened.save(path, **save_kwargs)
    flattened.close()


def fill_alpha(spec: dict[str, Any] | None = None) -> float:
    return float(_style(spec)["line"]["fill_alpha"])


def errorbar_capsize(spec: dict[str, Any] | None = None) -> float:
    return float(_style(spec)["line"]["errorbar_capsize"])


def annotate_panel(
    ax: Axes,
    label: str,
    spec: dict[str, Any] | None = None,
    x: float = 0.02,
    y: float = 0.98,
) -> None:
    annotation = _style(spec)["annotation"]
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=annotation["panel_label_fontsize"],
        fontweight=annotation["panel_label_fontweight"],
        color=annotation["color"],
        ha="left",
        va="top",
    )


__all__ = [
    "DEFAULT_PROFILE_PATH",
    "DEFAULT_SCHEMA_PATH",
    "ProfileError",
    "STYLE_PATH",
    "annotate_panel",
    "apply_elsevier_style",
    "apply_journal_style",
    "band_style_kwargs",
    "bar_style_kwargs",
    "colorbar_kwargs",
    "errorbar_capsize",
    "figure_width",
    "figure_size",
    "fill_alpha",
    "finalize_figure",
    "graphical_abstract_size",
    "heatmap_kwargs",
    "line_style_kwargs",
    "load_profile",
    "load_style",
    "resolve_profile_resource",
    "save_figure",
    "savefig_kwargs",
    "scatter_style_kwargs",
    "style_axis",
    "style_colorbar",
    "validate_profile",
]
