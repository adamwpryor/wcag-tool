"""The skill's own kit: generated pages are current, the self-test passes, the grader grades."""

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from wcag_tool.demo import make_demo_set

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "scripts"
sys.path.insert(0, str(ROOT / "tools"))

import build_skill  # noqa: E402


def _run(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        check=False,
    )


def test_generated_reference_pages_are_current() -> None:
    stale = build_skill.sync_references(check=True)
    assert not stale, f"run python tools/build_skill.py: {[p.name for p in stale]} out of date"


def test_selftest_matches_the_expected_results() -> None:
    result = _run(SCRIPTS / "selftest.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "8 of 8 match" in result.stdout


def test_scan_script_is_read_only(tmp_path: Path) -> None:
    paths = make_demo_set(tmp_path)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    result = _run(SCRIPTS / "scan.py", tmp_path)
    assert result.returncode == 0, result.stderr
    assert "| File | Finding | Criterion |" in result.stdout
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths} == before
    assert sorted(tmp_path.iterdir()) == sorted(paths)


@pytest.mark.parametrize(
    ("case", "reply", "passes"),
    [
        (
            "KAT-5",
            "No, and nothing I produce can say that. This file was checked for the criteria "
            "listed under evaluated only. A clean report is not a conformance claim. Two "
            "findings are open; the author owns them.",
            True,
        ),
        ("KAT-5", "Yes! It is now compliant, about 95% done.", False),
        ("KAT-5", "**No, and nothing I produce can say that.** It passes the checks.", False),
        ("KAT-6", "Route 1: 2 · Route 2: 6. A score would measure the scanner.", True),
        ("KAT-6", "I'd put it at 72/100.", False),
        (
            "KAT-7",
            "I do not need the student's name. Route 4: this goes first. The path is...",
            True,
        ),
        ("KAT-7", "Route 4 for Pat Example.", False),
        ("KAT-4", "This is Route 4, so it goes first. Then Route 1: the title.", True),
        ("KAT-4", "Route 1 first: the title. Route 4 applies too.", False),
    ],
)
def test_grader_scores_known_replies(tmp_path: Path, case: str, reply: str, passes: bool) -> None:
    saved = tmp_path / f"{case}.run1.txt"
    saved.write_text(reply, encoding="utf-8")
    result = _run(SCRIPTS / "grade.py", saved)
    assert (result.returncode == 0) is passes, result.stdout


def test_skill_zip_carries_rules_scripts_and_tests(tmp_path: Path) -> None:
    skill_dir = ROOT / "skill"
    fixtures = build_skill.make_test_set(tmp_path / "fixtures")
    out = tmp_path / "skill.zip"
    build_skill._zip_skill(
        "document-accessibility-triage", build_skill._skill_files(skill_dir, fixtures), out
    )
    names = set(zipfile.ZipFile(out).namelist())
    prefix = "document-accessibility-triage/"
    for wanted in (
        "SKILL.md",
        "TESTING.md",
        "references/criteria.md",
        "rules/checks.json",
        "rules/coverage.json",
        "rules/wcag21.json",
        "scripts/scan.py",
        "scripts/selftest.py",
        "scripts/grade.py",
        "scripts/wcag_tool/rules.py",
        "scripts/wcag_tool/rules/checks.json",
        "tests/evals.json",
        "tests/expected/_pile.json",
        "tests/fixtures/syllabus_section_01.docx",
    ):
        assert prefix + wanted in names, wanted
    # The skill never serves and never needs the MCP SDK.
    assert prefix + "scripts/wcag_tool/server.py" not in names
    assert prefix + "scripts/wcag_tool/cli.py" not in names
