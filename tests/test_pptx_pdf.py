from pathlib import Path

import pytest

from wcag_tool import engine
from wcag_tool.demo import make_worksheet_pdf


def test_pptx_scan_and_fix(bad_pptx: Path) -> None:
    report = engine.scan(bad_pptx)
    checks = {f.check for f in report.findings}
    assert checks == {
        "pptx.missing-title",
        "pptx.slide-no-title",
        "pptx.image-missing-alt",
        "pptx.table-no-header",
    }
    record = engine.fix(bad_pptx)
    assert set(record["applied"]) == {"set-title"}
    after = {f["check"] for f in record["after"]["findings"]}
    assert after == {"pptx.slide-no-title", "pptx.image-missing-alt", "pptx.table-no-header"}
    header_fix = next(f.fix_id for f in report.findings if f.check == "pptx.table-no-header")
    record = engine.fix(bad_pptx, apply=[header_fix], overwrite=True)
    assert header_fix in record["applied"]
    after = {f["check"] for f in record["after"]["findings"]}
    assert "pptx.table-no-header" not in after


def test_pdf_scan_and_fix(bad_pdf: Path) -> None:
    report = engine.scan(bad_pdf)
    checks = {f.check for f in report.findings}
    assert checks == {"pdf.missing-title", "pdf.missing-language", "pdf.untagged"}
    untagged = next(f for f in report.findings if f.check == "pdf.untagged")
    assert untagged.fix_id is None, "the tool must never claim to tag a PDF"
    record = engine.fix(bad_pdf, language="es-ES")
    assert set(record["applied"]) == {"set-title", "set-language"}
    after = {f["check"] for f in record["after"]["findings"]}
    assert after == {"pdf.untagged"}


def test_pdf_pictures_and_fields_are_found_page_by_page(tmp_path: Path) -> None:
    path = make_worksheet_pdf(tmp_path / "observation_worksheet.pdf")
    found = [(f.check, f.locator) for f in engine.scan(path).findings]
    # Both pages share the resource dictionary holding the picture; only page 1 draws it.
    assert ("pdf.picture-untagged", "page 1") in found
    assert ("pdf.picture-untagged", "page 2") not in found
    fields = next(f for f in engine.scan(path).findings if f.check == "pdf.form-field-no-name")
    assert fields.locator == "page 2"
    # The checkbox has a tooltip, so only the two text fields are named.
    assert "'Text Field0', 'Text Field1'." in fields.evidence
    assert "Check Box0" not in fields.evidence
    assert fields.fix_id is None, "the tool never writes a field's name; the author does"


def test_unsupported_extension(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("hello", encoding="utf-8")
    with pytest.raises(engine.UnsupportedFormatError):
        engine.scan(path)


def test_report_shape(bad_pdf: Path) -> None:
    data = engine.scan(bad_pdf).to_dict()
    assert set(data) == {
        "asset",
        "format",
        "findings",
        "counts_by_route",
        "evaluated",
        "not_evaluated",
        "coverage",
        "criteria",
        "bounded_claim",
    }
    assert "not a conformance claim" in data["bounded_claim"]
    # Every finding's criterion arrives with W3C's own words and the Understanding link.
    assert set(data["criteria"]) == {f["criterion"].split()[0] for f in data["findings"]}
    assert all(c["text"] and c["understanding"] for c in data["criteria"].values())
