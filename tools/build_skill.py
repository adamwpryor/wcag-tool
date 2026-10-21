"""Regenerate the skill's reference pages, then assemble the shareable set into ``dist/``.

The rules live as data in ``src/wcag_tool/rules/``. The skill's prose lives in
``skill/``. This script joins them, in two passes:

1. **References, in place.** The marked blocks in ``skill/references/checks.md``
   and the whole of ``skill/references/criteria.md`` are rendered from the rule
   files. ``--check`` only compares, and exits 1 if a page is out of date; CI
   runs it so a hand edit or a forgotten rebuild fails the build.
2. **The dist set.**

   * ``dist/<slug>.md`` -- the skill body (front matter removed) then every
     reference page in the order SKILL.md first mentions them. Paste it into any
     assistant.
   * ``dist/<slug>-skill.zip`` -- the skill folder: ``SKILL.md``,
     ``references/``, ``rules/`` (the JSON), ``scripts/`` (a read-only scanner,
     the self-test and the grader, with the checks vendored from the package),
     and ``tests/`` (fictional fixture files, their expected results, the
     conversation evals, and the realistic course pack some evals attach).
     Fixed timestamps, so an unchanged source produces a byte-identical archive.
   * ``dist/<slug>-gemini.zip`` -- the same skill for Gemini, which cannot run the
     files a skill carries: ``SKILL.md`` with its run-code paragraph taken from
     ``gemini/``, ``references/``, ``rules/``, and ``scanner/``, Markdown whose
     Python blocks save the scanner into the code sandbox and then scan, refusing
     if any part was not copied exactly. No ``scripts/`` and no test kit.
   * ``dist/<slug>-bot/`` -- the BoodleBox pack: ``instructions.md`` for the
     instruction field, built from ``bot/instructions.md`` with the rules and the
     shared session flow spliced in from SKILL.md; ``greeting.md`` for the greeting field;
     ``knowledge/`` to attach; and
     ``test-files/``, a realistic fictional course pack for testing it by hand.
     No scripts; the bot runs none.
     ``dist/<slug>-bot.zip`` is the same folder as one download for a release.
   * ``dist/README.md`` -- copied from ``skill/README.md``.

Lifted from the ACE/LAC programme's ``lac/tools/build_skills.py`` and generalized
to one repo-rooted skill. The slug is a published identifier; do not change it
after a release.

Example:
    python tools/build_skill.py
    python tools/build_skill.py --check
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import logging
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from wcag_tool import rules
from wcag_tool.course_pack import make_course_pack
from wcag_tool.demo import make_test_set

logger = logging.getLogger(__name__)

_ZIP_DATE_TIME = (2026, 10, 19, 0, 0, 0)
_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
_NAME = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
_REFERENCE_LINK = re.compile(r"`references/([A-Za-z0-9_.-]+\.md)`")
_BLOCK = re.compile(r"(<!-- generated:(\w+) -->\n).*?(<!-- /generated:\2 -->)", re.DOTALL)
_INCLUDE = re.compile(r"^<!-- include:SKILL\.md#(.+?) -->$", re.MULTILINE)
_VARIANT = re.compile(r"<!-- variant:([\w-]+) -->\n.*?<!-- /variant:\1 -->\n", re.DOTALL)
_LEADING_COMMENT = re.compile(r"\A<!--.*?-->\s*", re.DOTALL)
DEFAULT_SLUG = "wcag-triage"

# The package modules the skill's scripts need. server.py and cli.py stay out: they
# need the MCP SDK, and the skill's scripts never serve or write.
_VENDORED = (
    "__init__.py",
    "alt.py",
    "demo.py",
    "docx_checks.py",
    "docx_fixes.py",
    "engine.py",
    "findings.py",
    "log.py",
    "pdf_checks.py",
    "pptx_checks.py",
    "report.py",
    "rules.py",
)
# What a scan imports, which is what the Gemini pack carries as Markdown: the vendored set
# without demo.py and log.py, and the three rule files rules.load() reads.
_SCANNER = tuple(name for name in _VENDORED if name not in ("demo.py", "log.py"))
_SCANNER_RULES = ("checks.json", "coverage.json", "wcag21.json")
# What the BoodleBox bot attaches. wcag21.json is left out: its text is in criteria.md,
# which a knowledge index splits more cleanly than one long JSON array.
_BOT_RULES = ("checks.json", "coverage.json")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _rules_dir() -> Path:
    return _repo_root() / "src" / "wcag_tool" / "rules"


# ----- pass 1: reference pages ---------------------------------------------------------------


def _render_checks_md(text: str) -> str:
    rule_set = rules.load()

    def fill(match: re.Match[str]) -> str:
        fmt = match.group(2)
        body = rule_set.markdown_checks_table(fmt) + "\n\n" + rule_set.markdown_not_evaluated(fmt)
        return f"{match.group(1)}{body}\n{match.group(3)}"

    return _BLOCK.sub(fill, text)


def sync_references(check: bool = False) -> list[Path]:
    """Render the generated reference pages, or report which are stale.

    Args:
        check: Compare only; write nothing.

    Returns:
        The pages that were (or, with ``check``, would be) rewritten.
    """
    references = _repo_root() / "skill" / "references"
    wanted = {
        references
        / "checks.md": _render_checks_md((references / "checks.md").read_text(encoding="utf-8")),
        references / "criteria.md": rules.load().markdown_criteria(),
    }
    stale = []
    for path, text in wanted.items():
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current != text:
            stale.append(path)
            if not check:
                path.write_text(text, encoding="utf-8", newline="\n")
    return stale


# ----- pass 2: dist ----------------------------------------------------------------------------


def _skill_name(skill_text: str) -> str:
    front = _FRONT_MATTER.match(skill_text)
    name = _NAME.search(front.group(1)) if front else None
    if name is None:
        raise ValueError("SKILL.md front matter has no name")
    return name.group(1)


def _reference_order(skill_text: str, references_dir: Path) -> list[Path]:
    """Reference pages in the order SKILL.md first mentions them, then the rest."""
    seen: list[str] = []
    for name in _REFERENCE_LINK.findall(skill_text):
        if name not in seen:
            seen.append(name)
    ordered = [references_dir / n for n in seen if (references_dir / n).is_file()]
    for path in sorted(references_dir.glob("*.md")):
        if path not in ordered:
            ordered.append(path)
    return ordered


def _combined(skill_dir: Path) -> str:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    body = _FRONT_MATTER.sub("", skill_text, count=1).strip()
    parts = [
        body,
        "",
        "---",
        "",
        "# Reference pages\n\nThe pages the instructions above refer to as `references/...` "
        "follow, in the order they are first mentioned. Read them before the first answer.",
    ]
    for path in _reference_order(skill_text, skill_dir / "references"):
        parts += [
            "",
            "---",
            "",
            f"<!-- references/{path.name} -->",
            "",
            path.read_text(encoding="utf-8").strip(),
        ]
    parts.append("")
    return "\n".join(parts)


def _skill_files(
    skill_dir: Path, fixtures: list[Path], course_pack: list[Path] | None = None
) -> list[tuple[str, bytes]]:
    """Every (archive path, bytes) pair in the skill zip, relative to the skill folder."""
    out: list[tuple[str, bytes]] = [
        (name, (skill_dir / name).read_bytes())
        for name in ("SKILL.md", "TESTING.md", "README.md")
        if (skill_dir / name).is_file()
    ]
    for sub in ("references", "scripts", "tests"):
        for path in sorted((skill_dir / sub).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                out.append((path.relative_to(skill_dir).as_posix(), path.read_bytes()))
    for path in sorted(_rules_dir().glob("*.json")):
        out.append((f"rules/{path.name}", path.read_bytes()))
    package = _repo_root() / "src" / "wcag_tool"
    for name in _VENDORED:
        out.append((f"scripts/wcag_tool/{name}", (package / name).read_bytes()))
    for path in sorted(_rules_dir().glob("*.json")):
        out.append((f"scripts/wcag_tool/rules/{path.name}", path.read_bytes()))
    # The course pack sits beside the fixtures, not among them: the self-test scans every
    # fixture against tests/expected/, and the pack is for the conversation evals alone.
    for folder, paths in (("fixtures", fixtures), ("course-pack", course_pack or [])):
        for path in paths:
            data = path.read_bytes()
            if path.suffix in (".docx", ".pptx"):
                data = _stable_office(data)
            out.append((f"tests/{folder}/{path.name}", data))
    return out


def _stable_office(data: bytes) -> bytes:
    """Rewrite a .docx or .pptx package with fixed entry timestamps, keeping entry order.

    Office files are zips, and the libraries that write them stamp each entry with
    the time of saving. Without this, every build would ship different fixture bytes.
    """
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(out, "w") as dst:
        for item in src.infolist():
            info = zipfile.ZipInfo(item.filename, date_time=_ZIP_DATE_TIME)
            info.compress_type = item.compress_type
            dst.writestr(info, src.read(item))
    return out.getvalue()


def _zip_skill(name: str, files: list[tuple[str, bytes]], out: Path) -> None:
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for arcname, data in sorted(files):
            info = zipfile.ZipInfo(f"{name}/{arcname}")
            info.date_time = _ZIP_DATE_TIME
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def _section(markdown: str, heading: str) -> str:
    """The ``## heading`` section of a Markdown page, up to the next ``## `` heading."""
    match = re.search(
        rf"^## {re.escape(heading)}\n.*?(?=^## |\Z)", markdown, re.MULTILINE | re.DOTALL
    )
    if match is None:
        raise ValueError(f"SKILL.md has no section '## {heading}'")
    return match.group(0).strip()


