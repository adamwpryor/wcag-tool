"""Checks and fixes for PDF files.

The honest position on PDF: open-source tooling can read whether a file is
tagged and can set its metadata, but it cannot build a tag tree. An untagged PDF
is routed back to its source document for re-export, or to a person with Acrobat.
The tool says so instead of implying it fixed the file.

Built on ``pypdf`` (BSD licensed), so the checks can ship inside a shared skill.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, PdfObject, TextStringObject

from wcag_tool import rules
from wcag_tool.findings import Finding, Report

# Both lists come from rules/coverage.json; edit them there.
EVALUATED = rules.load().evaluated("pdf")
NOT_EVALUATED = rules.load().not_evaluated("pdf")

_SAMPLE_PAGES = 3


def _resolve(value: PdfObject | None) -> PdfObject | None:
    return value.get_object() if value is not None else None


def _is_tagged(reader: PdfReader) -> bool:
    mark_info = _resolve(reader.root_object.get("/MarkInfo"))
    if not isinstance(mark_info, DictionaryObject):
        return False
    return bool(_resolve(mark_info.get("/Marked")))


def _language(reader: PdfReader) -> str | None:
    lang = _resolve(reader.root_object.get("/Lang"))
    text = str(lang).strip() if lang is not None else ""
    return text or None


def _image_count(page: DictionaryObject) -> int:
    """Count image XObjects on a page without decoding them."""
    resources = _resolve(page.get("/Resources"))
    if not isinstance(resources, DictionaryObject):
        return 0
    xobjects = _resolve(resources.get("/XObject"))
    if not isinstance(xobjects, DictionaryObject):
        return 0
    count = 0
    for ref in xobjects.values():
        xobject = _resolve(ref)
        if isinstance(xobject, DictionaryObject) and xobject.get("/Subtype") == "/Image":
            count += 1
    return count


def scan(path: Path) -> Report:
    """Scan one PDF and return a routed report.

    Args:
        path: Path to the PDF.

    Returns:
        The report.
    """
    reader = PdfReader(str(path))
    asset = path.name
    report = Report.for_format(asset, "pdf")
    f = report.findings

    title = reader.metadata.title if reader.metadata is not None else None
    if not (title or "").strip():
        f.append(
            Finding.from_check(
                "pdf.missing-title",
                asset=asset,
                locator="document info",
                evidence="The title metadata is empty; readers announce the file name.",
            )
        )
    if _language(reader) is None:
        f.append(
            Finding.from_check(
                "pdf.missing-language",
                asset=asset,
                locator="document catalog",
                evidence="No document language is set.",
            )
        )
    if not _is_tagged(reader):
        f.append(
            Finding.from_check(
                "pdf.untagged",
                asset=asset,
                locator="document",
                evidence=(
                    "The PDF has no tag structure. A screen reader gets a stream of text with "
                    "no headings, lists or tables."
                ),
            )
        )

    pages = reader.pages[:_SAMPLE_PAGES]
    if pages:
        text_chars = sum(len((page.extract_text() or "").strip()) for page in pages)
        image_count = sum(_image_count(page) for page in pages)
        if text_chars == 0 and image_count > 0:
            f.append(
                Finding.from_check(
                    "pdf.scanned-no-text",
                    asset=asset,
                    locator=f"pages 1-{len(pages)}",
                    evidence=(
                        "Pages are images with no extractable text. A screen reader gets nothing."
                    ),
                )
            )
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
    writer = PdfWriter(clone_from=str(path))
    applied: dict[str, str] = {}
    failed: dict[str, str] = {}
    for fix_id in fix_ids:
        if fix_id == "set-title":
            title = path.stem.replace("_", " ").replace("-", " ")
            writer.add_metadata({"/Title": title})
            applied[fix_id] = (
                f"title set to {title!r} from the file name; check it reads as a title"
            )
        elif fix_id == "set-language":
            writer.root_object[NameObject("/Lang")] = TextStringObject(language)
            applied[fix_id] = f"language set to {language}"
        else:
            failed[fix_id] = "unknown fix"
    with output.open("wb") as handle:
        writer.write(handle)
    return {"applied": applied, "failed": failed}
