# Contributing

`elsevier-figure-style` is an unofficial, source-backed figure-review Skill. Contributions should improve reusable figure guidance, profile manifests, helpers, checkers, tests, or documentation without exposing private manuscript content.

Potential vulnerabilities must follow [SECURITY.md](./SECURITY.md) and must not be disclosed in a public issue.

## Good Contributions

- Official journal or publisher figure-format sources.
- Authorized, redacted paraphrases of editor/reviewer formatting comments.
- New journal profile bundles using the versioned manifest schema.
- Synthetic demos that expose a reusable plotting or audit pattern.
- Checker fixes accompanied by focused regression tests.
- Documentation and translation corrections.

## Privacy and Authorization

Before contributing revision evidence, remove manuscript titles, submission IDs, author names, affiliations, emails, reviewer identities, unpublished results, private methods, dataset names, and manuscript-specific claims.

Submit only a reusable paraphrase that you are authorized to publish. Never upload the original private correspondence, screenshots, tracked-review files, or confidential attachments. Non-official evidence must not be presented as official Elsevier policy.

## Evidence Levels

- A: official publisher or target-journal guidance.
- B: authorized redacted revision evidence.
- C: public review cases or reviewer-training material.
- D: practical visual QA or implementation heuristics.

Add or update a rule ID in `rule-registry.md` and keep its profile gate and source level explicit.

## Journal Profiles

Use `skills/elsevier-figure-style/assets/journal_figure_profile.schema.json`. A profile bundle must include one manifest plus every referenced evidence/checklist resource.

Existing detector types can change thresholds, severity, profile gates, and override policy through configuration. Changing detector behavior or messages requires checker code and tests. Relative resource paths resolve from the manifest directory.

Every manifest must declare a relative `bundle_root`. Its schema and resources must remain inside that boundary; absolute paths, traversal outside the bundle, and escaping symlinks are rejected.
The Python loader validates against the schema bundled with the helper. A profile-local `$schema` remains useful for editors and must exist, but it cannot weaken runtime validation.

## Local Validation

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the complete Python suite:

```bash
pytest
```

Run the demos and local Skill discovery:

```bash
python examples/python/good_line_plot.py
python examples/python/good_heatmap.py
python examples/python/good_bar.py
python examples/python/good_scatter.py
npx skills@1.5.15 add . --list
```

Run the expected source-checker failure without failing the shell:

```bash
python skills/elsevier-figure-style/scripts/check_elsevier_figure_style.py --path examples/bad/non_compliant_plot.py --profile editor --fail-on never
```

For R changes, install `ggplot2` and `jsonlite`, then run:

```bash
Rscript examples/r/good_ggplot_demo.R
```

Do not commit generated files under `examples/outputs/` or Python/R cache files.