def bot_instructions(skill_dir: Path, bot_dir: Path) -> str:
    """The bot's instruction text: SKILL.md's rules and session flow, around the bot's own parts.

    The bot never has a tool, so ``bot/instructions.md`` holds only what that changes:
    its opening, its report and its out-of-scope answers. Everything it shares with the
    skill is not rewritten there: each ``<!-- include:SKILL.md#<heading> -->`` line is
    replaced by that section of SKILL.md word for word, so the two cannot drift apart.

    Args:
        skill_dir: The folder holding SKILL.md.
        bot_dir: The folder holding the bot's instructions.md.

    Returns:
        The text to paste into the bot's Instructions field.

    Raises:
        ValueError: If the bot text includes no section, or names one SKILL.md lacks.
    """
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    source = (bot_dir / "instructions.md").read_text(encoding="utf-8")
    if not _INCLUDE.search(source):
        raise ValueError("bot/instructions.md must include the never-break rules from SKILL.md")
    body = _INCLUDE.sub(lambda m: _section(skill_text, m.group(1)), source)
    body = _LEADING_COMMENT.sub("", body, count=1).strip()
    header = (
        "<!-- BoodleBox bot instructions, built from bot/instructions.md and skill/SKILL.md. "
        "Do not edit here. -->\n\n"
    )
    return header + body + "\n"


