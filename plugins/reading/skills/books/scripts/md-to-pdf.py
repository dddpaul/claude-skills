"""Convert a markdown file to PDF using weasyprint, writing atomically.

Usage:
    md-to-pdf.py <source.md> <target.pdf>

Reads the source markdown, strips YAML frontmatter and Obsidian
`table-of-contents` fenced blocks, then converts to HTML via the `markdown`
package with `fenced_code`, `tables`, and `toc` extensions. An auto-generated
table of contents (H1 + H2 + H3) is injected at the top of the body with
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

EMOJI_SVG_MAP = {
    "\u2705": (
        '<svg class="icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="8" cy="8" r="7" fill="#2e8b57"/>'
        '<path d="M4.5 8l2.5 2.5 4.5-5" stroke="white" stroke-width="1.8" '
        'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        "</svg>"
    ),
    "\u274C": (
        '<svg class="icon" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M3.5 3.5 L12.5 12.5 M12.5 3.5 L3.5 12.5" '
        'stroke="#c41e3a" stroke-width="2.5" stroke-linecap="round"/>'
        "</svg>"
    ),
}
EMOJI_SVG_RE = re.compile("|".join(re.escape(k) for k in EMOJI_SVG_MAP))


def _svg_emoji(html: str) -> str:
    return EMOJI_SVG_RE.sub(lambda m: EMOJI_SVG_MAP[m.group(0)], html)


def _flatten_toc(tokens: list, out: list) -> None:
    for t in tokens:
        out.append((t["level"], t["id"], t["name"]))
        if t.get("children"):
            _flatten_toc(t["children"], out)


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
        extension_configs={"toc": {"toc_depth": "1-3"}},
    )
    html_body = md.convert(raw)
    html_body = _svg_emoji(html_body)
    flat: list = []
    _flatten_toc(md.toc_tokens, flat)
    if flat:
        rows = "".join(
            f'<li class="toc-h{level}" data-href="#{tid}">'
            f'<a href="#{tid}">{_svg_emoji(name)}</a></li>'
            for level, tid, name in flat
        )
        toc_section = (
            f'<nav class="toc"><h2 class="toc-title">Contents</h2>'
            f"<ul>{rows}</ul></nav>"
        )
    else:
        toc_section = ""
    html_doc = (
        '<!DOCTYPE html><html><head><meta charset="utf-8"></head>'
        f"<body>{toc_section}{html_body}</body></html>"
    )
    tmp = dst.with_name("." + dst.name + ".tmp")
    HTML(string=html_doc, base_url=str(src.parent)).write_pdf(
        str(tmp), stylesheets=[CSS(filename=str(css_path))]
    )
    tmp.replace(dst)
    print(str(dst))


if __name__ == "__main__":
    main()
