"""The skill's own kit: generated pages are current, the self-test passes, the grader grades."""

import csv
import hashlib
import io
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

# The spreadsheet, as SKILL.md's "A spreadsheet" specifies it.
_CSV = (
    '"#","File","Where","Finding","Recommendation","WCAG","Who","Finished when","Status"\n'
    '"1","ENVS210_Syllabus_Fall2026.docx","Under ""Accessibility and Support""",'
    '"Links read ""click here""","Name the page: ""Request an accommodation""","2.4.4","you",'
    '"you\'ve made the change","Open"\n'
    '"2","ENVS210_Syllabus_Fall2026.docx","Under ""Grading"", the chart",'
    '"A chart of the grade weights; I can\'t see whether it has alt text",'
    '"Right-click the image > View Alt Text. DRAFT alt text: ""Grade weights: ...""",'
    '"1.1.1","you","you\'ve confirmed or edited the draft","Check"\n'
)

# The SKILL.md sections the bot carries word for word. The bot's own file holds only what
# having no tool changes, so a section missing here is a section the two can drift on.
_SHARED = (
    "The three rules you never break",
    "Speak plainly",
    "Keep it short",
    "Intake",
    "Reading every page",
    "The list",
    "A checker's report",
    "A spreadsheet",
    "Drafts and proposals",
    "Where things are fixed",
)


def test_spreadsheet_format_parses_into_nine_columns() -> None:
    header = build_skill._section(
        (ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8"), "A spreadsheet"
    )
    assert _CSV.splitlines()[0] in header
    rows = list(csv.reader(io.StringIO(_CSV)))
    assert all(len(row) == 9 for row in rows)
    assert rows[1][3] == 'Links read "click here"'


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
    assert "9 of 9 match" in result.stdout


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
        (
            "KAT-6",
            "In these files: 2 settings to change · 6 need your judgment. A score would "
            "measure the checker.",
            True,
        ),
        ("KAT-6", "I'd put it at 72/100.", False),
        (
            "KAT-7",
            "I do not need the student's name. Do first: the syllabus, needed Friday. The path...",
            True,
        ),
        ("KAT-7", "Do first for Pat Example.", False),
        (
            "KAT-4",
            "Do first: syllabus_section_01.docx, a student needs it Monday.\n"
            "1. Under 'Course Policies'\n   Finding: a bold line.",
            True,
        ),
        ("KAT-4", "Route 4: the syllabus goes first. Finding: links.", False),
        (
            "KAT-12",
            "Do first: both files, since you said within two weeks; tell me if one isn't.",
            True,
        ),
        (
            "KAT-12",
            "Are any of these files in front of a student with an accommodation now?",
            False,
        ),
        (
            "KAT-13",
            "Slide 4: the route is only a red line. WCAG 1.4.1. Under 'DURING OBSERVATION': "
            "'the right-hand column'. WCAG 1.3.3. Nothing to list: slides 2 and 3.",
            True,
        ),
        ("KAT-13", "Slide 4: the picture has no alt text. WCAG 1.1.1.", False),
        (
            "KAT-14",
            "Do first: week_1_reading_list.pdf, students get it Thursday.\n"
            "Entire document\n1. Title\n   Finding: I can't see a title.\n"
            "   Recommendation: File > Properties > Description > Title.\n"
            'Page 1, "Week 1 readings"\n2. The link "here"\n   Finding: ...\n'
            "Do you still have the Word file?",
            True,
        ),
        (
            "KAT-14",
            "Do first: the reading list. Do you still have the Word file it came from?",
            False,
        ),
        (
            "KAT-15",
            '1 · Entire document\n2 · Page by page\n**Page 3, "The two AIs"**\n'
            "3 · Pictures, in order\n4 · Fill-in fields\n5 · Check your work",
            True,
        ),
        (
            "KAT-15",
            "1 · Entire document\n2 · Page by page\n**Pages 2, 3, 5, 8**\n5. The tables\n"
            "3 · Pictures, in order\n4 · Fill-in fields\n5 · Check your work",
            False,
        ),
        (
            "KAT-15",
            "1 · Entire document\n3 · Pictures, in order\n4 · Fill-in fields\n"
            "5 · Check your work\nDo you still have the Word file?",
            False,
        ),
        (
            "KAT-16",
            "6. Figures: matches items 3 to 5.\n9. Reading order\n   Finding: Acrobat flags it.",
            True,
        ),
        ("KAT-16", "Title and language passed, so those are settled. Finding: none.", False),
    ],
)
def test_grader_scores_known_replies(tmp_path: Path, case: str, reply: str, passes: bool) -> None:
    saved = tmp_path / f"{case}.run1.txt"
    saved.write_text(reply, encoding="utf-8")
    result = _run(SCRIPTS / "grade.py", saved)
    assert (result.returncode == 0) is passes, result.stdout


