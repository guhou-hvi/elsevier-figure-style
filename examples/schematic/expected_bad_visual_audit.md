# Expected Visual Audit: Flawed Schematic

Fixture: `bad_schematic.svg`

This expected report demonstrates the required location, severity, rule ID, and actionable fix. It is not produced by the metadata checker; an Agent must first render and view the SVG.

| Severity | Location | Issue | Source/Rule | Recommended fix |
| --- | --- | --- | --- | --- |
| FAIL | panel (a), input/model blocks | The two blocks overlap and the arrow crosses their text regions. | VIS-02 | Separate the blocks, reroute the arrow through clear whitespace, and recheck at final size. |
| WARN | panel (a), top-left | The panel label is visually fused with explanatory text and has weak contrast. | ED-07, VIS-04 | Keep `(a)` as a standalone high-contrast label and move the description into the caption. |
| WARN | panel (a), output block | Small low-contrast text is difficult to read. | ED-03, VIS-01 | Increase font size and text/background contrast. |
| WARN | entire figure | Spacing and margins are inconsistent, with unused central space and a compressed lower panel. | VIS-03, VIS-05 | Rebuild the layout on a consistent grid and balance panel heights and margins. |
