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


def test_the_agent_runs_without_api_keys_unless_asked(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.setenv(name, "not-a-real-key")
    monkeypatch.setenv("PATH_MARKER", "kept")
    env = agent_eval.agent_env()
    assert "ANTHROPIC_API_KEY" not in env and "GEMINI_API_KEY" not in env
    assert env["PATH_MARKER"] == "kept"
    assert agent_eval.agent_env(use_api_key=True)["ANTHROPIC_API_KEY"] == "not-a-real-key"


@pytest.mark.parametrize(
    ("status", "use_api_key", "refused"),
    [
        ({"loggedIn": True, "authMethod": "claude.ai", "subscriptionType": "max"}, False, False),
        (
            {"loggedIn": True, "authMethod": "claude.ai", "apiKeySource": "ANTHROPIC_API_KEY"},
            False,
            True,
        ),
        ({"loggedIn": True, "authMethod": "apiKey", "apiKeySource": "/login"}, False, True),
        ({"loggedIn": False}, False, True),
        ({"loggedIn": True, "authMethod": "claude.ai", "apiKeySource": "x"}, True, False),
    ],
)
def test_a_run_refuses_anything_but_the_subscription(
    status: dict, use_api_key: bool, refused: bool
) -> None:
    assert (agent_eval.login_problem(status, use_api_key) is not None) is refused


def test_the_eval_lets_the_agent_use_every_server_tool() -> None:
    # A tool missing here is silently blocked in the live run, as extract_content once was.
    import asyncio

    from wcag_tool.server import mcp

    names = {t.name for t in asyncio.run(mcp.list_tools())}
    allowed = {t.split("__")[-1] for t in agent_eval.ALLOWED_TOOLS if t.startswith("mcp__")}
    assert allowed == names


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