def _bot_pack(skill_dir: Path, out: Path) -> list[Path]:
    """Write the BoodleBox instructions, knowledge files and test files."""
    if out.exists():
        shutil.rmtree(out)
    knowledge = out / "knowledge"
    knowledge.mkdir(parents=True)
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    written = [out / "instructions.md"]
    written[0].write_text(
        bot_instructions(skill_dir, _repo_root() / "bot"), encoding="utf-8", newline="\n"
    )
    # The platform shows the greeting before the first turn, so it is not in the instructions.
    shutil.copyfile(_repo_root() / "bot" / "greeting.md", out / "greeting.md")
    written.append(out / "greeting.md")
    for page in _reference_order(skill_text, skill_dir / "references"):
        shutil.copyfile(page, knowledge / page.name)
        written.append(knowledge / page.name)
    for name in _BOT_RULES:
        shutil.copyfile(_rules_dir() / name, knowledge / name)
        written.append(knowledge / name)
    for path in make_course_pack(out / "test-files"):
        if path.suffix in (".docx", ".pptx"):
            path.write_bytes(_stable_office(path.read_bytes()))
        written.append(path)
    return written


# ----- the Gemini pack ---------------------------------------------------------------------------

_SAVE_BLOCK = """# Saves {target}, one part of the triage scanner. Run it exactly as written.
from pathlib import Path

_part = Path("{target}")
_part.parent.mkdir(parents=True, exist_ok=True)
_part.write_text(r'''{text}''', encoding="utf-8", newline="\\n")
"""

