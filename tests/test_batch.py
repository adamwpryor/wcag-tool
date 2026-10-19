from pathlib import Path

from wcag_tool import engine
from wcag_tool.report import render_markdown


def test_scan_folder_aggregates_route_five(demo_dir: Path) -> None:
    batch = engine.scan_folder(demo_dir)
    assert len(batch.reports) == 5
    assert not batch.skipped
    systemic = {s.check for s in batch.systemic()}
    # Three of five files are the same syllabus template: its defects recur.
    assert {"docx.missing-title", "docx.missing-language", "docx.table-no-header"} <= systemic
    # A defect in one file is not systemic.
    assert "pdf.untagged" not in systemic
    for s in batch.systemic():
        assert s.files >= 3 and s.total == 5 and s.proposal


def test_scan_folder_skips_our_own_outputs_and_lock_files(demo_dir: Path) -> None:
    engine.fix(demo_dir / "syllabus_section_01.docx")
    (demo_dir / "~$syllabus_section_01.docx").write_bytes(b"lock")
    (demo_dir / "notes.txt").write_text("not a document", encoding="utf-8")
    paths = engine.iter_supported(demo_dir)
    names = {p.name for p in paths}
    assert "syllabus_section_01.remediated.docx" not in names
    assert "~$syllabus_section_01.docx" not in names
    assert "notes.txt" not in names
    assert len(paths) == 5


def test_markdown_has_the_skill_table_and_the_claim(demo_dir: Path) -> None:
    batch = engine.scan_folder(demo_dir)
    text = render_markdown(batch)
    assert (
        "| File | Finding | Criterion | Route | Owner (a name) | Closure needed | Draft? |" in text
    )
    assert "## Route 5: fix once at the source" in text
    assert "## Not evaluated" in text
    assert "not a conformance claim" in text
    assert "This is a triage, not a conformance review" in text
    assert "compliant" not in text.lower()


def test_batch_dict_carries_markdown(demo_dir: Path) -> None:
    data = engine.scan_folder(demo_dir).to_dict()
    assert data["files"] == 5
    assert data["markdown"].startswith("# Triage: 5 files")
    assert data["systemic"] and all(s["route"] == 5 for s in data["systemic"])


def test_scan_many_records_unreadable_files(tmp_path: Path) -> None:
    broken = tmp_path / "broken.docx"
    broken.write_bytes(b"this is not a zip")
    missing = tmp_path / "missing.pptx"
    batch = engine.scan_many([broken, missing])
    assert not batch.reports
    assert {s["path"] for s in batch.skipped} == {str(broken), str(missing)}
