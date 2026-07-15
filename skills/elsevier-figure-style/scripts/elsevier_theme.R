.journal_theme_source <- tryCatch(
  normalizePath(sys.frame(1)$ofile, mustWork = FALSE),
  error = function(...) normalizePath("elsevier_theme.R", mustWork = FALSE)
)

default_journal_profile <- function() {
  script_dir <- dirname(.journal_theme_source)
  candidates <- c(
    file.path(script_dir, "profile.json"),
    file.path(script_dir, "..", "assets", "elsevier_figure_style.json")
  )
  existing <- candidates[file.exists(candidates)]
  if (length(existing) == 0) {
    stop("No journal figure profile found. Pass config_path explicitly.", call. = FALSE)
  }
  normalizePath(existing[[1]], mustWork = TRUE)
}

.is_absolute_path <- function(path) {
  grepl("^(/|[A-Za-z]:[/\\\\]|\\\\\\\\)", path)
}

.is_within_path <- function(path, root) {
  path <- normalizePath(path, winslash = "/", mustWork = TRUE)
  root <- normalizePath(root, winslash = "/", mustWork = TRUE)
  if (.Platform$OS.type == "windows") {
    path <- tolower(path)
    root <- tolower(root)
  }
  identical(path, root) || startsWith(path, paste0(root, "/"))
}

.require_fields <- function(object, fields, label) {
  missing <- fields[vapply(fields, function(field) is.null(object[[field]]), logical(1))]
  if (length(missing) > 0) {
    stop(sprintf("Journal figure profile is missing %s.%s", label, missing[[1]]), call. = FALSE)
  }
}

.require_positive <- function(value, label) {
  if (!is.numeric(value) || length(value) != 1 || is.na(value) || value <= 0) {
    stop(sprintf("Journal figure profile field %s must be a positive number.", label), call. = FALSE)
  }
}

