"""Command line: the same engine for people without an MCP client.

``wcag-tool`` with no arguments starts the MCP server over stdio, which is what
an MCP client's configuration expects. Subcommands run the engine directly and
write the result to stdout.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from wcag_tool import __version__, engine, log
from wcag_tool.demo import make_demo_set
from wcag_tool.report import render_markdown, render_worklist


def _path(text: str) -> Path:
    """A path as typed, with ``~`` meaning the home folder on every platform."""
    return Path(text).expanduser()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wcag-tool",
        description=(
            "Accessibility triage for course documents (DOCX, PPTX, PDF). "
            "With no subcommand, starts the MCP server over stdio."
        ),
    )
    parser.add_argument("--version", action="version", version=f"wcag-tool {__version__}")
    sub = parser.add_subparsers(dest="command")

    scan = sub.add_parser("scan", help="scan a file or a folder and print the routed table")
    scan.add_argument("path", type=_path)
    scan.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    scan.add_argument(
        "--list", action="store_true", help="print the plain-words work order, not the table"
    )
    scan.add_argument("--no-recursive", action="store_true", help="do not descend into subfolders")

    fix = sub.add_parser("fix", help="write a remediated copy of one file and a JSON record")
    fix.add_argument("path", type=_path)
    fix.add_argument("--apply", action="append", default=[], metavar="FIX_ID")
    fix.add_argument("--output", type=_path, default=None)
    fix.add_argument(
        "--language",
        default=None,
        help="language code for set-language (en-US, es-ES); without it the fix is held",
    )
    fix.add_argument(
        "--title",
        default=None,
        help="the document title to set; without it, one is taken from the file and flagged",
    )

    demo = sub.add_parser("demo", help="write fictional files with known defects into a folder")
    demo.add_argument("directory", type=_path)

    sub.add_parser("serve", help="start the MCP server over stdio (the default)")
    return parser


def _write(text: str) -> None:
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Arguments without the program name. Defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    args = _parser().parse_args(argv)
    log.configure(logging.INFO)

    if args.command in (None, "serve"):
        from wcag_tool.server import mcp

        mcp.run()
        return 0

    # Windows consoles default to a legacy code page; reports carry file names and
    # punctuation it cannot encode. The MCP server writes bytes and is unaffected.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    try:
        if args.command == "scan":
            if args.path.is_dir():
                batch = engine.scan_folder(args.path, recursive=not args.no_recursive)
            else:
                batch = engine.scan_many([args.path])
            if args.json:
                _write(json.dumps(batch.to_dict(), indent=2))
            else:
                _write(render_worklist(batch) if args.list else render_markdown(batch))
            return 0
        if args.command == "fix":
            record = engine.fix(
                args.path,
                apply=args.apply or None,
                output=args.output,
                language=args.language,
                title=args.title,
            )
            _write(json.dumps(record, indent=2))
            return 0
        if args.command == "demo":
            for path in make_demo_set(args.directory):
                _write(str(path))
            return 0
    except (FileNotFoundError, engine.UnsupportedFormatError) as exc:
        sys.stderr.write(f"wcag-tool: {exc}\n")
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
