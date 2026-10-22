"""show_asset's extraction: the picture a finding's locator points at, read-only."""

import hashlib
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from wcag_tool import assets, engine
from wcag_tool.demo import make_demo_set, make_worksheet_pdf

_PICTURE_CHECKS = ("image-missing-alt", "picture-untagged", "scanned-no-text")


def test_every_picture_finding_can_be_shown(tmp_path: Path) -> None:
    files = [*make_demo_set(tmp_path), make_worksheet_pdf(tmp_path / "worksheet.pdf")]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    shown = 0
    for path in files:
        for finding in engine.scan(path).findings:
            if not finding.check.endswith(_PICTURE_CHECKS):
                continue
            for picture in assets.extract(path, finding.locator):
                with Image.open(BytesIO(picture.data)) as image:
                    assert max(image.size) <= assets.MAX_SIDE
                shown += 1
    assert shown >= 5
    # Read-only: every file is unchanged and nothing new was written.
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files} == before
    assert sorted(tmp_path.iterdir()) == sorted(files)


def test_a_pdf_page_returns_only_the_pictures_it_draws(tmp_path: Path) -> None:
    # Both pages share one resource list naming the picture; only page 1 draws it.
    path = make_worksheet_pdf(tmp_path / "worksheet.pdf")
    pictures = assets.extract(path, "page 1")
    assert [p.label for p in pictures] == ["page 1, picture 1 of 1"]
    with pytest.raises(assets.AssetError, match="No picture is drawn on page 2"):
        assets.extract(path, "page 2")


def test_large_artwork_is_scaled_and_kept_under_the_size_limit() -> None:
    noise = Image.effect_noise((3000, 2000), 120).convert("RGB")
    raw = BytesIO()
    noise.save(raw, format="PNG")
    data, fmt = assets._encode(raw.getvalue(), "test")
    with Image.open(BytesIO(data)) as image:
        assert max(image.size) == assets.MAX_SIDE
    assert len(data) <= 5_000_000 and fmt in ("png", "jpeg")


@pytest.mark.parametrize(
    ("name", "locator", "message"),
    [
        ("syllabus_section_01.docx", "Picture 99", "No picture named"),
        ("week_1_slides.pptx", "slide 9, Picture 1", "has no slide 9"),
        ("week_1_slides.pptx", "Picture 1", "Expected a locator like 'slide 4"),
        ("week_1_reading_list.pdf", "page 7", "has pages 1 to 1"),
    ],
)
def test_a_locator_with_no_picture_says_why(
    tmp_path: Path, name: str, locator: str, message: str
) -> None:
    make_demo_set(tmp_path)
    with pytest.raises(assets.AssetError, match=message):
        assets.extract(tmp_path / name, locator)
