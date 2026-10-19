"""Assemble the shareable skill set into ``dist/``.

The skill is authored as a folder: ``skill/SKILL.md`` with YAML front matter plus
``skill/references/`` pages it reads. That is the shape an assistant platform
takes as a skill or project folder. A faculty member in a chat window wants the
opposite: one file to paste. This script produces both from the one source:

* ``dist/<slug>.md`` -- the skill body (front matter removed) then every
  reference page in the order SKILL.md first mentions them. Paste it into any
  assistant, or use it as a BoodleBox bot's instructions.
* ``dist/<slug>-skill.zip`` -- ``SKILL.md`` and ``references/`` as a zip with
  fixed timestamps, so an unchanged source produces a byte-identical archive.
* ``dist/README.md`` -- copied from ``skill/README.md``.

Lifted from the ACE/LAC programme's ``lac/tools/build_skills.py`` and generalized
to one repo-rooted skill. The slug is a published identifier; do not change it
after a release.

Example:
    python tools/build_skill.py
    python tools/build_skill.py --slug wcag-triage
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

_ZIP_DATE_TIME = (2026, 10, 19, 0, 0, 0)
_FRONT_MATTER = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
_REFERENCE_LINK = re.compile(r"`references/([A-Za-z0-9_.-]+\.md)`")
DEFAULT_SLUG = "wcag-triage"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def _zip_skill(skill_dir: Path, out: Path) -> None:
    files = [skill_dir / "SKILL.md", *sorted((skill_dir / "references").glob("*.md"))]
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(str(path.relative_to(skill_dir.parent)).replace("\\", "/"))
            info.date_time = _ZIP_DATE_TIME
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())


def build(slug: str) -> list[Path]:
    """Build ``dist/`` and return the files written.

    Args:
        slug: The published identifier used in the dist file names.

    Returns:
        Paths written.
    """
    root = _repo_root()
    skill_dir = root / "skill"
    if not (skill_dir / "SKILL.md").is_file():
        raise FileNotFoundError(f"no SKILL.md under {skill_dir}")
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    written: list[Path] = []

    combined = dist / f"{slug}.md"
    combined.write_text(_combined(skill_dir), encoding="utf-8", newline="\n")
    written.append(combined)

    archive = dist / f"{slug}-skill.zip"
    _zip_skill(skill_dir, archive)
    written.append(archive)

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
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for path in build(args.slug):
        logger.info("  %s  (%d bytes)", path.relative_to(_repo_root()), path.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
