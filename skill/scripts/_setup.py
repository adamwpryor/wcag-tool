"""Shared start-up for the skill's scripts: find the checks, fail clearly if a library is missing.

Inside the skill zip, the checks sit next to this file in ``wcag_tool/``, copied
from the package at build time. In a checkout of the repository they come from
the installed ``wcag-tool`` package instead. Either way it is the same code the
MCP server runs.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
_NEEDED = {"docx": "python-docx", "pptx": "python-pptx", "pypdf": "pypdf", "lxml": "lxml"}


def ready() -> None:
    """Put the vendored checks on the path and confirm the file libraries import.

    Exits with status 2 and an install line when a library is missing, rather than
    failing halfway through a scan.
    """
    if (HERE / "wcag_tool").is_dir() and str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    missing = [pkg for mod, pkg in _NEEDED.items() if importlib.util.find_spec(mod) is None]
    if importlib.util.find_spec("wcag_tool") is None:
        missing.append("wcag-tool")
    if missing:
        sys.stderr.write(
            "These libraries are needed and not installed: "
            + ", ".join(missing)
            + "\nInstall them with: pip install "
            + " ".join(missing)
            + "\n"
        )
        raise SystemExit(2)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
