"""compare_rebuild: a rebuild checked against its original, with every loss reported."""

import shutil
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    DictionaryObject,
    NameObject,
    TextStringObject,
)

from wcag_tool.compare import CLAIM, compare
from wcag_tool.demo import make_bad_pdf, make_scanned_pdf, make_worksheet_pdf


def _rebuild(original: Path, out: Path, alt: bool = True, name_fields: bool = True) -> Path:
    """A stand-in for an agent's rebuild: the same content, tagged, with a figure and names."""
    writer = PdfWriter(clone_from=str(original))
    figure = DictionaryObject(
        {NameObject("/Type"): NameObject("/StructElem"), NameObject("/S"): NameObject("/Figure")}
    )
    if alt:
        figure[NameObject("/Alt")] = TextStringObject("A sample observation sketch")
    tree = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/StructTreeRoot"),
            NameObject("/K"): ArrayObject([writer._add_object(figure)]),
        }
    )
    writer.root_object[NameObject("/StructTreeRoot")] = writer._add_object(tree)
    writer.root_object[NameObject("/MarkInfo")] = DictionaryObject(
        {NameObject("/Marked"): BooleanObject(True)}
    )
    if name_fields:
        for ref in writer.pages[1]["/Annots"]:
            field = ref.get_object()
            if "/TU" not in field:
                field[NameObject("/TU")] = TextStringObject(str(field["/T"]))
    with out.open("wb") as handle:
        writer.write(handle)
    return out


@pytest.fixture
def original(tmp_path: Path) -> Path:
    return make_worksheet_pdf(tmp_path / "worksheet.pdf")


def test_a_faithful_tagged_rebuild_has_no_problems(original: Path, tmp_path: Path) -> None:
    result = compare(original, _rebuild(original, tmp_path / "worksheet.rebuilt.pdf"))
    assert result["problems"] == []
    assert result["words"]["original"] == result["words"]["rebuilt"] > 0
    assert result["pictures"] == {
        "original": 1,
        "rebuilt": 1,
        "figures_tagged": 1,
        "figures_without_alt": 0,
    }
    # Even with nothing found, the claim stays bounded.
    assert result["claim"] == CLAIM and "not a conformance claim" in CLAIM


def test_lost_words_are_reported_verbatim(original: Path, tmp_path: Path) -> None:
    other = make_bad_pdf(tmp_path / "other.pdf")
    result = compare(original, other)
    assert result["words"]["missing"] == [
        "Field observation worksheet Site name Weather Consent script read"
    ]
    assert any("missing from the rebuild" in p for p in result["problems"])
    assert any("1 picture and the rebuild 0" in p for p in result["problems"])
    assert any("3 fill-in fields and the rebuild 0" in p for p in result["problems"])


def test_an_untagged_or_unnamed_rebuild_is_caught(original: Path, tmp_path: Path) -> None:
    copy = tmp_path / "copy.pdf"
    shutil.copyfile(original, copy)
    problems = compare(original, copy)["problems"]
    assert any("2 fill-in fields in the rebuild with no name" in p for p in problems)
    assert any("scan of the rebuild still finds" in p for p in problems)
    no_alt = _rebuild(original, tmp_path / "no-alt.pdf", alt=False)
    assert "1 figure in the rebuild with no alt text." in compare(original, no_alt)["problems"]


def test_ignored_phrases_leave_both_sides(original: Path, tmp_path: Path) -> None:
    rebuilt = _rebuild(original, tmp_path / "worksheet.rebuilt.pdf")
    result = compare(original, rebuilt, ignore=["Consent script read"])
    assert result["problems"] == []
    assert result["words"]["original"] == 6 and result["words"]["ignored"] == [
        "Consent script read"
    ]


def test_a_scanned_original_needs_a_person(tmp_path: Path) -> None:
    scan = make_scanned_pdf(tmp_path / "scan.pdf")
    other = make_bad_pdf(tmp_path / "typed.pdf")
    problems = compare(scan, other)["problems"]
    assert problems[0].startswith("The original has no text to compare against")


def test_the_original_cannot_be_its_own_rebuild(original: Path) -> None:
    with pytest.raises(ValueError, match="separate rebuilt file"):
        compare(original, original)
