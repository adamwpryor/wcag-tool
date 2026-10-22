import re
from pathlib import Path

from wcag_tool import engine
from wcag_tool.demo import make_worksheet_pdf
from wcag_tool.report import render_markdown, render_worklist, worklist_fields


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
        "| File | Finding | Criterion | Route | Owner (a name) | Closure needed | Next step |"
        in text
    )
    assert "ask author what it shows" in text
    assert "confirm, then apply" in text
    assert "## Route 5: fix once at the source" in text
    assert "## Not evaluated" in text
    assert "not a conformance claim" in text
    assert "This is a triage, not a conformance review" in text
    assert "compliant" not in text.lower()


def test_batch_dict_carries_markdown(demo_dir: Path) -> None:
    data = engine.scan_folder(demo_dir).to_dict()
    assert data["files"] == 5
    assert data["formats"] == {"docx": 3, "pptx": 1, "pdf": 1}
    assert data["evaluated"] and data["not_evaluated"]
    header = data["markdown"].splitlines()[0]
    assert header.startswith("# Triage: 5 files (")
    assert "3 docx" in header and "1 pptx" in header and "1 pdf" in header
    assert data["systemic"] and all(s["route"] == 5 for s in data["systemic"])


_PARTS = (
    "**1 · Entire document**",
    "**2 · Page by page**",
    "**3 · Pictures, in order**",
    "**4 · Fill-in fields**",
    "**5 · Check your work**",
    "**6 · Try it with a screen reader**",
)


def test_worklist_is_the_six_part_template_in_plain_words(demo_dir: Path) -> None:
    worksheet = make_worksheet_pdf(demo_dir / "observation_worksheet.pdf")
    batch = engine.scan_folder(demo_dir)
    text = render_worklist(batch)
    # Every file gets every part, in order.
    for report in batch.reports:
        block = text.split(f"**`{report.asset}`**", 1)[1].split("**`", 1)[0]
        positions = [block.index(part) for part in _PARTS]
        assert positions == sorted(positions), report.asset
    # The person never reads a route, a check id or a fix id.
    assert "Route" not in text and "route" not in text
    assert not re.search(r"\b(docx|pptx|pdf)\.[a-z-]+", text)
    for fix_id in ("set-title", "set-language", "mark-header-row", "apply-heading"):
        assert fix_id not in text, fix_id
    assert "compliant" not in text.lower()
    # Numbers run straight through and match the map an agent uses to apply fixes.
    numbers = [int(n) for n in re.findall(r"^(\d+)\. ", text, re.M)]
    items = worklist_fields(batch)["worklist_items"]
    assert numbers == list(range(1, len(numbers) + 1)) == [i["number"] for i in items]
    assert any(i["fix_id"] == "set-title" for i in items)
    # The worksheet's picture and fields land in their parts, on their pages.
    block = text.split(f"**`{worksheet.name}`**", 1)[1]
    pictures = block.split("**3 · Pictures, in order**", 1)[1].split("**4 ·", 1)[0]
    fields = block.split("**4 · Fill-in fields**", 1)[1].split("**5 ·", 1)[0]
    assert "**Page 1:** 1 picture on this page." in pictures
    assert "**Page 2:** 2 fill-in fields" in fields


def test_scan_many_records_unreadable_files(tmp_path: Path) -> None:
    broken = tmp_path / "broken.docx"
    broken.write_bytes(b"this is not a zip")
    missing = tmp_path / "missing.pptx"
    batch = engine.scan_many([broken, missing])
    assert not batch.reports
    assert {s["path"] for s in batch.skipped} == {str(broken), str(missing)}