_SCAN_BLOCK = """# Checks the saved parts, then scans. Read-only: it never writes to a course file.
import hashlib
import json
import sys
from pathlib import Path

# The course files, as paths this sandbox can open. Empty: every Word, PowerPoint and PDF file
# under the working folder.
FILES: list[str] = []
# True prints the report as data instead of the routed table.
JSON = False

PARTS = {{
{parts}
}}

if sys.version_info < (3, 11):
    raise RuntimeError(f"The scanner needs Python 3.11 or later, not {{sys.version.split()[0]}}.")
wrong = [
    part
    for part, digest in PARTS.items()
    if not Path(part).is_file() or hashlib.sha256(Path(part).read_bytes()).hexdigest() != digest
]
if wrong:
    raise RuntimeError(
        "Missing or not copied exactly: " + ", ".join(wrong) + ". Run the block for each "
        "again, unchanged, then this one."
    )
sys.path.insert(0, str(Path.cwd()))
for name in [m for m in sys.modules if m == "wcag_tool" or m.startswith("wcag_tool.")]:
    del sys.modules[name]

from wcag_tool import engine  # noqa: E402
from wcag_tool.report import render_markdown  # noqa: E402

found: list[Path] = []
for given in [Path(f) for f in FILES] or [Path.cwd()]:
    found.extend(engine.iter_supported(given) if given.is_dir() else [given])
if not found:
    raise RuntimeError("No Word, PowerPoint or PDF file found. Set FILES to the course files.")
batch = engine.scan_many(found)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.stdout.write(
    json.dumps(batch.to_dict(), indent=2, ensure_ascii=False) if JSON else render_markdown(batch)
)
sys.stdout.write("\\n")
"""


def scanner_parts() -> list[tuple[str, str]]:
    """The scanner's files as (sandbox path, text), in the form the Gemini pack saves them.

    Line endings are normalised so the fingerprints hold on any checkout. The rule files
    are minified: the sandbox has to reproduce every character, and indentation is half
    of coverage.json.

    Returns:
        Pairs for each module the scan imports, then each rule file it reads.
    """
    package = _repo_root() / "src" / "wcag_tool"
    parts = [
        (f"wcag_tool/{name}", (package / name).read_text(encoding="utf-8").replace("\r\n", "\n"))
        for name in _SCANNER
    ]
    for name in _SCANNER_RULES:
        data = json.loads((_rules_dir() / name).read_text(encoding="utf-8"))
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
        parts.append((f"wcag_tool/rules/{name}", text))
    return parts


def _save_block(target: str, text: str) -> str:
    block = _SAVE_BLOCK.format(target=target, text=text)
    # A raw triple-quoted string cannot hold every text. Prove this one survives the trip.
    literal = block.split("_part.write_text(", 1)[1].rsplit(", encoding=", 1)[0]
    if ast.literal_eval(literal) != text:
        raise ValueError(f"{target} cannot be carried in a raw string literal")
    return block


