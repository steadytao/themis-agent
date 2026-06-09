# Screen reader and WCAG-oriented design

Themis is designed so review material is not trapped inside a visual-only interface.

The CLI path can generate the same Markdown report as the browser UI:
```powershell
uv run themis-review samples/change_risky.md > themis-review.md
```

The report uses structured headings, lists and text labels for recommendation, readiness confidence, risks, missing evidence, verification steps, rollback questions and human-review notes. Severity and readiness are written as text rather than relying on colour alone.

# Screen reader and plain-text use

Markdown output can be read in a terminal, committed to Git, attached to tickets or converted into other document formats. The output is intended to remain useful when read linearly by a screen reader or reviewed in plain text.

The Streamlit UI uses standard controls, labelled fields, tabs, tables and download buttons. Those controls provide a better accessibility baseline than custom canvas or image-only interfaces.

The normal `Report` tab also exposes the complete Markdown report in a labelled `Markdown report` text area and provides a `Download markdown report` button. This gives screen-reader users and keyboard-only reviewers a linear report path that does not depend on dataframe navigation.

# WCAG-oriented practices

The project does not claim completed WCAG compliance, a WCAG audit or accessibility certification.

Current and future UI work preserves these practices where possible:
- keep all controls labelled for assistive technology
- keep keyboard navigation usable
- keep focus states visible
- avoid relying on colour alone for severity, status or recommendation
- keep text contrast strong
- keep headings and report sections in a logical reading order
- provide text alternatives for diagrams, screenshots, GIFs and videos
- keep the CLI and Markdown path functional when UI changes are made

# Architecture accessibility

The architecture is documented in both Mermaid and prose. The diagram is helpful for sighted review. The prose documentation remains the source of truth for readers who cannot use the diagram.
