"""Checks for Word documents (.docx).

Every check returns findings already routed. Route 1 is reserved for the two
defects whose repair invents no meaning: a missing document title and a missing
document language. Everything else is a proposal for the person who knows the
content, because marking a row as a header or a paragraph as a heading asserts
something about what the author meant.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentType
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from wcag_tool.alt import is_missing_or_placeholder
from wcag_tool.findings import Closure, Confidence, Finding, Report, Route

EVALUATED = [
    "1.1.1 Non-text Content (alt text present and not a filename or auto-generated phrase)",
    "1.3.1 Info and Relationships (heading styles, table header rows)",
    "2.4.2 Page Titled (document title)",
    "2.4.4 Link Purpose (link text)",
    "2.4.6 Headings and Labels (heading level sequence, empty headings)",
    "3.1.1 Language of Page (default document language)",
]

NOT_EVALUATED = [
    "1.1.1 quality of existing alt text: a person must judge meaning",
    "1.3.2 Meaningful Sequence: reading order of floating objects and text boxes",
    "1.4.1 Use of Color and 1.4.3 Contrast: run-level color is not analyzed yet",
    "3.1.2 Language of Parts: per-run language changes are not analyzed",
]

GENERIC_LINK_TEXT = {"click here", "here", "link", "read more", "more", "this", "this link"}
_HEADING_RE = re.compile(r"^heading (\d)$", re.IGNORECASE)
_MAX_HEADING_WORDS = 12


def style_name(paragraph: Paragraph) -> str:
    """Return the paragraph's style name, or an empty string when it has no style."""
    return paragraph.style.name if paragraph.style is not None else ""


def _heading_level(style_name: str) -> int | None:
    """Return the heading level for a style name such as ``Heading 2``, else None."""
    match = _HEADING_RE.match(style_name.strip())
    return int(match.group(1)) if match else None


def _default_language(doc: DocumentType) -> str | None:
    """Return the document default language code, or None if unset."""
    styles = doc.styles.element
    langs = styles.xpath("./w:docDefaults/w:rPrDefault/w:rPr/w:lang")
    if not langs:
        return None
    return langs[0].get(qn("w:val"))


def _is_fake_heading(paragraph: Paragraph, next_text: str) -> bool:
    """Heuristic: short, bold, unstyled, no terminal punctuation, followed by body text."""
    text = paragraph.text.strip()
    if not text or len(text.split()) > _MAX_HEADING_WORDS or text[-1] in ".!?;:":
        return False
    name = style_name(paragraph)
    if _heading_level(name) is not None or name == "Title":
        return False
    runs = [r for r in paragraph.runs if r.text.strip()]
    if not runs:
        return False
    style_bold = paragraph.style.font.bold if paragraph.style is not None else None
    bold = all(r.bold or (r.font.bold is None and style_bold) for r in runs)
    return bool(bold) and bool(next_text.strip())


