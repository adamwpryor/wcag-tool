"""Checks and fixes for PDF files.

The honest position on PDF: open-source tooling can read whether a file is
tagged and can set its metadata, but it cannot build a tag tree. An untagged PDF
is routed back to its source document for re-export, or to a person with Acrobat.
The tool says so instead of implying it fixed the file.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

from wcag_tool.findings import Closure, Confidence, Finding, Report, Route

EVALUATED = [
    "1.3.1 Info and Relationships (the file is tagged at all)",
    "2.4.2 Page Titled (document title metadata)",
    "3.1.1 Language of Page (document language)",
    "Text is extractable (not a scanned image without OCR)",
]

NOT_EVALUATED = [
    "1.1.1 alt text on figures: requires walking the structure tree; not analyzed yet",
    "1.3.2 Meaningful Sequence: tag order vs visual order needs a person with a screen reader",
    "Tables, headings and bookmarks inside the tag tree: not analyzed yet",
    "1.4.3 Contrast: not analyzed yet",
]

_SAMPLE_PAGES = 3
_WRITABLE_METADATA = (
    "author",
    "creationDate",
    "creator",
    "keywords",
    "modDate",
    "producer",
    "subject",
    "title",
)


def _is_tagged(doc: pymupdf.Document) -> bool:
    catalog = doc.pdf_catalog()
    kind, value = doc.xref_get_key(catalog, "MarkInfo")
    return kind == "dict" and "/Marked true" in value


def _language(doc: pymupdf.Document) -> str | None:
    catalog = doc.pdf_catalog()
    kind, value = doc.xref_get_key(catalog, "Lang")
    if kind == "string" and value.strip():
        return value.strip("() ")
    return None


def scan(path: Path) -> Report:
    """Scan one PDF and return a routed report.

    Args:
        path: Path to the PDF.

    Returns:
        The report.
    """
    doc = pymupdf.open(str(path))
    asset = path.name
    report = Report(asset=asset, format="pdf", evaluated=EVALUATED, not_evaluated=NOT_EVALUATED)
    f = report.findings

    if not (doc.metadata.get("title") or "").strip():
        f.append(
            Finding(
                check="pdf.missing-title",
                criterion="2.4.2 Page Titled",
                asset=asset,
                locator="document info",
                evidence="The title metadata is empty; readers announce the file name.",
                route=Route.AUTO_FIX,
                closure_required=Closure.AUTOMATICALLY_VERIFIED,
                confidence=Confidence.HIGH,
                fix_id="set-title",
            )
        )
    if _language(doc) is None:
        f.append(
            Finding(
                check="pdf.missing-language",
                criterion="3.1.1 Language of Page",
                asset=asset,
                locator="document catalog",
                evidence="No document language is set.",
                route=Route.AUTO_FIX,
                closure_required=Closure.AUTOMATICALLY_VERIFIED,
                confidence=Confidence.HIGH,
                fix_id="set-language",
            )
        )
    if not _is_tagged(doc):
        f.append(
            Finding(
                check="pdf.untagged",
                criterion="1.3.1 Info and Relationships",
                asset=asset,
                locator="document",
                evidence=(
                    "The PDF has no tag structure. A screen reader gets a stream of text with "
                    "no headings, lists or tables."
                ),
                route=Route.CONTENT_OWNER,
                closure_required=Closure.EXPERT_VERIFIED,
                confidence=Confidence.HIGH,
                proposal=(
                    "Re-export from the source Word or PowerPoint file after fixing it there; the "
                    "export carries the tags. If there is no source, this file needs Acrobat's "
                    "auto-tag followed by a human check. This tool cannot build a tag tree."
                ),
            )
        )

    sampled = min(_SAMPLE_PAGES, doc.page_count)
    if sampled:
        text_chars = sum(len(doc[i].get_text().strip()) for i in range(sampled))
        image_count = sum(len(doc[i].get_images(full=False)) for i in range(sampled))
        if text_chars == 0 and image_count > 0:
            f.append(
                Finding(
                    check="pdf.scanned-no-text",
                    criterion="1.1.1 Non-text Content",
                    asset=asset,
                    locator=f"pages 1-{sampled}",
                    evidence=(
                        "Pages are images with no extractable text. A screen reader gets nothing."
                    ),
                    route=Route.CONTENT_OWNER,
                    closure_required=Closure.EXPERT_VERIFIED,
                    confidence=Confidence.HIGH,
                    proposal=(
                        "Find the original document, or run OCR and then check the recognized "
                        "text against the page."
                    ),
                )
            )
    doc.close()
    return report


def apply(path: Path, fix_ids: list[str], output: Path, language: str = "en-US") -> dict:
    """Apply the named metadata fixes and save to ``output``.

    Args:
        path: The original PDF. Never overwritten.
        fix_ids: ``set-title`` and ``set-language`` are the only fixes that exist for PDF.
        output: Where the copy is written.
        language: Language code used by ``set-language``.

    Returns:
        A dict with ``applied`` and ``failed``.
    """
    doc = pymupdf.open(str(path))
    applied: dict[str, str] = {}
    failed: dict[str, str] = {}
    for fix_id in fix_ids:
        if fix_id == "set-title":
            title = path.stem.replace("_", " ").replace("-", " ")
            current = doc.metadata or {}
            metadata = {k: current.get(k, "") for k in _WRITABLE_METADATA}
            metadata["title"] = title
            doc.set_metadata(metadata)
            applied[fix_id] = f"title set to {title!r}"
        elif fix_id == "set-language":
            doc.xref_set_key(doc.pdf_catalog(), "Lang", f"({language})")
            applied[fix_id] = f"language set to {language}"
        else:
            failed[fix_id] = "unknown fix"
    doc.save(str(output), garbage=0)
    doc.close()
    return {"applied": applied, "failed": failed}
