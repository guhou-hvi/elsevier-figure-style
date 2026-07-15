library(ggplot2)

args <- commandArgs(trailingOnly = FALSE)
file_arg <- "--file="
script_path <- sub(file_arg, "", args[grep(file_arg, args)])
if (length(script_path) == 0) {
  script_path <- file.path("examples", "r", "good_ggplot_demo.R")
}
root <- normalizePath(file.path(dirname(script_path), "..", ".."), mustWork = FALSE)
source(file.path(root, "skills", "elsevier-figure-style", "scripts", "elsevier_theme.R"))
config_path <- file.path(root, "skills", "elsevier-figure-style", "assets", "elsevier_figure_style.json")
profile <- load_journal_profile(config_path)

data <- read.csv(file.path(root, "examples", "data", "training_metrics.csv"))
plot <- ggplot(data, aes(epoch)) +
  geom_line(aes(y = train, color = "train"), linewidth = profile$style$line$linewidth) +
  geom_line(aes(y = validation, color = "validation"), linewidth = profile$style$line$linewidth) +
  geom_point(aes(y = train, color = "train"), size = profile$style$line$marker_size / 2) +
  geom_point(aes(y = validation, color = "validation"), size = profile$style$line$marker_size / 2) +
  scale_color_manual(values = journal_palette(config_path)) +
  labs(x = "Epoch", y = "Loss") +
  theme_journal(config_path)

save_journal(
  plot,
  file.path(root, "examples", "outputs", "good_ggplot_demo"),
  formats = c("pdf", "png"),
  artwork_type = "line",
  config_path = config_path
)
