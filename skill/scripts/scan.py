"""Scan course files and print the routed table. Read-only: nothing is ever written.

The same checks the MCP server runs, for an assistant that can run Python but has
no MCP tool connected (claude.ai with code execution, Claude Code, a notebook).
It reads what a text paste cannot show: alt text, header-row marks, the title
property, the default language, heading styles.

It does not fix anything. Fixes, the copy beside the original, and the record
are the MCP server's job.

Example:
    python scripts/scan.py "Course files/"
    python scripts/scan.py syllabus.docx slides.pptx --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _setup import ready

ready()

from wcag_tool import engine  # noqa: E402  (ready() puts the checks on the path)
from wcag_tool.report import render_markdown  # noqa: E402


def collect(paths: list[Path]) -> list[Path]:
    """Expand folders into the supported files under them; keep files as given."""
    out: list[Path] = []
    for path in paths:
        out.extend(engine.iter_supported(path) if path.is_dir() else [path])
    return out


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("paths", nargs="+", type=Path, help="files or folders")
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args(argv)
    batch = engine.scan_many(collect(args.paths))
    sys.stdout.write(
        json.dumps(batch.to_dict(), indent=2, ensure_ascii=False)
        if args.json
        else render_markdown(batch)
    )
    sys.stdout.write("\n")
    return 0 if batch.reports else 1


if __name__ == "__main__":
    sys.exit(main())
