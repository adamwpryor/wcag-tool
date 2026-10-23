"""set-title: a named title is used exactly; a guessed one says where it came from."""

from pathlib import Path

import pytest
from docx import Document
from pptx import Presentation
from pypdf import PdfReader

from wcag_tool import engine


def _title(path: Path) -> str | None:
    if path.suffix == ".docx":
        return Document(str(path)).core_properties.title
    if path.suffix == ".pptx":
        return Presentation(str(path)).core_properties.title
    metadata = PdfReader(str(path)).metadata
    return metadata.title if metadata else None


@pytest.mark.parametrize("fixture", ["bad_docx", "bad_pptx", "bad_pdf"])
def test_a_named_title_is_used_exactly(fixture: str, request: pytest.FixtureRequest) -> None:
    path: Path = request.getfixturevalue(fixture)
    record = engine.fix(path, title="  ENVS 210 Syllabus, Fall 2026 ", language="en-US")
    assert record["title"] == "ENVS 210 Syllabus, Fall 2026"
    assert record["applied"]["set-title"] == "title set to 'ENVS 210 Syllabus, Fall 2026', as named"
    copy = Path(record["output"])
    assert _title(copy) == "ENVS 210 Syllabus, Fall 2026"
    assert not [f for f in record["after"]["findings"] if f["check"].endswith("missing-title")]


@pytest.mark.parametrize("fixture", ["bad_docx", "bad_pptx", "bad_pdf"])
def test_a_guessed_title_says_where_it_came_from(
    fixture: str, request: pytest.FixtureRequest
) -> None:
    path: Path = request.getfixturevalue(fixture)
    record = engine.fix(path)
    note = record["applied"]["set-title"]
    assert record["title"] is None
    assert " from " in note and "check it names the whole" in note
    assert "as named" not in note
