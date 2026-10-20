"""The rule set as data: WCAG's text, the checks, and what the checks cannot see.

Three files under ``wcag_tool/rules/`` hold everything the scanner, the skill and
the bot must agree on:

* ``wcag21.json`` -- the 50 Level A and AA success criteria, quoted from W3C by
  ``tools/extract_wcag.py``.
* ``checks.json`` -- every check: its criterion, route, closure state, fix and
  wording.
* ``coverage.json`` -- for every criterion in every format, whether a check
  covers part of it, and who judges what is left.

This module loads them, refuses to start if they disagree with each other, and
renders the Markdown that the skill's reference pages and the bot's knowledge
files are built from. It imports nothing else from the package, so every other
module can import it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

FORMATS = ("docx", "pptx", "pdf")
FORMAT_NAMES = {"docx": "Word", "pptx": "PowerPoint", "pdf": "PDF"}
ROUTES = (1, 2)
CLOSURES = (
    "automatically_verified",
    "content_owner_verified",
    "expert_verified",
    "user_task_verified",
)
CONFIDENCES = ("high", "medium", "low")
STATUSES = ("checked_in_part", "not_checked", "if_present")
WHO = {"author": "the author", "expert": "an expert", "user_test": "a screen-reader task test"}


class RulesError(ValueError):
    """Raised when the rule files disagree with each other or a caller misuses them."""


@dataclass(frozen=True)
class Criterion:
    """One WCAG 2.1 success criterion, as W3C words it."""

    id: str
    name: str
    level: str
    text: str
    understanding: str

    @property
    def label(self) -> str:
        """Number and name, e.g. ``2.4.2 Page Titled``."""
        return f"{self.id} {self.name}"


@dataclass(frozen=True)
class Check:
    """One check the scanner runs. Field meanings are in ``checks.schema.json``."""

    id: str
    format: str
    criterion: str
    finding: str
    looks_at: str
    route: int
    closure: str
    confidence: str
    fix_id: str | None
    remedy: str
    proposal: str | None
    template_fix: str
    from_text: str

    @property
    def fix_name(self) -> str | None:
        """The fix id up to its first placeholder, e.g. ``mark-header-row``."""
        return self.fix_id.split(":", 1)[0] if self.fix_id else None


@dataclass(frozen=True)
class Cell:
    """What the tool can say about one criterion in one format."""

    status: str
    who: str
    note: str
    when: str | None = None


@dataclass(frozen=True)
class Rules:
    """The loaded, cross-checked rule set."""

    criteria: dict[str, Criterion]
    checks: dict[str, Check]
    coverage: dict[str, dict[str, Cell]]
    source: dict[str, str]

    # ----- queries -------------------------------------------------------------------------

    def checks_for(self, fmt: str, criterion: str | None = None) -> list[Check]:
        """Checks for a format, optionally narrowed to one criterion, in file order."""
        return [
            c
            for c in self.checks.values()
            if c.format == fmt and (criterion is None or c.criterion == criterion)
        ]

    def ids_with(self, fmt: str, status: str) -> list[str]:
        """Criterion ids whose cell for ``fmt`` has ``status``, in WCAG order."""
        return [cid for cid in self.criteria if self.coverage[cid][fmt].status == status]

    def evaluated(self, fmt: str) -> list[str]:
        """What the checks look at, one line per criterion they touch.

        Args:
            fmt: ``docx``, ``pptx`` or ``pdf``.

        Returns:
            Lines such as ``2.4.2 Page Titled (document title)``.
        """
        lines = []
        for cid in self.ids_with(fmt, "checked_in_part"):
            looks = "; ".join(dict.fromkeys(c.looks_at for c in self.checks_for(fmt, cid)))
            lines.append(f"{self.criteria[cid].label} ({looks})")
        return lines

    def not_evaluated(self, fmt: str) -> list[str]:
        """Everything the checks do not settle, for every criterion, in WCAG order.

        A criterion a check covers in part appears too, with what is left. Nothing is
        left out, so nothing can be read as passed.

        Args:
            fmt: ``docx``, ``pptx`` or ``pdf``.

        Returns:
            One line per criterion, naming who can judge it.
        """
        lines = []
        for cid, criterion in self.criteria.items():
            cell = self.coverage[cid][fmt]
            if cell.status == "checked_in_part":
                head = f"{criterion.label}, beyond what was checked"
            elif cell.status == "if_present":
                head = f"{criterion.label}, if the file has {cell.when}"
            else:
                head = criterion.label
            lines.append(f"{head}: {cell.note} ({WHO[cell.who]})")
        return lines

    def coverage_summary(self, fmt: str) -> dict[str, list[str]]:
        """Criterion ids grouped by status, the compact form a report carries."""
        return {status: self.ids_with(fmt, status) for status in STATUSES}

    def criteria_detail(self, ids: list[str]) -> dict[str, dict[str, str]]:
        """W3C's wording and Understanding link for the given criteria, in WCAG order."""
        wanted = set(ids)
        return {
            cid: {
                "name": c.name,
                "level": c.level,
                "text": c.text,
                "understanding": c.understanding,
            }
            for cid, c in self.criteria.items()
            if cid in wanted
        }

    def resolve_fix_id(self, check_id: str, fix_id: str | None) -> str | None:
        """Return the fix id a finding should carry, filled in and checked against its template.

        Args:
            check_id: The check raising the finding.
            fix_id: The id the scanner built, or None to take the check's fixed id.

        Returns:
            The fix id, or None when the check has no fix.

        Raises:
            RulesError: If the id does not match the check's template.
        """
        check = self.checks[check_id]
        if check.fix_id is None:
            if fix_id is not None:
                raise RulesError(f"{check_id} has no fix, but the scanner passed {fix_id!r}")
            return None
        template = check.fix_id.split(":")
        if fix_id is None:
            if len(template) > 1:
                raise RulesError(f"{check_id} needs its fix id filled in: {check.fix_id}")
            return check.fix_id
        parts = fix_id.split(":")
        if parts[0] != template[0] or len(parts) != len(template):
            raise RulesError(f"{fix_id!r} does not match {check_id}'s fix {check.fix_id!r}")
        return fix_id

    # ----- consistency ---------------------------------------------------------------------

    def validate(self) -> None:
        """Raise if the three files disagree. Called on every load.

        Raises:
            RulesError: Naming the first disagreement found.
        """
        levels = [c.level for c in self.criteria.values()]
        if (levels.count("A"), levels.count("AA")) != (30, 20):
            raise RulesError("wcag21.json must hold 30 Level A and 20 Level AA criteria")
        if list(self.coverage) != list(self.criteria):
            raise RulesError("coverage.json must list every criterion once, in WCAG order")
        for check in self.checks.values():
            if check.criterion not in self.criteria:
                raise RulesError(f"{check.id}: unknown criterion {check.criterion}")
            if check.format not in FORMATS or not check.id.startswith(f"{check.format}."):
                raise RulesError(f"{check.id}: id and format disagree")
            if check.route not in ROUTES or check.closure not in CLOSURES:
                raise RulesError(f"{check.id}: route or closure out of range")
            if check.confidence not in CONFIDENCES:
                raise RulesError(f"{check.id}: confidence out of range")
            if check.route == 1 and (check.fix_id is None or ":" in check.fix_id):
                raise RulesError(f"{check.id}: Route 1 needs a fix that takes no arguments")
            if check.route == 2 and not check.proposal:
                raise RulesError(f"{check.id}: Route 2 needs a proposal for the person")
            cell = self.coverage[check.criterion][check.format]
            if cell.status != "checked_in_part":
                raise RulesError(
                    f"{check.id} checks {check.criterion} in {check.format}, but coverage.json "
                    f"says {cell.status}"
                )
        for cid, cells in self.coverage.items():
            for fmt, cell in cells.items():
                if cell.status not in STATUSES or cell.who not in WHO:
                    raise RulesError(f"coverage {cid} {fmt}: status or who out of range")
                if (cell.status == "if_present") != (cell.when is not None):
                    raise RulesError(f"coverage {cid} {fmt}: 'when' goes with if_present only")
                if cell.status == "checked_in_part" and not self.checks_for(fmt, cid):
                    raise RulesError(
                        f"coverage says {cid} is checked in part in {fmt}, but no check exists"
                    )

    # ----- Markdown ------------------------------------------------------------------------

    def markdown_checks_table(self, fmt: str) -> str:
        """The table for one format in ``checks.md``."""
        lines = ["| Check | Criterion | Route | Fix |", "| :--- | :--- | :-: | :--- |"]
        for c in self.checks_for(fmt):
            fix = f"`{c.fix_id}` — {c.remedy}" if c.fix_id else c.remedy
            lines.append(f"| {c.finding} | {c.criterion} | {c.route} | {fix} |")
        return "\n".join(lines)

    def markdown_not_evaluated(
        self, fmt: str, files: int | None = None, details: str = "`criteria.md`"
    ) -> str:
        """The compact not-evaluated paragraph for one format.

        Args:
            fmt: ``docx``, ``pptx`` or ``pdf``.
            files: How many files of this format were scanned, when it is a pile.
            details: Where the reader finds what each criterion needs.

        Returns:
            Markdown naming every criterion the checks do not settle, by status.
        """
        name = FORMAT_NAMES[fmt]
        if files is not None:
            name += f" ({files} file{'s' if files != 1 else ''})"
        part = ", ".join(self.ids_with(fmt, "checked_in_part"))
        missing = " · ".join(self.criteria[cid].label for cid in self.ids_with(fmt, "not_checked"))
        if_present = ", ".join(self.ids_with(fmt, "if_present"))
        return (
            f"**Not evaluated in {name}.** Checked only in part, a person judges the rest: "
            f"{part}. Not checked at all: {missing}. Not checked, and applies only when the "
            f"file has that kind of content (media, forms, animation, a set of files): "
            f"{if_present}. What each one needs, and who judges it, is in {details}."
        )

    def markdown_criteria(self) -> str:
        """The whole ``criteria.md`` reference page: the matrix, then W3C's words."""
        short = {
            "checked_in_part": "in part",
            "not_checked": "not checked",
            "if_present": "if present",
        }
        lines = [
            "# Every WCAG 2.1 A and AA criterion, and what the triage can say about it",
            "",
            "Generated from `rules/wcag21.json` and `rules/coverage.json` by "
            "`tools/build_skill.py`. Do not edit by hand.",
            "",
            "For each criterion and each format: **in part** means a check exists and a person "
            "judges the rest; **not checked** means it applies to every file and the tool does "
            "not look; **if present** means it applies only when the file has that kind of "
            "content. No criterion is ever reported as passed. *Who* names who can close the "
            "gap: the author, an expert, or a screen-reader task test (Route 3).",
            "",
            f"Criterion text is quoted from [WCAG 2.1]({self.source['source']}) "
            f"(W3C Recommendation, {self.source['source_date']}). {self.source['copyright']} "
            f"[License]({self.source['license']}).",
            "",
            "| Criterion | Level | Word | PowerPoint | PDF |",
            "| :--- | :-: | :--- | :--- | :--- |",
        ]
        for cid, c in self.criteria.items():
            cells = " | ".join(short[self.coverage[cid][fmt].status] for fmt in FORMATS)
            lines.append(f"| {c.label} | {c.level} | {cells} |")
        for cid, c in self.criteria.items():
            lines += ["", f"## {c.label} (Level {c.level})", ""]
            lines += [f"> {line}" if line else ">" for line in c.text.splitlines()]
            lines += ["", f"[Understanding {c.name}]({c.understanding})", ""]
            for fmt in FORMATS:
                cell = self.coverage[cid][fmt]
                checks = ", ".join(f"`{k.id}`" for k in self.checks_for(fmt, cid))
                status = {
                    "checked_in_part": f"checked in part by {checks}; still to judge",
                    "not_checked": "not checked",
                    "if_present": f"if the file has {cell.when}; not checked",
                }[cell.status]
                who = WHO[cell.who]
                lines.append(f"- **{FORMAT_NAMES[fmt]}**: {status}: {cell.note}. *Who:* {who}.")
        lines.append("")
        return "\n".join(lines)


def _read(name: str) -> Any:
    return json.loads((files("wcag_tool") / "rules" / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load() -> Rules:
    """Load and cross-check the rule files. Cached; the files do not change at run time.

    Returns:
        The rule set.

    Raises:
        RulesError: If the files disagree with each other.
    """
    wcag = _read("wcag21.json")
    raw_checks = _read("checks.json")["checks"]
    raw_coverage = _read("coverage.json")["criteria"]
    rules = Rules(
        criteria={c["id"]: Criterion(**c) for c in wcag["criteria"]},
        checks={c["id"]: Check(**c) for c in raw_checks},
        coverage={row["id"]: {fmt: Cell(**row[fmt]) for fmt in FORMATS} for row in raw_coverage},
        source={k: wcag[k] for k in ("source", "source_date", "copyright", "license")},
    )
    if len(rules.checks) != len(raw_checks):
        raise RulesError("checks.json has a duplicate check id")
    rules.validate()
    return rules
