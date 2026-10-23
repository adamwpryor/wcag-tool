"""Checks and fixes for PDF files.

The honest position on PDF: open-source tooling can read whether a file is
tagged and can set its metadata, but it cannot build a tag tree. An untagged PDF
is routed back to its source document for re-export, or to a person with Acrobat.
The tool says so instead of implying it fixed the file.

Built on ``pypdf`` (BSD licensed), so the checks can ship inside a shared skill.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter
from pypdf.errors import PdfReadError
from pypdf.generic import (
    ArrayObject,
    ContentStream,
    DictionaryObject,
    IndirectObject,
    NameObject,
    PdfObject,
    StreamObject,
    TextStringObject,
)

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


def _drawn_images(
    reader: PdfReader, owner: PdfObject | None, resources: PdfObject | None, seen: set[int]
) -> list[int | None]:
    """The images a content stream actually draws, following form XObjects.

    Reading the resource dictionary is not enough: some exporters (WeasyPrint is
    one) give every page the same dictionary, so each page would appear to hold
    every picture in the file.

    Returns:
        One entry per image drawn, in drawing order: its object number, or None for
        an image that is not an indirect object.
    """
    resources = _resolve(resources)
    if not isinstance(resources, DictionaryObject):
        return []
    xobjects = _resolve(resources.get("/XObject"))
    if owner is None or not isinstance(xobjects, DictionaryObject):
        return []
    try:
        operations = ContentStream(owner, reader).operations
    except (PdfReadError, ValueError):
        return []
    drawn: list[int | None] = []
    for operands, operator in operations:
        if operator != b"Do" or not operands or operands[0] not in xobjects:
            continue
        ref = xobjects.raw_get(operands[0])
        xobject = _resolve(ref)
        if not isinstance(xobject, StreamObject):
            continue
        if xobject.get("/Subtype") == "/Image":
            drawn.append(ref.idnum if isinstance(ref, IndirectObject) else None)
        elif xobject.get("/Subtype") == "/Form" and id(xobject) not in seen:
            seen.add(id(xobject))
            drawn += _drawn_images(reader, xobject, xobject.get("/Resources") or resources, seen)
    return drawn


def drawn_images(reader: PdfReader, page: PageObject) -> list[int | None]:
    """The images one page draws, in order, by object number.

    Args:
        reader: The open PDF.
        page: One of its pages.

    Returns:
        One entry per image drawn; None for an image that is not an indirect object.
    """
    return _drawn_images(reader, page.get_contents(), page.get("/Resources"), set())


def _unnamed_fields(page: PageObject) -> list[str]:
    """The internal names of a page's form fields that carry no tooltip.

    The tooltip (``/TU``) is what a screen reader announces for a field. Without it,
    readers fall back to the internal name, such as "Text Field0", or to nothing.
    """
    unnamed: list[str] = []
    annotations = _resolve(page.get("/Annots"))
    if not isinstance(annotations, ArrayObject):
        return unnamed
    for ref in annotations:
        widget = _resolve(ref)
        if not isinstance(widget, DictionaryObject) or widget.get("/Subtype") != "/Widget":
            continue
        field: DictionaryObject | None = widget
        name = tooltip = None
        while isinstance(field, DictionaryObject):
            name = name or field.get("/T")
            tooltip = tooltip or field.get("/TU")
            field = _resolve(field.get("/Parent"))  # type: ignore[assignment]
        if not str(tooltip or "").strip():
            unnamed.append(str(name or "unnamed"))
    return unnamed


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
    tagged = _is_tagged(reader)
    if not tagged:
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

    # Page by page, so the person can work through the file in order. A page with no
    # text is a scan, which pdf.scanned-no-text already covers.
    for number, page in enumerate(reader.pages, start=1):
        if not tagged and (page.extract_text() or "").strip():
            pictures = len(drawn_images(reader, page))
            if pictures:
                f.append(
                    Finding.from_check(
                        "pdf.picture-untagged",
                        asset=asset,
                        locator=f"page {number}",
                        evidence=(
                            f"{pictures} picture{'s' if pictures > 1 else ''} on this page. The "
                            "file has no tags, so no picture can carry alt text or be marked "
                            "decorative."
                        ),
                    )
                )
        unnamed = _unnamed_fields(page)
        if unnamed:
            shown = ", ".join(repr(name) for name in unnamed[:3])
            more = f" and {len(unnamed) - 3} more" if len(unnamed) > 3 else ""
            f.append(
                Finding.from_check(
                    "pdf.form-field-no-name",
                    asset=asset,
                    locator=f"page {number}",
                    evidence=(
                        f"{len(unnamed)} fill-in field{'s' if len(unnamed) > 1 else ''} with no "
                        f"tooltip; a screen reader announces the internal name: {shown}{more}."
                    ),
                )
            )
    return report


def apply(
    path: Path,
    fix_ids: list[str],
    output: Path,
    language: str = "en-US",
    title: str | None = None,
) -> dict:
    """Apply the named metadata fixes and save to ``output``.

    Args:
        path: The original PDF. Never overwritten.
        fix_ids: ``set-title`` and ``set-language`` are the only fixes that exist for PDF.
        output: Where the copy is written.
        language: Language code used by ``set-language``.
        title: The title a person named for ``set-title``; without one, it is taken from
            the file name and the note says so.

    Returns:
        A dict with ``applied`` and ``failed``.
    """
    writer = PdfWriter(clone_from=str(path))
    applied: dict[str, str] = {}
    failed: dict[str, str] = {}
    for fix_id in fix_ids:
        if fix_id == "set-title" and title:
            writer.add_metadata({"/Title": title})
            applied[fix_id] = f"title set to {title!r}, as named"
        elif fix_id == "set-title":
            guessed = path.stem.replace("_", " ").replace("-", " ")
            writer.add_metadata({"/Title": guessed})
            applied[fix_id] = (
                f"title set to {guessed!r} from the file name; check it names the whole document"
            )
        elif fix_id == "set-language":
            writer.root_object[NameObject("/Lang")] = TextStringObject(language)
            applied[fix_id] = f"language set to {language}"
        else:
            failed[fix_id] = "unknown fix"
    with output.open("wb") as handle:
        writer.write(handle)
    return {"applied": applied, "failed": failed}