def scan(path: Path) -> Report:
    """Scan one .docx file and return a routed report.

    Args:
        path: Path to the document.

    Returns:
        The report with findings, evaluated and not-evaluated criteria.
    """
    doc = Document(str(path))
    asset = path.name
    report = Report(asset=asset, format="docx", evaluated=EVALUATED, not_evaluated=NOT_EVALUATED)
    f = report.findings

    if not (doc.core_properties.title or "").strip():
        f.append(
            Finding(
                check="docx.missing-title",
                criterion="2.4.2 Page Titled",
                asset=asset,
                locator="core properties",
                evidence=(
                    "The document title property is empty; screen readers announce the file name."
                ),
                route=Route.AUTO_FIX,
                closure_required=Closure.AUTOMATICALLY_VERIFIED,
                confidence=Confidence.HIGH,
                fix_id="set-title",
            )
        )

    if _default_language(doc) is None:
        f.append(
            Finding(
                check="docx.missing-language",
                criterion="3.1.1 Language of Page",
                asset=asset,
                locator="document defaults",
                evidence="No default language is set, so a screen reader must guess pronunciation.",
                route=Route.AUTO_FIX,
                closure_required=Closure.AUTOMATICALLY_VERIFIED,
                confidence=Confidence.HIGH,
                fix_id="set-language",
            )
        )

    for doc_pr in doc.element.body.xpath(".//wp:docPr"):
        descr = doc_pr.get("descr")
        if not is_missing_or_placeholder(descr):
            continue
        name = doc_pr.get("name") or f"image {doc_pr.get('id')}"
        evidence = (
            "The image has no alt text."
            if not (descr or "").strip()
            else (
                "The alt text is a filename or an auto-generated phrase: "
                f"{(descr or '').strip()[:60]!r}."
            )
        )
        f.append(
            Finding(
                check="docx.image-missing-alt",
                criterion="1.1.1 Non-text Content",
                asset=asset,
                locator=name,
                evidence=evidence,
                route=Route.CONTENT_OWNER,
                closure_required=Closure.CONTENT_OWNER_VERIFIED,
                confidence=Confidence.HIGH,
                proposal=(
                    "Write one sentence saying what this image conveys in this course, or mark "
                    "it decorative if it conveys nothing. The tool cannot know which."
                ),
            )
        )

    paragraphs = doc.paragraphs
    levels: list[tuple[int, int]] = []
    for index, paragraph in enumerate(paragraphs):
        level = _heading_level(style_name(paragraph))
        if level is not None and paragraph.text.strip():
            levels.append((index, level))
            continue
        if level is not None:
            f.append(
                Finding(
                    check="docx.empty-heading",
                    criterion="2.4.6 Headings and Labels",
                    asset=asset,
                    locator=f"paragraph {index}",
                    evidence=(
                        f"A Heading {level} paragraph with no text; it is announced as an "
                        "empty heading."
                    ),
                    route=Route.CONTENT_OWNER,
                    closure_required=Closure.CONTENT_OWNER_VERIFIED,
                    confidence=Confidence.HIGH,
                    proposal="Delete the empty heading, or give it the section's title.",
                )
            )
            continue
        next_text = paragraphs[index + 1].text if index + 1 < len(paragraphs) else ""
        if _is_fake_heading(paragraph, next_text):
            f.append(
                Finding(
                    check="docx.fake-heading",
                    criterion="1.3.1 Info and Relationships",
                    asset=asset,
                    locator=f"paragraph {index}",
                    evidence=(
                        "Bold text that reads as a heading but is styled as body: "
                        f"{paragraph.text.strip()[:60]!r}"
                    ),
                    route=Route.CONTENT_OWNER,
                    closure_required=Closure.CONTENT_OWNER_VERIFIED,
                    confidence=Confidence.MEDIUM,
                    fix_id=f"apply-heading:{index}:2",
                    proposal=(
                        "If this is a section heading, apply a Heading style at the right level."
                    ),
                )
            )

    body_paragraphs = sum(1 for p in paragraphs if p.text.strip())
    if not levels and body_paragraphs >= 15:
        f.append(
            Finding(
                check="docx.no-headings",
                criterion="2.4.6 Headings and Labels",
                asset=asset,
                locator="document",
                evidence=(
                    f"{body_paragraphs} paragraphs and no heading styles; the document cannot "
                    "be navigated by structure."
                ),
                route=Route.CONTENT_OWNER,
                closure_required=Closure.CONTENT_OWNER_VERIFIED,
                confidence=Confidence.MEDIUM,
                proposal=(
                    "Apply Heading styles to the section titles. The tool cannot decide which "
                    "lines are sections."
                ),
            )
        )

    previous = 0
    for index, level in levels:
        if previous and level > previous + 1:
            f.append(
                Finding(
                    check="docx.heading-skip",
                    criterion="1.3.1 Info and Relationships",
                    asset=asset,
                    locator=f"paragraph {index}",
                    evidence=f"Heading level jumps from {previous} to {level}.",
                    route=Route.CONTENT_OWNER,
                    closure_required=Closure.CONTENT_OWNER_VERIFIED,
                    confidence=Confidence.MEDIUM,
                    proposal=f"Use Heading {previous + 1} here, or restructure the sections above.",
                )
            )
        previous = level

    for t_index, table in enumerate(doc.tables):
        if not table.rows:
            continue
        if table.rows[0]._tr.xpath("./w:trPr/w:tblHeader"):
            continue
        f.append(
            Finding(
                check="docx.table-no-header",
                criterion="1.3.1 Info and Relationships",
                asset=asset,
                locator=f"table {t_index}",
                evidence=(
                    "No row is marked as a header row, so cells are read without their column "
                    "names."
                ),
                route=Route.CONTENT_OWNER,
                closure_required=Closure.CONTENT_OWNER_VERIFIED,
                confidence=Confidence.HIGH,
                fix_id=f"mark-header-row:{t_index}",
                proposal=(
                    "If the first row holds column names, mark it as a repeating header row. "
                    "If the table is used for layout, convert it to text."
                ),
            )
        )

    for h_index, link in enumerate(doc.element.body.xpath(".//w:hyperlink")):
        text = "".join(t.text or "" for t in link.xpath(".//w:t")).strip()
        lowered = text.lower()
        if lowered in GENERIC_LINK_TEXT or lowered.startswith(("http://", "https://", "www.")):
            f.append(
                Finding(
                    check="docx.link-text",
                    criterion="2.4.4 Link Purpose (In Context)",
                    asset=asset,
                    locator=f"hyperlink {h_index}",
                    evidence=f"Link text is {text[:60]!r}, which does not say where it goes.",
                    route=Route.CONTENT_OWNER,
                    closure_required=Closure.CONTENT_OWNER_VERIFIED,
                    confidence=Confidence.HIGH,
                    proposal=(
                        "Replace the link text with the name of the destination, e.g. the page "
                        "or document title."
                    ),
                )
            )

    return report
