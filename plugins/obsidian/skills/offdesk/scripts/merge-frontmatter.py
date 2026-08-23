#!/usr/bin/env python3
"""Merge offdesk-* keys into a markdown file's YAML frontmatter.

Reads source markdown from a path, merges four keys
(offdesk-source, offdesk-project-root, offdesk-copied-at,
offdesk-transport) into the existing leading `---` ... `---`
frontmatter block (or creates one if absent), and writes the result to a
destination path. Existing keys are preserved untouched. A key that
already exists is updated in place rather than duplicated.

Usage:

    merge-frontmatter.py \\
        --src <source.md> \\
        --dst <vault-copy.md> \\
        --offdesk-source <rel-path> \\
        --offdesk-project-root <abs-path> \\
        [--offdesk-copied-at <iso-utc>] \\
        [--offdesk-transport syncthing|icloud]

If --offdesk-copied-at is omitted, the current UTC time in ISO 8601
seconds precision is used. If --offdesk-transport is omitted it defaults
to the skill's default transport, syncthing; the key records which vault
the copy was written to, so a vault copy stays self-describing if a vault
later moves. The merge is line-based and assumes scalar string values for
the offdesk-* keys (no nested structures, no list values). Non-offdesk
keys in the frontmatter are preserved verbatim regardless of their shape.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

FRONTMATTER_DELIM = "---"
OFFDESK_KEYS = (
    "offdesk-source",
    "offdesk-project-root",
    "offdesk-copied-at",
    "offdesk-transport",
)
# Kept in lockstep with scripts/transports.py TRANSPORTS by a test, so this
# script stays importable and runnable on its own.
TRANSPORT_NAMES = ("syncthing", "icloud")
DEFAULT_TRANSPORT = "syncthing"


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """Return (frontmatter_lines, body_text).

    frontmatter_lines is the list of lines between the leading `---`
    delimiters, exclusive of the delimiters themselves. If the file
    has no leading frontmatter, returns ([], text).
    """
    lines = text.splitlines(keepends=False)
    if not lines or lines[0].strip() != FRONTMATTER_DELIM:
        return [], text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == FRONTMATTER_DELIM:
            fm_lines = lines[1:idx]
            body_lines = lines[idx + 1 :]
            body = "\n".join(body_lines)
            if text.endswith("\n") and body and not body.endswith("\n"):
                body += "\n"
            return fm_lines, body
    return [], text


def merge_keys(fm_lines: list[str], updates: dict[str, str]) -> list[str]:
    """Merge updates into fm_lines in place.

    Keys that already exist at the top level get their values replaced;
    new keys are appended. Top-level keys are detected as lines matching
    `<key>: ...` with no leading whitespace.
    """
    remaining = dict(updates)
    result: list[str] = []
    for line in fm_lines:
        stripped = line.lstrip()
        if line == stripped and ":" in line:
            key = line.split(":", 1)[0].strip()
            if key in remaining:
                result.append(f"{key}: {remaining.pop(key)}")
                continue
        result.append(line)
    for key, value in remaining.items():
        result.append(f"{key}: {value}")
    return result


def render(fm_lines: list[str], body: str) -> str:
    """Render frontmatter + body back to a string."""
    header = FRONTMATTER_DELIM + "\n" + "\n".join(fm_lines) + "\n" + FRONTMATTER_DELIM + "\n"
    if body and not body.startswith("\n"):
        return header + body
    return header + body


def iso_utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", required=True, type=Path)
    parser.add_argument("--dst", required=True, type=Path)
    parser.add_argument("--offdesk-source", required=True)
    parser.add_argument("--offdesk-project-root", required=True)
    parser.add_argument("--offdesk-copied-at", default=None)
    parser.add_argument(
        "--offdesk-transport",
        default=DEFAULT_TRANSPORT,
        choices=TRANSPORT_NAMES,
    )
    args = parser.parse_args(argv)

    text = args.src.read_text(encoding="utf-8")
    fm_lines, body = split_frontmatter(text)
    updates = {
        "offdesk-source": args.offdesk_source,
        "offdesk-project-root": args.offdesk_project_root,
        "offdesk-copied-at": args.offdesk_copied_at or iso_utc_now(),
        "offdesk-transport": args.offdesk_transport,
    }
    missing = [k for k in OFFDESK_KEYS if k not in updates]
    if missing:
        raise SystemExit(f"missing required keys: {missing}")
    merged = merge_keys(fm_lines, updates)
    out = render(merged, body)
    args.dst.parent.mkdir(parents=True, exist_ok=True)
    args.dst.write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
