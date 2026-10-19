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
    "routed findings; fix_document repairs only what is deterministic unless a person "
    "names a specific fix; describe_routes explains the five routes. Never describe a "
    "clean report as conformance. Alt text is always a proposal for a person to confirm."
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
    language: str = "en-US",
) -> dict[str, Any]:
    """Write a remediated copy of the file and a JSON record of before and after.

    Route 1 fixes (document title, document language) are applied by default.
    Fixes attached to Route 2 findings, such as mark-header-row:0 or
    apply-heading:12:2, are applied only when named in `apply`, after a person
    has confirmed the proposal. The original is never overwritten.

    Args:
        path: The file to remediate.
        apply: Extra fix ids to apply, taken from a prior scan_document result.
        output_path: Where to write the copy. Defaults to <name>.remediated.<ext>.
        language: Language code for set-language, e.g. en-US or es-ES.
    """
    return engine.fix(
        Path(path),
        apply=apply,
        output=Path(output_path) if output_path else None,
        language=language,
    )


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
