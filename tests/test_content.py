"""extract_content: every page's words and objects, under the scan's place names, read-only."""

import hashlib
from pathlib import Path

import pytest

from wcag_tool import content, engine
from wcag_tool.course_pack import make_course_pack
from wcag_tool.demo import make_worksheet_pdf
from wcag_tool.report import _where


@pytest.fixture(scope="module")
def pack(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    folder = tmp_path_factory.mktemp("pack")
    return {p.name: p for p in make_course_pack(folder)}


def _blocks(data: dict) -> list[dict]:
    return [b for unit in data["units"] for b in unit["blocks"]]


def test_word_places_match_the_scan(pack: dict[str, Path]) -> None:
    path = pack["ENVS210_Syllabus_Fall2026.docx"]
    blocks = _blocks(content.extract(path))
    by_place = {b["where"]: b for b in blocks}
    # Every paragraph, table and picture the scan names is a block with the same place.
    for finding in engine.scan(path).findings:
        where = _where(finding.locator)
        if where.startswith(("Paragraph", "Table", "Picture")):
            assert where in by_place, where
    assert by_place["Paragraph 14"]["text"] == "Course Policies"
    assert by_place["Paragraph 14"]["bold"] is True
    assert by_place["Paragraph 12"] == {
        "kind": "heading",
        "where": "Paragraph 12",
        "text": "Required Materials",
        "level": 3,
    }
    links = [link for b in blocks for link in b.get("links", [])]
    assert {"click here", "here"} <= {link["text"] for link in links}
    assert all(link["where"].startswith("Link ") for link in links)
    tables = [b for b in blocks if b["kind"] == "table"]
    assert len(tables) == 3 and not any(t["header_row_marked"] for t in tables)


def test_slides_carry_their_notes_and_pictures(pack: dict[str, Path]) -> None:
    units = content.extract(pack["ENVS210_Week03_Lecture.pptx"])["units"]
    slide4 = units[3]
    assert slide4["unit"] == "slide 4"
    kinds = {b["kind"]: b for b in slide4["blocks"]}
    assert kinds["heading"]["text"] == "Thursday's route"
    assert kinds["picture"]["alt"] == "IMG_2041.png"
    assert "red line" in kinds["notes"]["text"]


def test_pdf_pages_report_words_pictures_and_fields(tmp_path: Path) -> None:
    path = make_worksheet_pdf(tmp_path / "worksheet.pdf")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    data = content.extract(path)
    assert data["settings"] == {
        "title": "Field observation worksheet",
        "language": "en-US",
        "tagged": False,
    }
    page1, page2 = data["units"]
    assert {"kind": "pictures", "where": "page 1", "count": 1} in page1["blocks"]
    fields = [b for b in page2["blocks"] if b["kind"] == "field"]
    assert [f["tooltip"] for f in fields] == [None, None, "Consent script read"]
    assert not [b for b in page2["blocks"] if b["kind"] == "pictures"]
    # An untagged PDF has text, not headings: nothing guesses a role the file does not mark.
    assert not [b for b in _blocks(data) if b["kind"] == "heading"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["worksheet.pdf"]
