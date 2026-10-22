"""The agent eval's judge, against simulated agents: no model runs here."""

import json
import sys
from pathlib import Path

import pytest

from wcag_tool import engine
from wcag_tool.demo import make_bad_docx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import agent_eval  # noqa: E402

_CASES = {
    c["id"]: c
    for c in json.loads((ROOT / "skill" / "tests" / "evals.json").read_text(encoding="utf-8"))[
        "cases"
    ]
    if "agent" in c
}


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    course = tmp_path / "course"
    course.mkdir()
    make_bad_docx(course / "syllabus_section_01.docx")
    return course


def _fix_id(path: Path, kind: str) -> str:
    return next(
        f.fix_id for f in engine.scan(path).findings if f.fix_id and f.fix_id.startswith(kind)
    )


def test_every_agent_case_names_only_fixes_the_tool_offers() -> None:
    assert {"KAT-9", "KAT-10", "KAT-17"} <= set(_CASES)
    known = {"set-title", "set-language", "mark-header-row", "apply-heading"}
    for case in _CASES.values():
        agent = case["agent"]
        assert set(agent["allowed_fix_ids"]) <= known, case["id"]
        assert set(agent["required_fix_ids"]) <= set(agent["allowed_fix_ids"]), case["id"]


@pytest.mark.parametrize(
    ("case", "apply", "language"),
    [
        ("KAT-9", [], None),
        ("KAT-10", [], "en-US"),
        ("KAT-17", ["mark-header-row"], "en-US"),
    ],
)
def test_an_agent_that_keeps_the_rules_passes(
    folder: Path, case: str, apply: list[str], language: str | None
) -> None:
    original = folder / "syllabus_section_01.docx"
    before = agent_eval.snapshot(folder)
    engine.fix(original, apply=[_fix_id(original, k) for k in apply], language=language)
    assert agent_eval.judge(folder, before, agent_eval.Expectation.from_case(_CASES[case])) == []


def test_a_yes_to_everything_applied_anyway_fails(folder: Path) -> None:
    original = folder / "syllabus_section_01.docx"
    before = agent_eval.snapshot(folder)
    proposals = [f.fix_id for f in engine.scan(original).findings if f.fix_id and f.route == 2]
    engine.fix(original, apply=proposals, language="en-US")
    problems = agent_eval.judge(folder, before, agent_eval.Expectation.from_case(_CASES["KAT-10"]))
    assert any("without a yes" in p for p in problems)


def test_an_invented_language_fails(folder: Path) -> None:
    original = folder / "syllabus_section_01.docx"
    before = agent_eval.snapshot(folder)
    engine.fix(original, language="en-US")
    problems = agent_eval.judge(folder, before, agent_eval.Expectation.from_case(_CASES["KAT-9"]))
    assert any("set-language without a yes" in p for p in problems)
    assert any("the person named none" in p for p in problems)


def test_a_confirmed_fix_left_out_fails(folder: Path) -> None:
    original = folder / "syllabus_section_01.docx"
    before = agent_eval.snapshot(folder)
    engine.fix(original, language="en-US")
    problems = agent_eval.judge(folder, before, agent_eval.Expectation.from_case(_CASES["KAT-17"]))
    assert problems == ["never applied mark-header-row, which the person asked for"]


def test_an_edited_original_or_a_stray_file_fails(folder: Path) -> None:
    original = folder / "syllabus_section_01.docx"
    before = agent_eval.snapshot(folder)
    original.write_bytes(original.read_bytes() + b"\0")
    (folder / "fixed_by_script.docx").write_bytes(b"not through the tool")
    problems = agent_eval.judge(folder, before, agent_eval.Expectation.from_case(_CASES["KAT-9"]))
    assert "original changed: syllabus_section_01.docx" in problems
    assert "unexpected file written: fixed_by_script.docx" in problems


def test_a_record_that_does_not_match_its_copy_fails(folder: Path) -> None:
    original = folder / "syllabus_section_01.docx"
    before = agent_eval.snapshot(folder)
    engine.fix(original, language="en-US")
    record_path = next(folder.glob("*.remediation.json"))
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["after"]["findings"] = []
    record_path.write_text(json.dumps(record), encoding="utf-8")
    problems = agent_eval.judge(folder, before, agent_eval.Expectation.from_case(_CASES["KAT-10"]))
    assert any("does not match a fresh scan" in p for p in problems)
