"""The MCP server: eight tools over stdio.

Runs locally. Files never leave the machine; what crosses the wire to the
client's model is the report and, when show_asset is asked for one, a picture
from the file. Any MCP client with its own model and API key can use it.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Image

from wcag_tool import assets, compare, content, engine, log, rules
from wcag_tool.findings import ROUTES_SUMMARY
from wcag_tool.report import Batch, worklist_fields

INSTRUCTIONS = (
    "Accessibility triage for course documents (DOCX, PPTX, PDF). scan_document returns "
    "routed findings for one file, each with its locator; scan_folder does a pile and adds "
    "Route 5 candidates. Both return `worklist`, the plain-words work order already laid out "
    "from the scan's facts, and `worklist_items`, which maps each item number to its file, "
    "place and fix_id: build the reply on the worklist, filling its marked gaps by reading "
    "every page, since a scan reads settings, not meaning. extract_content gives you every "
    "page's words and objects in order, under the scan's place names: read it before you "
    "write the list. Change a course file only through fix_document, never with any other "
    "tool or code. For a PDF with no source, if the person asks for a rebuilt copy, rebuild "
    "it from extract_content into a new tagged file beside the original, and check it with "
    "compare_rebuild before calling it anything; the original is never touched. "
    "fix_document repairs only what is deterministic unless a person names a specific fix. "
    "Each proposal needs its own yes: a yes to a batch ('yes to all', 'fix everything') is a "
    "yes to nothing, so list the proposals, ask for each by its item, and pass only the ids "
    "confirmed one by one. Speak plainly: never show the person a route number, a check id "
    "or a fix id; name each item by its number and what it changes. describe_routes explains "
    "the five routes; explain_criterion quotes "
    "W3C's text for one WCAG criterion and says what the tool can and cannot judge about it. "
    "Never describe a clean report as conformance. Before you describe a picture or draft its "
    "alt text, look at it: show_asset returns the picture a finding's locator points at. Alt "
    "text is always a proposal for a person to confirm. Explain a criterion from its quoted "
    "text, not from memory."
)

mcp = MCPServer("wcag-tool", instructions=INSTRUCTIONS)


def _path(text: str) -> Path:
    """A path as a person or a model writes it, with ``~`` meaning the home folder."""
    return Path(text).expanduser()


@mcp.tool()
def scan_document(path: str) -> dict[str, Any]:
    """Scan one DOCX, PPTX or PDF file and return routed accessibility findings.

    Each finding carries a WCAG criterion, a route (1 auto-fix, 2 content owner,
    3 manual test, 4 expedited, 5 systemic), the closure evidence it needs, and
    a fix_id when the tool can repair it. The report also lists what was
    evaluated, what was not (every WCAG 2.1 A and AA criterion appears, with who
    can judge it), `coverage` (criterion numbers by status), and `criteria`
    (W3C's text for each criterion a finding names). `worklist` is the plain-words
    work order for the person, and `worklist_items` maps each of its numbers to
    the finding's place and fix_id. A clean report is not a conformance claim.

    Args:
        path: Absolute or relative path to the file on this machine.
    """
    report = engine.scan(_path(path))
    return {**report.to_dict(), **worklist_fields(Batch(reports=[report]))}


@mcp.tool()
def fix_document(
    path: str,
    apply: list[str] | None = None,
    output_path: str | None = None,
    language: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Write a remediated copy of the file and a JSON record of before and after.

    Route 1 fixes are applied by default: the document title, and the document
    language once a person has named it (set-language is held and reported
    under `held` until `language` is given; the tool never guesses a language).
    Pass the title the person wants in `title`. Without it, the title is taken
    from the file (a heading, the first slide title, or the file name), and the
    applied note says where it came from: show it to the person, and if it does
    not name the whole file, ask for the title and run again with `title`.
    Fixes attached to Route 2 findings, such as mark-header-row:0 or
    apply-heading:12:2, are applied only when named in `apply`, after a person
    has confirmed that proposal by itself. A yes to a batch ("yes to all") is a
    yes to nothing: ask for each one, and pass only the ids confirmed one by one.
    An id that matches no finding is returned in
    `unknown_fix_ids` and not applied. The original is never overwritten. Read
    back `applied`, `failed`, `unknown_fix_ids` and `held` before reporting.

    Args:
        path: The file to remediate.
        apply: Fix ids a person has confirmed, taken from a prior scan result.
        output_path: Where to write the copy. Defaults to <name>.remediated.<ext>.
            Leave it unset; it must never be the original.
        language: Language code for set-language, e.g. en-US or es-ES, as named
            by the person who owns the file.
        title: The document title, as the person named it, e.g. "ENVS 210 Syllabus,
            Fall 2026". Used exactly as given.
    """
    return engine.fix(
        _path(path),
        apply=apply,
        output=_path(output_path) if output_path else None,
        language=language,
        title=title,
    )


@mcp.tool()
def scan_folder(path: str, recursive: bool = True) -> dict[str, Any]:
    """Scan every DOCX, PPTX and PDF under a folder and return the pile as one triage.

    Adds what a single scan cannot see: Route 5 candidates, meaning checks that
    recur across enough files to be fixed once at the template or the export
    setting instead of in every copy. `worklist` is the plain-words work order
    to build the reply on, and `worklist_items` maps each of its numbers to the
    finding's place and fix_id. `markdown` holds the routed table: working data,
    not the reply.

    Args:
        path: Folder on this machine.
        recursive: Descend into subfolders. Defaults to true.
    """
    return engine.scan_folder(_path(path), recursive=recursive).to_dict()


@mcp.tool()
def show_asset(path: str, locator: str) -> list[str | Image]:
    """Show the picture a finding points at, so alt text is drafted from looking.

    Pass a finding's `locator` from a scan: `Picture 1` (Word), `slide 4, Picture 2`
    (PowerPoint), or `page 3` (PDF, which returns every picture that page draws).
    Each picture comes with a line saying where it is. Look before you describe a
    picture or draft its alt text; the draft is still a proposal the author confirms.
    A drawing made of shapes, such as a logo drawn in a PDF, is not a picture in the
    file and cannot be shown: the reply says so. Reads the file; writes nothing.

    Args:
        path: The course file on this machine.
        locator: The finding's locator, exactly as the scan gave it.
    """
    try:
        pictures = assets.extract(_path(path), locator)
    except assets.AssetError as error:
        return [str(error)]
    out: list[str | Image] = []
    for picture in pictures:
        out += [picture.label, Image(data=picture.data, format=picture.format)]
    return out


@mcp.tool()
def extract_content(path: str) -> dict[str, Any]:
    """Return a document's words and objects, in reading order, so you can read every page.

    One unit per page (PDF), per slide (PowerPoint), or for the whole Word document,
    each with ordered blocks: headings, paragraphs, list items, tables (cells, and
    whether a header row is marked), pictures (alt text, decorative), links (text
    and target), fill-in fields (name, tooltip), speaker notes, headers and footers.
    Places use the scan's names, so "Paragraph 14" here is item "Paragraph 14" in the
    worklist. It reports what the file marks and guesses no role it does not: an
    untagged PDF has text, not headings. Reads the file; writes nothing.

    Args:
        path: The course file on this machine.
    """
    return content.extract(_path(path))


@mcp.tool()
def compare_rebuild(original: str, rebuilt: str, ignore: list[str] | None = None) -> dict[str, Any]:
    """Check a rebuilt copy against its original before anyone relies on it.

    For a PDF with no source that an agent rebuilt from extract_content into a new
    tagged file. Checks: every word of the original in the rebuild, in order, nothing
    added (differences in `words.missing` and `words.added`, verbatim); the same number
    of pictures, and every figure in the rebuild's tags with alt text; every link
    target kept; the same fill-in fields, each now named; and a scan of the rebuild.
    `problems` lists what to resolve; report each to the person. Even with no
    problems, the rebuild is not a conformance claim: say `claim`, word for word or
    shorter. A scanned original has no text to compare, and a person must read the
    rebuild against it. Reads both files; writes nothing.

    Args:
        original: The file the rebuild was made from.
        rebuilt: The rebuilt copy, a different file.
        ignore: Phrases to leave out of the word check on both sides, such as a running
            footer the rebuild does not repeat on every page. Tell the person what you
            left out.
    """
    return compare.compare(_path(original), _path(rebuilt), ignore)


@mcp.tool()
def describe_routes() -> str:
    """Explain the five routes and four closure states every finding uses."""
    return ROUTES_SUMMARY


@mcp.tool()
def explain_criterion(criterion: str) -> dict[str, Any]:
    """Quote one WCAG 2.1 A or AA success criterion and say what this tool can judge of it.

    Returns W3C's normative text, the link to W3C's Understanding page, and for
    Word, PowerPoint and PDF: whether a check covers it in part, which checks,
    what a person still judges, and who (the author, an expert, or a
    screen-reader task test). Use it to explain why a finding matters, in W3C's
    words rather than from memory.

    Args:
        criterion: The criterion number, e.g. "1.3.1". A name after the number is ignored.
    """
    rule_set = rules.load()
    cid = criterion.strip().split(" ", 1)[0]
    if cid not in rule_set.criteria:
        return {
            "error": f"{cid!r} is not a WCAG 2.1 Level A or AA success criterion",
            "known": list(rule_set.criteria),
        }
    c = rule_set.criteria[cid]
    return {
        "id": c.id,
        "name": c.name,
        "level": c.level,
        "text": c.text,
        "understanding": c.understanding,
        "source": rule_set.source,
        "formats": {
            fmt: {
                "status": cell.status,
                "checks": [k.id for k in rule_set.checks_for(fmt, cid)],
                "still_to_judge": cell.note,
                "who": rules.WHO[cell.who],
                **({"applies_when": cell.when} if cell.when else {}),
            }
            for fmt, cell in rule_set.coverage[cid].items()
        },
    }


def main() -> None:
    """Run the server over stdio."""
    log.configure(logging.INFO)
    logging.getLogger(__name__).info("starting wcag-tool MCP server")
    mcp.run()


if __name__ == "__main__":
    main()
