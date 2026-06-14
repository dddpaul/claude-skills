"""Convert a markdown file to PDF using weasyprint, writing atomically.

Usage:
    md-to-pdf.py <source.md> <target.pdf>

Reads the source markdown, converts to HTML via the `markdown` package with
`fenced_code` and `tables` extensions, then renders to PDF using weasyprint
with the sibling `references/styles.css` stylesheet. The PDF is written to
a hidden `.<name>.tmp` file alongside the target and `os.replace`d into
place so iCloud only ever sees a complete file.
"""

import re
import sys
from pathlib import Path

import markdown
from weasyprint import CSS, HTML


def main() -> None:
    src = Path(sys.argv[1]).resolve()
    dst = Path(sys.argv[2]).resolve()
    css_path = Path(__file__).parent.parent / "references" / "styles.css"
    raw = src.read_text(encoding="utf-8")
    raw = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", raw, count=1, flags=re.DOTALL)
    html_body = markdown.markdown(
        raw,
        extensions=["fenced_code", "tables"],
    )
    html_doc = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f"<body>{html_body}</body></html>"
    )
    tmp = dst.with_name("." + dst.name + ".tmp")
    HTML(string=html_doc).write_pdf(
        str(tmp), stylesheets=[CSS(filename=str(css_path))]
    )
    tmp.replace(dst)
    print(str(dst))


if __name__ == "__main__":
    main()
