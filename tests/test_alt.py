import pytest

from wcag_tool.alt import is_missing_or_placeholder


@pytest.mark.parametrize(
    "descr",
    [
        None,
        "",
        "   ",
        "image.png",
        "IMG_4521.JPG",
        "Screenshot 2026-10-19.png",
        "Picture",
        "A picture containing text, whiteboard",
        "Diagram Description automatically generated",
    ],
)
def test_placeholders_count_as_missing(descr: str | None) -> None:
    assert is_missing_or_placeholder(descr)


@pytest.mark.parametrize(
    "descr",
    [
        "Bunsen burner with the air hole half open, blue flame.",
        "Enrollment rose from 1,200 to 1,900.",
    ],
)
def test_real_alt_text_passes(descr: str) -> None:
    assert not is_missing_or_placeholder(descr)