def _scanner_pages(parts: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """The ``scanner/`` pages: one per part, then ``run.md`` with the scan block."""
    pages = []
    for target, text in parts:
        page = Path(target).name + ".md"
        body = (
            f"# {target}\n\nOne part of the triage scanner. See `run.md`. Run this block "
            f"exactly as written; it saves `{target}` in the sandbox.\n\n"
            f"```python\n{_save_block(target, text)}```\n"
        )
        pages.append((page, body))
    listed = "\n".join(
        f"- `{page}` saves `{target}`" for (page, _), (target, _) in zip(pages, parts, strict=True)
    )
    digests = "\n".join(
        f'    "{target}": "{hashlib.sha256(text.encode("utf-8")).hexdigest()}",'
        for target, text in parts
    )
    run = (_repo_root() / "gemini" / "run.md").read_text(encoding="utf-8").strip()
    run += f"\n\n## The parts\n\n{listed}\n\n## Scan\n\n"
    run += f"```python\n{_SCAN_BLOCK.format(parts=digests)}```\n"
    return [*pages, ("run.md", run)]


def gemini_skill_md(skill_dir: Path) -> str:
    """SKILL.md as the Gemini pack carries it: each marked variant replaced from ``gemini/``.

    Args:
        skill_dir: The folder holding SKILL.md.

    Returns:
        The SKILL.md text for the Gemini pack.

    Raises:
        ValueError: If SKILL.md marks no variant.
    """
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    if not _VARIANT.search(text):
        raise ValueError("SKILL.md marks no variant for the Gemini pack")
    gemini = _repo_root() / "gemini"
    return _VARIANT.sub(
        lambda m: (gemini / f"{m.group(1)}.md").read_text(encoding="utf-8").strip() + "\n", text
    )


def gemini_files(skill_dir: Path) -> list[tuple[str, bytes]]:
    """Every (archive path, bytes) pair in the Gemini skill zip.

    Gemini skills cannot run the files they carry, so ``scripts/`` and the test kit stay
    out and the scanner comes as ``scanner/``: Markdown whose blocks save it into the
    code sandbox, then scan.

    Args:
        skill_dir: The folder holding SKILL.md.

    Returns:
        Archive paths relative to the skill folder, with their bytes.
    """
    out = [("SKILL.md", gemini_skill_md(skill_dir).encode("utf-8"))]
    if (skill_dir / "README.md").is_file():
        out.append(("README.md", (skill_dir / "README.md").read_bytes()))
    for path in sorted((skill_dir / "references").glob("*.md")):
        out.append((f"references/{path.name}", path.read_bytes()))
    for path in sorted(_rules_dir().glob("*.json")):
        out.append((f"rules/{path.name}", path.read_bytes()))
    for page, body in _scanner_pages(scanner_parts()):
        out.append((f"scanner/{page}", body.encode("utf-8")))
    return out


def build(slug: str) -> list[Path]:
    """Sync the references, then build ``dist/`` and return the files written.

    Args:
        slug: The published identifier used in the dist file names.

    Returns:
        Paths written.
    """
    root = _repo_root()
    skill_dir = root / "skill"
    if not (skill_dir / "SKILL.md").is_file():
        raise FileNotFoundError(f"no SKILL.md under {skill_dir}")
    written = sync_references()
    dist = root / "dist"
    dist.mkdir(exist_ok=True)

    combined = dist / f"{slug}.md"
    combined.write_text(_combined(skill_dir), encoding="utf-8", newline="\n")
    written.append(combined)

    name = _skill_name((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    archive = dist / f"{slug}-skill.zip"
    with tempfile.TemporaryDirectory() as tmp:
        fixtures = make_test_set(Path(tmp) / "fixtures")
        pack = make_course_pack(Path(tmp) / "course-pack")
        _zip_skill(name, _skill_files(skill_dir, fixtures, pack), archive)
    written.append(archive)

    gemini_zip = dist / f"{slug}-gemini.zip"
    _zip_skill(name, gemini_files(skill_dir), gemini_zip)
    written.append(gemini_zip)

    bot_dir = dist / f"{slug}-bot"
    written += _bot_pack(skill_dir, bot_dir)
    # One download for the release page: the same folder, zipped.
    bot_zip = dist / f"{slug}-bot.zip"
    bot_files = [
        (p.relative_to(bot_dir).as_posix(), p.read_bytes())
        for p in sorted(bot_dir.rglob("*"))
        if p.is_file()
    ]
    _zip_skill(bot_dir.name, bot_files, bot_zip)
    written.append(bot_zip)

    readme = skill_dir / "README.md"
    if readme.is_file():
        shutil.copyfile(readme, dist / "README.md")
        written.append(dist / "README.md")
    return written


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--slug", default=DEFAULT_SLUG)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if a generated reference page is out of date; write nothing",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.check:
        stale = sync_references(check=True)
        for path in stale:
            logger.error("out of date: %s (run python tools/build_skill.py)", path.name)
        return 1 if stale else 0
    for path in build(args.slug):
        logger.info("  %s  (%d bytes)", path.relative_to(_repo_root()), path.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