validate_journal_profile <- function(profile, config_path) {
  .require_fields(
    profile,
    c("$schema", "schema_version", "bundle_root", "identity", "resources", "profiles", "audit", "style"),
    "root"
  )
  if (profile$schema_version != 1) {
    stop("Unsupported journal figure profile schema_version.", call. = FALSE)
  }
  if (!is.character(profile$bundle_root) || length(profile$bundle_root) != 1 ||
      !nzchar(profile$bundle_root) || .is_absolute_path(profile$bundle_root)) {
    stop("Journal figure profile bundle_root must be a non-empty relative path.", call. = FALSE)
  }
  if (!profile$bundle_root %in% c(".", "..")) {
    stop("Journal figure profile bundle_root must be '.' or '..'.", call. = FALSE)
  }

  config_path <- normalizePath(config_path, winslash = "/", mustWork = TRUE)
  bundle_root <- normalizePath(
    file.path(dirname(config_path), profile$bundle_root),
    winslash = "/",
    mustWork = TRUE
  )
  referenced_paths <- c(profile$`$schema`, unlist(profile$resources, use.names = FALSE))
  for (relative_path in referenced_paths) {
    if (!is.character(relative_path) || length(relative_path) != 1 ||
        !nzchar(relative_path) || .is_absolute_path(relative_path)) {
      stop("Journal figure profile references must be non-empty relative paths.", call. = FALSE)
    }
    resolved <- normalizePath(
      file.path(dirname(config_path), relative_path),
      winslash = "/",
      mustWork = TRUE
    )
    if (!.is_within_path(resolved, bundle_root)) {
      stop(sprintf("Journal figure profile reference escapes bundle_root: %s", relative_path), call. = FALSE)
    }
  }

  .require_fields(profile$profiles, c("default", "order", "definitions"), "profiles")
  expected_profiles <- c("official", "editor", "strict")
  if (!identical(as.character(profile$profiles$order), expected_profiles) ||
      profile$profiles$default != "editor") {
    stop("Journal figure profile must define official/editor/strict in that order with editor as default.", call. = FALSE)
  }

  style <- profile$style
  .require_fields(
    style,
    c("font", "figure", "graphical_abstract", "axes", "ticks", "legend", "line", "palette"),
    "style"
  )
  .require_fields(style$font, c("size", "label_size", "tick_size", "legend_size", "sans_serif"), "style.font")
  .require_fields(
    style$figure,
    c(
      "save_dpi", "single_column_width_in", "one_half_column_width_in", "double_column_width_in",
      "default_layout", "default_aspect_ratio",
      "halftone_dpi", "combination_dpi", "line_art_dpi", "facecolor"
    ),
    "style.figure"
  )
  .require_fields(
    style$graphical_abstract,
    c("minimum_width_px", "minimum_height_px", "minimum_resolution_dpi"),
    "style.graphical_abstract"
  )
  .require_fields(style$axes, c("linewidth", "edgecolor", "labelcolor", "facecolor"), "style.axes")
  .require_fields(style$ticks, c("major_width", "color"), "style.ticks")
  .require_fields(style$line, c("linewidth", "marker_size"), "style.line")
  .require_fields(style$palette, c("cycle", "series"), "style.palette")

  positive_fields <- list(
    "style.font.size" = style$font$size,
    "style.font.label_size" = style$font$label_size,
    "style.font.tick_size" = style$font$tick_size,
    "style.figure.single_column_width_in" = style$figure$single_column_width_in,
    "style.figure.default_aspect_ratio" = style$figure$default_aspect_ratio,
    "style.line.linewidth" = style$line$linewidth,
    "style.line.marker_size" = style$line$marker_size
  )
  for (label in names(positive_fields)) {
    .require_positive(positive_fields[[label]], label)
  }
  if (!style$figure$default_layout %in% c("single", "one-half", "double")) {
    stop("style.figure.default_layout must be single, one-half, or double.", call. = FALSE)
  }

  .require_fields(profile$audit, c("artwork_types", "target_layouts", "detectors"), "audit")
  for (artwork_type in c("halftone", "combination", "line")) {
    .require_fields(profile$audit$artwork_types[[artwork_type]], "minimum_dpi", paste0("audit.artwork_types.", artwork_type))
  }
  dpi_pairs <- list(
    halftone = "halftone_dpi",
    combination = "combination_dpi",
    line = "line_art_dpi"
  )
  for (artwork_type in names(dpi_pairs)) {
    audit_dpi <- profile$audit$artwork_types[[artwork_type]]$minimum_dpi
    style_dpi <- style$figure[[dpi_pairs[[artwork_type]]]]
    .require_positive(audit_dpi, paste0("audit.artwork_types.", artwork_type, ".minimum_dpi"))
    if (!isTRUE(all.equal(as.numeric(audit_dpi), as.numeric(style_dpi)))) {
      stop(sprintf("Style and audit DPI values disagree for %s artwork.", artwork_type), call. = FALSE)
    }
  }
  if (style$figure$save_dpi < max(vapply(profile$audit$artwork_types, function(item) item$minimum_dpi, numeric(1)))) {
    stop("style.figure.save_dpi must be at least the largest artwork minimum DPI.", call. = FALSE)
  }

  .require_fields(
    profile$audit$target_layouts,
    c("minimal", "single", "one-half", "double", "graphical-abstract"),
    "audit.target_layouts"
  )
  width_pairs <- list(
    single = "single_column_width_in",
    "one-half" = "one_half_column_width_in",
    double = "double_column_width_in"
  )
  for (layout_name in names(width_pairs)) {
    audit_width <- profile$audit$target_layouts[[layout_name]]$width_mm
    style_width <- style$figure[[width_pairs[[layout_name]]]] * 25.4
    .require_positive(audit_width, paste0("audit.target_layouts.", layout_name, ".width_mm"))
    if (abs(audit_width - style_width) > 0.2) {
      stop(sprintf("Style and audit widths disagree for %s layout.", layout_name), call. = FALSE)
    }
  }

  audit_graphical <- profile$audit$target_layouts[["graphical-abstract"]]
  graphical_pairs <- list(
    minimum_width_px = "minimum_width_px",
    minimum_height_px = "minimum_height_px",
    minimum_dpi = "minimum_resolution_dpi"
  )
  for (audit_key in names(graphical_pairs)) {
    if (!isTRUE(all.equal(
      as.numeric(audit_graphical[[audit_key]]),
      as.numeric(style$graphical_abstract[[graphical_pairs[[audit_key]]]])
    ))) {
      stop(sprintf("Style and audit graphical-abstract values disagree for %s.", audit_key), call. = FALSE)
    }
  }

  required_detectors <- c(
    "style_integration", "manual_rcparams", "hardcoded_style", "grid", "low_dpi",
    "unknown_artwork_type", "minor_ticks", "minor_tick_style", "step_spacing", "unit_spacing",
    "font_official", "font_editor", "plot_title", "small_bitmap", "missing_dpi", "png_preview",
    "manual_metadata", "color_mode", "transparency", "file_size", "target_layout",
    "graphical_dimensions", "graphical_ratio", "corrupt_bitmap"
  )
  .require_fields(profile$audit$detectors, required_detectors, "audit.detectors")
  for (detector_name in required_detectors) {
    .require_fields(
      profile$audit$detectors[[detector_name]],
      c("rule_id", "minimum_profile", "severity", "allow_override"),
      paste0("audit.detectors.", detector_name)
    )
  }
  .require_fields(profile$audit$detectors$font_official, "threshold", "audit.detectors.font_official")
  .require_fields(profile$audit$detectors$font_editor, "threshold", "audit.detectors.font_editor")
  invisible(profile)
}

