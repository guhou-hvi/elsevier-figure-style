# R Workflow

R/ggplot2 is a supported basic v0.1 path. It reads the same versioned manifest as Python through `jsonlite`; there is no R static checker.

Install `ggplot2` and `jsonlite` before use. The R loader validates the fixed profile order, bundle boundary, required plotting fields, and shared DPI values before applying a theme.

## Minimal Pattern

```r
library(ggplot2)
source("skills/elsevier-figure-style/scripts/elsevier_theme.R")

p <- ggplot(df, aes(epoch, loss, color = split)) +
  geom_line(linewidth = 0.45) +
  geom_point(size = 1.6) +
  scale_color_manual(values = journal_palette()) +
  labs(x = "Epoch", y = "Loss") +
  theme_journal()

save_journal(p, "figure", formats = c("pdf", "tiff"), artwork_type = "line")
```

Pass `config_path = "path/to/profile.json"` to `journal_palette()`, `theme_journal()`, and `save_journal()` to select another profile. The aliases `elsevier_palette()`, `theme_elsevier()`, and `save_elsevier()` remain available.

## Final Audit

- Use the shared submission checklist and visual audit workflow.
- Verify target-journal overrides, final dimensions, artwork type, and export format.
- Do not treat the absence of an R static checker as proof of compliance.
