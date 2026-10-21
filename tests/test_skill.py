"""The skill's own kit: generated pages are current, the self-test passes, the grader grades."""

import csv
import hashlib
import io
import re
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
    '"2","ENVS210_Syllabus_Fall2026.docx","Under ""Grading""",'
    '"Not visible to me: alt text on the chart","Right-click the image > View Alt Text",'
    '"1.1.1","you","you\'ve checked it","Check in the file"\n'
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
    gemini = dict(build_skill.gemini_files(ROOT / "skill"))["SKILL.md"].decode("utf-8")
    # Each scan path asks for the data, whose findings carry a locator; the table has none.
    for text, flag in ((skill_text, "scripts/scan.py --json"), (gemini, "`JSON = True`")):
        reading = build_skill._section(text, "Reading every page")
        for criterion in ("1.4.1", "1.3.3", "2.4.4", "1.4.5"):
            assert criterion in reading, criterion
        assert flag in text, flag


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


_PYTHON_BLOCK = re.compile(r"```python\n(.*?)```\n", re.DOTALL)


def _gemini_blocks() -> tuple[list[str], str]:
    """The scanner's save blocks and its scan block, as the Gemini pack carries them."""
    pages = {
        name: data.decode("utf-8")
        for name, data in build_skill.gemini_files(ROOT / "skill")
        if name.startswith("scanner/")
    }
    run = _PYTHON_BLOCK.findall(pages.pop("scanner/run.md"))
    saves = [block for page in pages.values() for block in _PYTHON_BLOCK.findall(page)]
    assert len(run) == 1 and len(saves) == len(pages)
    return saves, run[0]


def test_gemini_blocks_scan_like_the_package_and_refuse_a_bad_copy(tmp_path: Path) -> None:
    from wcag_tool import engine
    from wcag_tool.report import render_markdown

    work, scripts = tmp_path / "sandbox", tmp_path / "scripts"
    scripts.mkdir()
    paths = make_demo_set(work)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    saves, run = _gemini_blocks()
    # One code step, as run.md asks: every save block, then the scan block.
    step = scripts / "step.py"
    step.write_text("\n".join([*saves, run]), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", str(step)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=work,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == render_markdown(engine.scan_many(engine.iter_supported(work))) + "\n"
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths} == before

    # A later step that finds one part altered refuses to scan, and names the part.
    altered = work / "wcag_tool" / "alt.py"
    altered.write_text(altered.read_text(encoding="utf-8") + "# edited\n", encoding="utf-8")
    again = scripts / "again.py"
    again.write_text(run, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", str(again)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=work,
        check=False,
    )
    assert result.returncode != 0
    assert "wcag_tool/alt.py" in result.stderr and "| File |" not in result.stdout


def test_gemini_pack_carries_the_scanner_as_markdown_only() -> None:
    files = dict(build_skill.gemini_files(ROOT / "skill"))
    assert not [n for n in files if n.endswith((".py", ".sh"))]
    assert not [n for n in files if n.startswith(("scripts/", "tests/")) or n == "TESTING.md"]
    for wanted in ("references/criteria.md", "rules/wcag21.json", "scanner/run.md"):
        assert wanted in files, wanted
    skill = files["SKILL.md"].decode("utf-8")
    assert "scanner/run.md" in skill
    assert "scripts/" not in skill and "variant:" not in skill
    # Everything outside the marked paragraph is SKILL.md word for word.
    source = (ROOT / "skill" / "SKILL.md").read_text(encoding="utf-8")
    assert build_skill._section(source, "The three rules you never break") in skill
    assert build_skill._section(source, "If asked for something outside this") in skill
    assert source.split("<!-- variant:")[0] in skill