load_journal_profile <- function(config_path = NULL) {
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("The jsonlite package is required to load journal figure profiles.", call. = FALSE)
  }
  path <- if (is.null(config_path)) default_journal_profile() else config_path
  if (!file.exists(path)) {
    stop(sprintf("Journal figure profile not found: %s", path), call. = FALSE)
  }
  path <- normalizePath(path, winslash = "/", mustWork = TRUE)
  profile <- jsonlite::fromJSON(path, simplifyVector = TRUE)
  validate_journal_profile(profile, path)
  profile
}

journal_palette <- function(config_path = NULL) {
  profile <- load_journal_profile(config_path)
  unlist(profile$style$palette$series, use.names = TRUE)
}

.resolve_journal_font_family <- function(candidates) {
  candidates <- as.character(candidates)
  pdf_families <- names(grDevices::pdfFonts())
  supported <- candidates[candidates %in% pdf_families]
  if (length(supported) > 0) {
    return(supported[[1]])
  }
  "sans"
}

theme_journal <- function(config_path = NULL, base_size = NULL, base_family = NULL) {
  profile <- load_journal_profile(config_path)
  style <- profile$style
  if (is.null(base_size)) {
    base_size <- style$font$size
  }
  if (is.null(base_family)) {
    base_family <- .resolve_journal_font_family(style$font$sans_serif)
  }
  ggplot2::theme_classic(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.title = ggplot2::element_blank(),
      axis.line = ggplot2::element_line(linewidth = style$axes$linewidth, colour = style$axes$edgecolor),
      axis.ticks = ggplot2::element_line(linewidth = style$ticks$major_width, colour = style$ticks$color),
      axis.text = ggplot2::element_text(size = style$font$tick_size, colour = style$ticks$color),
      axis.title = ggplot2::element_text(size = style$font$label_size, colour = style$axes$labelcolor),
      legend.text = ggplot2::element_text(size = style$font$legend_size),
      legend.title = ggplot2::element_blank(),
      legend.key = ggplot2::element_blank(),
      legend.background = ggplot2::element_blank(),
      panel.background = ggplot2::element_rect(fill = style$axes$facecolor, colour = NA),
      plot.background = ggplot2::element_rect(fill = style$figure$facecolor, colour = NA)
    )
}

save_journal <- function(plot, filename, width = NULL, height = NULL,
                         formats = c("pdf", "tiff"), artwork_type = "line",
                         config_path = NULL, dpi = NULL) {
  profile <- load_journal_profile(config_path)
  style <- profile$style
  if (is.null(width)) {
    width_keys <- c(
      single = "single_column_width_in",
      "one-half" = "one_half_column_width_in",
      double = "double_column_width_in"
    )
    width <- style$figure[[width_keys[[style$figure$default_layout]]]]
  }
  if (is.null(height)) {
    height <- width / style$figure$default_aspect_ratio
  }
  dpi_keys <- c(
    line = "line_art_dpi",
    combination = "combination_dpi",
    halftone = "halftone_dpi"
  )
  if (!artwork_type %in% names(dpi_keys)) {
    stop("artwork_type must be line, combination, or halftone", call. = FALSE)
  }
  if (is.null(dpi)) {
    dpi <- style$figure[[dpi_keys[[artwork_type]]]]
  }
  dir.create(dirname(filename), recursive = TRUE, showWarnings = FALSE)
  saved <- character()
  for (fmt in formats) {
    path <- paste0(tools::file_path_sans_ext(filename), ".", fmt)
    ggplot2::ggsave(
      path,
      plot = plot,
      width = width,
      height = height,
      units = "in",
      dpi = dpi,
      bg = style$figure$facecolor
    )
    saved <- c(saved, path)
  }
  invisible(saved)
}

elsevier_palette <- function(config_path = NULL) {
  journal_palette(config_path)
}

theme_elsevier <- function(base_size = NULL, base_family = NULL, config_path = NULL) {
  theme_journal(config_path = config_path, base_size = base_size, base_family = base_family)
}

save_elsevier <- function(plot, filename, width = NULL, height = NULL,
                          dpi = NULL, formats = c("pdf", "tiff"),
                          artwork_type = "line", config_path = NULL) {
  save_journal(
    plot,
    filename,
    width = width,
    height = height,
    formats = formats,
    artwork_type = artwork_type,
    config_path = config_path,
    dpi = dpi
  )
}
