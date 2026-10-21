"""Generate fictional course files with known defects.

Used by the tests, by the live demo, and by anyone who wants to see what the
tool does without pointing it at a real file. Nothing here is a real course, a
real person, or a real institution.
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.util import Inches
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    ContentStream,
    DecodedStreamObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

# A 1x1 transparent PNG, so no image file has to ship with the package.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _add_hyperlink(paragraph, url: str, text: str) -> None:  # type: ignore[no-untyped-def]
    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = text
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def make_bad_docx(path: Path, section: int = 1) -> Path:
    """Write a syllabus with one of every defect the Word checks look for.

    Args:
        path: Where to write the file.
        section: A number that varies the text so two files are not identical.

    Returns:
        The path written.
    """
    doc = Document()
    doc.core_properties.title = ""
    for lang in doc.styles.element.xpath("./w:docDefaults/w:rPrDefault/w:rPr/w:lang"):
        lang.getparent().remove(lang)

    doc.add_paragraph(f"Introduction to Campus Studies, section {section:02d}. Fall term.")
    fake = doc.add_paragraph()
    fake.add_run("Course Policies").bold = True
    doc.add_paragraph(
        "Attendance is expected. Late work loses one letter grade per day unless an "
        "extension is agreed in advance."
    )
    doc.add_picture(BytesIO(PNG_1X1))
    doc.add_paragraph("Figure: the campus map used for the field exercise.")

    table = doc.add_table(rows=3, cols=3)
    for col, text in enumerate(("Week", "Topic", "Reading")):
        table.cell(0, col).text = text
    table.cell(1, 0).text = "1"
    table.cell(1, 1).text = "Orientation"
    table.cell(1, 2).text = "Chapter 1"
    table.cell(2, 0).text = "2"
    table.cell(2, 1).text = "The campus as a system"
    table.cell(2, 2).text = "Chapter 2"

    doc.add_heading("Grading", level=1)
    doc.add_heading("", level=2)
    doc.add_heading("Participation", level=3)
    doc.add_paragraph("Twenty percent of the grade.")

    link_paragraph = doc.add_paragraph("The full policy is online: ")
    _add_hyperlink(link_paragraph, "https://example.edu/policies/late-work", "click here")

    doc.save(str(path))
    return path


def make_bad_pptx(path: Path) -> Path:
    """Write a deck with an untitled slide, a picture without alt text, and a headerless table.

    Args:
        path: Where to write the file.

    Returns:
        The path written.
    """
    prs = Presentation()
    prs.core_properties.title = ""

    titled = prs.slides.add_slide(prs.slide_layouts[5])
    titled.shapes.title.text = "Week 1: Orientation"
    table = titled.shapes.add_table(3, 2, Inches(1), Inches(2), Inches(6), Inches(2)).table
    table.first_row = False
    table.cell(0, 0).text = "Day"
    table.cell(0, 1).text = "Activity"
    table.cell(1, 0).text = "Monday"
    table.cell(1, 1).text = "Campus walk"
    table.cell(2, 0).text = "Wednesday"
    table.cell(2, 1).text = "Library session"

    blank = prs.slides.add_slide(prs.slide_layouts[6])
    blank.shapes.add_picture(BytesIO(PNG_1X1), Inches(1), Inches(1), Inches(2), Inches(2))

    prs.save(str(path))
    return path


def make_bad_pdf(path: Path) -> Path:
    """Write an untagged PDF with no title and no language.

    Args:
        path: Where to write the file.

    Returns:
        The path written.
    """
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    content = ContentStream(None, writer)
    content.set_data(
        b"BT /F1 16 Tf 72 720 Td (Week 1 reading list) Tj ET\n"
        b"BT /F1 12 Tf 72 682 Td (Chapter 1, pages 1 to 24.) Tj ET\n"
        b"BT /F1 12 Tf 72 662 Td (Chapter 2, pages 25 to 51.) Tj ET\n"
    )
    page.replace_contents(content)
    with path.open("wb") as handle:
        writer.write(handle)
    return path


def make_unstructured_docx(path: Path) -> Path:
    """Write a long handout with a title and a language but no headings at all.

    Args:
        path: Where to write the file.

    Returns:
        The path written.
    """
    doc = Document()
    doc.core_properties.title = "Field exercise handout"
    for lang in doc.styles.element.xpath("./w:docDefaults/w:rPrDefault/w:rPr/w:lang"):
        lang.set(qn("w:val"), "en-US")
    for week in range(1, 17):
        doc.add_paragraph(
            f"Week {week}. Walk the assigned route, note three features of the built "
            "environment, and bring the notes to the next session."
        )
    doc.save(str(path))
    return path


def make_scanned_pdf(path: Path) -> Path:
    """Write a PDF whose only page is a picture: no text a screen reader could read.

    Args:
        path: Where to write the file.

    Returns:
        The path written.
    """
    from PIL import Image  # Pillow arrives with python-pptx

    fixed = "D:20261019000000Z"
    Image.new("RGB", (200, 260), "white").save(
        path, "PDF", resolution=72.0, creationDate=fixed, modDate=fixed
    )
    return path


def _field(
    kind: str, name: str, rect: tuple[int, int, int, int], tooltip: str = ""
) -> DictionaryObject:
    """A form field that is also its own widget, as most exporters write them."""
    field = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/FT"): NameObject(kind),
            NameObject("/T"): TextStringObject(name),
            NameObject("/Rect"): ArrayObject([FloatObject(v) for v in rect]),
        }
    )
    if tooltip:
        field[NameObject("/TU")] = TextStringObject(tooltip)
    return field


def make_worksheet_pdf(path: Path) -> Path:
    """Write an untagged two-page worksheet with a picture and fill-in fields.

    The title and language are set, so only the page-by-page checks fire. Both
    pages share one resource dictionary that holds the picture, as WeasyPrint
    writes it, but only page 1 draws it: page 2 must not be reported as having a
    picture. Page 2 has two fields with no tooltip and one with a tooltip.

    Args:
        path: Where to write the file.

    Returns:
        The path written.
    """
    writer = PdfWriter()
    writer.add_metadata({"/Title": "Field observation worksheet"})
    writer.root_object[NameObject("/Lang")] = TextStringObject("en-US")
    picture = DecodedStreamObject()
    picture.set_data(b"\x80")
    picture.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(1),
            NameObject("/Height"): NumberObject(1),
            NameObject("/ColorSpace"): NameObject("/DeviceGray"),
            NameObject("/BitsPerComponent"): NumberObject(8),
        }
    )
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    resources = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
                NameObject("/XObject"): DictionaryObject(
                    {NameObject("/Im0"): writer._add_object(picture)}
                ),
            }
        )
    )
    pages = (
        b"BT /F1 16 Tf 72 720 Td (Field observation worksheet) Tj ET\n"
        b"q 200 0 0 120 72 560 cm /Im0 Do Q\n",
        b"BT /F1 12 Tf 72 720 Td (Site name) Tj ET\n"
        b"BT /F1 12 Tf 72 680 Td (Weather) Tj ET\n"
        b"BT /F1 12 Tf 72 640 Td (Consent script read) Tj ET\n",
    )
    for data in pages:
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = resources
        content = ContentStream(None, writer)
        content.set_data(data)
        page.replace_contents(content)
    fields = [
        _field("/Tx", "Text Field0", (200, 712, 500, 732)),
        _field("/Tx", "Text Field1", (200, 672, 500, 692)),
        _field("/Btn", "Check Box0", (250, 632, 266, 648), tooltip="Consent script read"),
    ]
    refs = [writer._add_object(field) for field in fields]
    writer.pages[1][NameObject("/Annots")] = ArrayObject(refs)
    writer.root_object[NameObject("/AcroForm")] = DictionaryObject(
        {NameObject("/Fields"): ArrayObject(refs)}
    )
    with path.open("wb") as handle:
        writer.write(handle)
    return path


def make_test_set(directory: Path) -> list[Path]:
    """The demo pile plus one file for each check the demo does not trigger.

    Every check in ``rules/checks.json`` fires on at least one of these files; the
    skill's self-test and its expected results are built from them.

    Args:
        directory: Created if needed.

    Returns:
        The paths written, in a stable order.
    """
    return [
        *make_demo_set(directory),
        make_unstructured_docx(directory / "field_exercise_handout.docx"),
        make_scanned_pdf(directory / "scanned_article.pdf"),
        make_worksheet_pdf(directory / "observation_worksheet.pdf"),
    ]


def make_demo_set(directory: Path) -> list[Path]:
    """Write a small pile of files that exercises every check and the Route 5 aggregation.

    Args:
        directory: Created if needed.

    Returns:
        The paths written, in a stable order.
    """
    directory.mkdir(parents=True, exist_ok=True)
    return [
        make_bad_docx(directory / "syllabus_section_01.docx", section=1),
        make_bad_docx(directory / "syllabus_section_02.docx", section=2),
        make_bad_docx(directory / "syllabus_section_03.docx", section=3),
        make_bad_pptx(directory / "week_1_slides.pptx"),
        make_bad_pdf(directory / "week_1_reading_list.pdf"),
    ]
