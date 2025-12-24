Reports README

This folder contains three Markdown reports describing the FalconResQ application:

- `report_full.md` — comprehensive technical report (detailed)
- `report_medium.md` — condensed report (medium detail)
- `report_short.md` — short summary

Generating PDFs

To convert the Markdown files to PDF locally, you can use one of the following methods.

Method A — Pandoc (recommended):

1. Install Pandoc: https://pandoc.org/installing.html
2. (Optional) Install a PDF engine (wkhtmltopdf, or use LaTeX like TinyTeX).

Example commands:

```bash
# Convert to PDF (requires a PDF engine installed)
pandoc report_full.md -o report_full.pdf
pandoc report_medium.md -o report_medium.pdf
pandoc report_short.md -o report_short.pdf
```

Method B — Python script (uses `markdown` and `pdfkit`) — requires `wkhtmltopdf` and `pip install markdown pdfkit`.

```bash
python scripts/convert_md_to_pdf.py reports/report_full.md reports/report_full.pdf
```

Notes

- If you lack a local PDF engine, the Markdown files can be opened in any editor (VS Code) and exported to PDF.
- The `scripts/convert_md_to_pdf.py` script included attempts a conversion but depends on system packages.
