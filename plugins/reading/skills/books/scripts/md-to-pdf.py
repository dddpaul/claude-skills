"""Convert a markdown file to PDF using weasyprint, writing atomically.

Usage:
    md-to-pdf.py <source.md> <target.pdf>

Reads the source markdown, strips YAML frontmatter and Obsidian
`table-of-contents` fenced blocks, then converts to HTML via the `markdown`
package with `fenced_code`, `tables`, and `toc` extensions. An auto-generated
table of contents (H1 + H2) is injected at the top of the body with
`target-counter`-compatible markup so the CSS can emit dot leaders and page
numbers. The document is rendered to PDF via weasyprint with the sibling
`references/styles.css` stylesheet, written to a hidden `.<name>.tmp` file
alongside the target and `os.replace`d into place so iCloud only ever sees
a complete file.
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
    raw = re.sub(
        r"^```table-of-contents\b.*?^```\s*\n?",
        "",
        raw,
        flags=re.DOTALL | re.MULTILINE,
    )
    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc"],
        extension_configs={"toc": {"toc_depth": "1-2"}},
    )
    html_body = md.convert(raw)
    toc_html = md.toc or ""
    toc_html = re.sub(
        r'<li><a href="([^"]+)">',
        r'<li data-href="\1"><a href="\1">',
        toc_html,
    )
    toc_section = (
        f'<nav class="toc"><h2 class="toc-title">Contents</h2>{toc_html}</nav>'
        if toc_html
        else ""
    )
    html_doc = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f"<body>{toc_section}{html_body}</body></html>"
    )
    tmp = dst.with_name("." + dst.name + ".tmp")
    HTML(string=html_doc).write_pdf(
        str(tmp), stylesheets=[CSS(filename=str(css_path))]
    )
    tmp.replace(dst)
    print(str(dst))


if __name__ == "__main__":
    main()
