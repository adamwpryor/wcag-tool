from pathlib import Path

import pytest

from wcag_tool.demo import make_bad_docx, make_bad_pdf, make_bad_pptx, make_demo_set


@pytest.fixture
def bad_docx(tmp_path: Path) -> Path:
    return make_bad_docx(tmp_path / "bad_syllabus.docx")


@pytest.fixture
def bad_pptx(tmp_path: Path) -> Path:
    return make_bad_pptx(tmp_path / "bad_deck.pptx")


@pytest.fixture
def bad_pdf(tmp_path: Path) -> Path:
    return make_bad_pdf(tmp_path / "bad_reading.pdf")


@pytest.fixture
def demo_dir(tmp_path: Path) -> Path:
    make_demo_set(tmp_path / "pile")
    return tmp_path / "pile"
