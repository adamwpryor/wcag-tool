"""Generate fictional course files with known defects.

Used by the tests, by the live demo, and by anyone who wants to see what the
tool does without pointing it at a real file. Nothing here is a real course, a
real person, or a real institution.
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import pymupdf
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pptx import Presentation
from pptx.util import Inches

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
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Week 1 reading list", fontsize=16)
    page.insert_text((72, 110), "Chapter 1, pages 1 to 24.")
    page.insert_text((72, 130), "Chapter 2, pages 25 to 51.")
    doc.save(str(path))
    doc.close()
    return path


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
