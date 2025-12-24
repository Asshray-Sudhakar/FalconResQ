"""
Simple Markdown to PDF converter using `markdown` and `pdfkit`.
This script requires:
- pip install markdown pdfkit
- wkhtmltopdf installed and on PATH (https://wkhtmltopdf.org/)

Usage:
python convert_md_to_pdf.py input.md output.pdf
"""
import sys
import os

try:
    import markdown
    import pdfkit
except ImportError:
    print("Required packages not installed. Run: pip install markdown pdfkit")
    sys.exit(1)


def md_to_pdf(input_md, output_pdf):
    with open(input_md, 'r', encoding='utf-8') as f:
        text = f.read()
    html = markdown.markdown(text, extensions=['tables', 'fenced_code'])
    # Basic HTML wrapper
    html_doc = f"""<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>Report</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
pre { background: #f5f5f5; padding: 10px; overflow: auto; }
code { background: #f5f5f5; padding: 2px 4px; }
</style>
</head>
<body>
{html}
</body>
</html>
"""
    try:
        pdfkit.from_string(html_doc, output_pdf)
        print(f"Saved PDF: {output_pdf}")
    except Exception as e:
        print("Failed to generate PDF; ensure wkhtmltopdf is installed and on PATH.")
        print(str(e))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python convert_md_to_pdf.py input.md output.pdf")
        sys.exit(1)
    input_md = sys.argv[1]
    output_pdf = sys.argv[2]
    if not os.path.exists(input_md):
        print(f"Input file not found: {input_md}")
        sys.exit(1)
    md_to_pdf(input_md, output_pdf)