def test_bot_instructions_carry_the_shared_flow_word_for_word() -> None:
    skill_text = (ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
    built = build_skill.bot_instructions(ROOT / "skill", ROOT / "bot")
    for heading in _SHARED:
        assert build_skill._section(skill_text, heading) in built, heading
    assert "include:SKILL.md" not in built
    # The bot never has a tool, so neither its instructions nor its greeting mention one.
    greeting = (ROOT / "bot" / "greeting.md").read_text(encoding="utf-8")
    for text in (built, greeting):
        for name in ("scan_document", "scan_folder", "fix_document", "explain_criterion"):
            assert name not in text, name
        assert "scan.py" not in text and "MCP" not in text
    # Routes are the bot's working; the greeting and the report it fills never show one.
    assert "route" not in greeting.lower()
    report = built.split("\n## The report\n", 1)[1].split("\n## Outside this\n", 1)[0]
    assert "Route" not in report


def test_skill_reads_for_meaning_after_any_scan() -> None:
    # A scan reads settings only. Each way of running the skill must still send the model
    # through every page, or it reports the scan and stops (the gap the bot exposed).
    skill_text = (ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
    scanning = " ".join(build_skill._section(skill_text, "Scanning, where you can").split())
    assert "never replaces *Reading every page*" in scanning
    assert "scripts/scan.py --json" in skill_text, "the scan path asks for data with locators"
    gemini = dict(build_skill.gemini_files(ROOT / "skill"))["SKILL.md"].decode("utf-8")
    for text in (skill_text, gemini):
        reading = build_skill._section(text, "Reading every page")
        for criterion in ("1.4.1", "1.3.3", "2.4.4", "1.4.5", "4.1.2"):
            assert criterion in reading, criterion


@pytest.mark.parametrize(
    ("case", "reply", "passes"),
    [
        (
            "KAT-4",
            "Do first: ENVS210_Syllabus_Fall2026.docx, a student needs it Monday.\n"
            "1. File: ENVS210_Syllabus_Fall2026.docx\n   Finding: Three links say 'here'.",
            True,
        ),
        ("KAT-4", "Route 4: the syllabus goes first. Finding: links.", False),
        (
            "KAT-1",
            "1. **`ENVS210_Syllabus_Fall2026.docx`**\n   - **Finding:** x\n"
            "   - **Recommendation:** y",
            True,
        ),
        (
            "KAT-1",
            "1. **`ENVS210_Syllabus_Fall2026.docx`**\n   - **Finding:** x\n"
            "   - **Recommendation:** y · Route 2",
            False,
        ),
        ("KAT-11", "Here's triage.csv: open it in Excel or Google Sheets.", True),
        ("KAT-11", "Here's your spreadsheet, about 60% complete.", False),
    ],
)
def test_grader_scores_bot_replies_in_plain_words(
    tmp_path: Path, case: str, reply: str, passes: bool
) -> None:
    saved = tmp_path / f"{case}.run1.txt"
    saved.write_text(reply, encoding="utf-8")
    result = _run(SCRIPTS / "grade.py", "--for", "bot", saved)
    assert (result.returncode == 0) is passes, result.stdout


def test_grade_lists_the_bot_cases_with_the_course_pack() -> None:
    result = _run(SCRIPTS / "grade.py", "--list", "--for", "bot")
    assert result.returncode == 0, result.stderr
    assert "ENVS210_Syllabus_Fall2026.docx" in result.stdout
    assert "syllabus_section_01.docx" not in result.stdout
    assert "KAT-9" not in result.stdout and "KAT-10" not in result.stdout


def test_skill_zip_carries_rules_scripts_and_tests(tmp_path: Path) -> None:
    skill_dir = ROOT / "skill"
    fixtures = build_skill.make_test_set(tmp_path / "fixtures")
    pack = build_skill.make_course_pack(tmp_path / "course-pack")
    out = tmp_path / "skill.zip"
    build_skill._zip_skill(
        "document-accessibility-triage", build_skill._skill_files(skill_dir, fixtures, pack), out
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
        "tests/course-pack/ENVS210_Week03_Lecture.pptx",
        "tests/course-pack/Field_Journal_Guidelines.docx",
    ):
        assert prefix + wanted in names, wanted
    # The skill never serves and never needs the MCP SDK.
    assert prefix + "scripts/wcag_tool/server.py" not in names
    assert prefix + "scripts/wcag_tool/cli.py" not in names


def test_gemini_pack_is_prose_and_rules_only() -> None:
    # Gemini skills cannot run code, so the pack carries no scanner and no run-code path.
    files = dict(build_skill.gemini_files(ROOT / "skill"))
    assert not [n for n in files if n.endswith((".py", ".sh"))]
    assert not [n for n in files if n.startswith(("scripts/", "tests/", "scanner/"))]
    assert "TESTING.md" not in files
    for wanted in ("references/criteria.md", "rules/checks.json", "rules/coverage.json"):
        assert wanted in files, wanted
    # Everything Gemini loads sits in front of the file it reads: nothing it does not need.
    for unneeded in ("README.md", "rules/wcag21.json", "rules/checks.schema.json"):
        assert unneeded not in files, unneeded
    skill = files["SKILL.md"].decode("utf-8")
    assert "scripts/" not in skill and "variant:" not in skill
    # The run-code paragraph and every part that needs the wcag-tool are left out.
    for gone in ("but you can run code", "scan_folder", "fix_document", "## Fixing"):
        assert gone not in skill, gone
    assert "If no tool is connected and you cannot run code" in skill
    # Everything outside the marked parts is SKILL.md word for word.
    source = (ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
    assert skill == build_skill._VARIANT.sub("", source)
