"""The realistic course pack: the defects it is built to carry fire, and nothing else does."""

from collections import Counter
from pathlib import Path

from wcag_tool import engine
from wcag_tool.course_pack import make_course_pack


def test_course_pack_trips_the_checks_it_is_built_for(tmp_path: Path) -> None:
    paths = make_course_pack(tmp_path)
    found = {p.name: Counter(f.check for f in engine.scan(p).findings) for p in paths}
    assert found["ENVS210_Syllabus_Fall2026.docx"] == Counter(
        {
            "docx.table-no-header": 3,
            "docx.link-text": 3,
            "docx.fake-heading": 2,
            "docx.missing-title": 1,
            "docx.missing-language": 1,
            "docx.image-missing-alt": 1,
            "docx.heading-skip": 1,
            "docx.empty-heading": 1,
        }
    )
    assert found["ENVS210_Week03_Lecture.pptx"] == Counter(
        {
            "pptx.image-missing-alt": 3,
            "pptx.missing-title": 1,
            "pptx.slide-no-title": 1,
            "pptx.table-no-header": 1,
        }
    )
    # Title and language set, and a picture with real alt text: only the structure is missing.
    assert found["Field_Journal_Guidelines.docx"] == Counter({"docx.no-headings": 1})
    assert found["Week03_Reading_List.pdf"] == Counter(
        {"pdf.missing-title": 1, "pdf.missing-language": 1, "pdf.untagged": 1}
    )
    assert found["Course_Reader_Ch3_scan.pdf"]["pdf.scanned-no-text"] == 1


def test_course_pack_fake_headings_include_the_one_the_evals_name(tmp_path: Path) -> None:
    syllabus = make_course_pack(tmp_path)[0]
    evidence = [
        f.evidence for f in engine.scan(syllabus).findings if f.check == "docx.fake-heading"
    ]
    assert any("'Course Policies'" in e for e in evidence)
