"""The MCP server: three tools over stdio.

Runs locally. Files never leave the machine; the only thing that crosses the
wire is the report. Any MCP client with its own model and API key can use it.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from wcag_tool import engine, log
from wcag_tool.findings import ROUTES_SUMMARY

INSTRUCTIONS = (
    "Accessibility triage for course documents (DOCX, PPTX, PDF). scan_document returns "
    "routed findings for one file; scan_folder does a pile and adds Route 5 candidates and a "
    "ready-made routed table; fix_document repairs only what is deterministic unless a person "
    "names a specific fix; describe_routes explains the five routes. Never describe a clean "
    "report as conformance. Alt text is always a proposal for a person to confirm."
)

mcp = MCPServer("wcag-tool", instructions=INSTRUCTIONS)


@mcp.tool()
def scan_document(path: str) -> dict[str, Any]:
    """Scan one DOCX, PPTX or PDF file and return routed accessibility findings.

    Each finding carries a WCAG criterion, a route (1 auto-fix, 2 content owner,
    3 manual test, 4 expedited, 5 systemic), the closure evidence it needs, and
    a fix_id when the tool can repair it. The report also lists which criteria
    were evaluated and which were not. A clean report is not a conformance claim.

    Args:
        path: Absolute or relative path to the file on this machine.
    """
    return engine.scan(Path(path)).to_dict()


@mcp.tool()
def fix_document(
    path: str,
    apply: list[str] | None = None,
    output_path: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Write a remediated copy of the file and a JSON record of before and after.

    Route 1 fixes are applied by default: the document title, and the document
    language once a person has named it (set-language is held and reported
    under `held` until `language` is given; the tool never guesses a language).
    Fixes attached to Route 2 findings, such as mark-header-row:0 or
    apply-heading:12:2, are applied only when named in `apply`, after a person
    has confirmed the proposal; an id that matches no finding is returned in
    `unknown_fix_ids` and not applied. The original is never overwritten. Read
    back `applied`, `failed`, `unknown_fix_ids` and `held` before reporting.

    Args:
        path: The file to remediate.
        apply: Fix ids a person has confirmed, taken from a prior scan result.
        output_path: Where to write the copy. Defaults to <name>.remediated.<ext>.
            Leave it unset; it must never be the original.
        language: Language code for set-language, e.g. en-US or es-ES, as named
            by the person who owns the file.
    """
    return engine.fix(
        Path(path),
        apply=apply,
        output=Path(output_path) if output_path else None,
        language=language,
    )


@mcp.tool()
def scan_folder(path: str, recursive: bool = True) -> dict[str, Any]:
    """Scan every DOCX, PPTX and PDF under a folder and return the pile as one triage.

    Adds what a single scan cannot see: Route 5 candidates, meaning checks that
    recur across enough files to be fixed once at the template or the export
    setting instead of in every copy. The result includes a `markdown` field
    holding the routed table in the shape the triage skill asks for, with the
    owner column left blank for a person's name.

    Args:
        path: Folder on this machine.
        recursive: Descend into subfolders. Defaults to true.
    """
    return engine.scan_folder(Path(path), recursive=recursive).to_dict()


@mcp.tool()
def describe_routes() -> str:
    """Explain the five routes and four closure states every finding uses."""
    return ROUTES_SUMMARY


def main() -> None:
    """Run the server over stdio."""
    log.configure(logging.INFO)
    logging.getLogger(__name__).info("starting wcag-tool MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
