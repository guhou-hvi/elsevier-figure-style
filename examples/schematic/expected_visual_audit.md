# Expected Visual Audit Example

Fixture: `schematic_demo.svg`

This is a synthetic example of the report shape expected from `references/visual-audit-workflow.md`.

| Severity | Location | Issue | Source/Rule | Recommended fix |
| --- | --- | --- | --- | --- |
| PASS | panel labels | `(a)` and `(b)` are visible, high-contrast, and placed near the top-left of each panel region. | ED-06, VIS-04 | Keep label style consistent across manuscript figures. |
| PASS | main workflow row | Boxes, arrows, and labels are evenly spaced with no obvious overlap. | VIS-02, VIS-03 | Keep current spacing if final journal width preserves legibility. |
| WARN | entire figure | SVG metadata is not parsed by the v1 metadata checker. | STYLE-02 | Use manual visual audit and verify journal-specific SVG/PDF requirements. |
