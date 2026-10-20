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
     and ``tests/`` (fictional fixture files, their expected results, and the
     conversation evals). Fixed timestamps, so an unchanged source produces a
     byte-identical archive.
   * ``dist/<slug>-bot/`` -- the BoodleBox pack: ``instructions.md`` for the
     instruction field and ``knowledge/`` to attach. No scripts; the bot runs none.
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
import io
import logging
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from wcag_tool import rules
from wcag_tool.demo import make_test_set

logger = logging.getLogger(__name__)

_ZIP_DATE_TIME = (2026, 10, 19, 0, 0, 0)
_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
_NAME = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
_REFERENCE_LINK = re.compile(r"`references/([A-Za-z0-9_.-]+\.md)`")
_BLOCK = re.compile(r"(<!-- generated:(\w+) -->\n).*?(<!-- /generated:\2 -->)", re.DOTALL)
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


def _skill_files(skill_dir: Path, fixtures: list[Path]) -> list[tuple[str, bytes]]:
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
    for path in fixtures:
        data = path.read_bytes()
        if path.suffix in (".docx", ".pptx"):
            data = _stable_office(data)
        out.append((f"tests/fixtures/{path.name}", data))
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


def _bot_pack(skill_dir: Path, out: Path) -> list[Path]:
    """Write the BoodleBox instructions and knowledge files."""
    if out.exists():
        shutil.rmtree(out)
    knowledge = out / "knowledge"
    knowledge.mkdir(parents=True)
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    body = _FRONT_MATTER.sub("", skill_text, count=1).strip()
    attached = [p.name for p in _reference_order(skill_text, skill_dir / "references")]
    header = (
        "<!-- BoodleBox bot instructions, built from skill/SKILL.md. Do not edit here. -->\n\n"
        "You are running as a BoodleBox bot. No tool is connected and you cannot run code, so "
        "every session takes the last path in §2, *no tool connected and you cannot run code*, "
        "and the report uses the no-tool claim. Your knowledge files are the "
        "pages this text calls `references/...`: "
        + ", ".join(f"`{n}`" for n in attached)
        + ", plus `checks.json` and `coverage.json`, the same rules as data. When a page and "
        "a JSON file seem to differ, the JSON is right; say so.\n\n"
    )
    written = [out / "instructions.md"]
    written[0].write_text(header + body + "\n", encoding="utf-8", newline="\n")
    for page in _reference_order(skill_text, skill_dir / "references"):
        shutil.copyfile(page, knowledge / page.name)
        written.append(knowledge / page.name)
    for name in _BOT_RULES:
        shutil.copyfile(_rules_dir() / name, knowledge / name)
        written.append(knowledge / name)
    return written


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
        fixtures = make_test_set(Path(tmp))
        _zip_skill(name, _skill_files(skill_dir, fixtures), archive)
    written.append(archive)

    written += _bot_pack(skill_dir, dist / f"{slug}-bot")

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
