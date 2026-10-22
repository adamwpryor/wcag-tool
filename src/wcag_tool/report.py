"""A pile of files: Route 5 aggregation, the routed table, and the plain-words work order.

One file is a report. A pile is a batch. The batch is where Route 5 lives,
because a systemic defect is only visible across files, and it is where the time
goes back: one template fix retires the same finding in every section.

The routed table (``render_markdown``) is working data. What a person reads is the
work order (``render_worklist``): the six-part template from the skill's *The list*,
laid out from the scan's facts so the format never depends on the model.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from wcag_tool import rules
from wcag_tool.findings import BOUNDED_CLAIM, Closure, Finding, Report, Route

# A sentence ends at a period followed by whitespace, so "image.png" stays whole.
_SENTENCE_END = re.compile(r"(?<=\.)\s+")

CLOSING_SENTENCE = (
    "This is a triage, not a conformance review. The files that matter most still need one "
    "person with a screen reader and a named task."
)

# A check becomes a Route 5 candidate when it appears in at least this many files
# and in at least this share of the files scanned.
_SYSTEMIC_MIN_FILES = 3
_SYSTEMIC_MIN_SHARE = 0.5


@dataclass
class Systemic:
    """One check that recurs across files.

    Attributes:
        check: The check id.
        criterion: The WCAG criterion.
        files: How many files carry it.
        total: How many files were scanned.
        proposal: What fixing it once at the source would look like.
    """

    check: str
    criterion: str
    files: int
    total: int
    proposal: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain types."""
        return {
            "check": self.check,
            "criterion": self.criterion,
            "files": self.files,
            "total": self.total,
            "route": int(Route.SYSTEMIC),
            "proposal": self.proposal,
        }


@dataclass
class Batch:
    """Several files scanned together.

    Attributes:
        reports: One per file, in scan order.
        skipped: Paths that were not scanned, with the reason.
    """

    reports: list[Report] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)

    def systemic(self) -> list[Systemic]:
        """Checks that recur across enough files to be fixed at the source."""
        total = len(self.reports)
        if total == 0:
            return []
        per_check: dict[str, set[str]] = defaultdict(set)
        criterion: dict[str, str] = {}
        for report in self.reports:
            for finding in report.findings:
                per_check[finding.check].add(report.asset)
                criterion[finding.check] = finding.criterion
        checks = rules.load().checks
        out: list[Systemic] = []
        for check, assets in sorted(per_check.items()):
            n = len(assets)
            if n >= _SYSTEMIC_MIN_FILES and n / total >= _SYSTEMIC_MIN_SHARE:
                out.append(
                    Systemic(
                        check=check,
                        criterion=criterion[check],
                        files=n,
                        total=total,
                        proposal=checks[check].template_fix,
                    )
                )
        return out

    def counts_by_route(self) -> dict[int, int]:
        """Findings per route across the batch."""
        counts: dict[int, int] = {r.value: 0 for r in Route}
        for report in self.reports:
            for route, n in report.by_route().items():
                counts[route] += n
        return counts

    def formats(self) -> dict[str, int]:
        """How many files of each format were scanned."""
        counts: dict[str, int] = {}
        for report in self.reports:
            counts[report.format] = counts.get(report.format, 0) + 1
        return counts

    def evaluated(self) -> dict[str, list[str]]:
        """What the checks look at, once per format in the pile."""
        return {fmt: rules.load().evaluated(fmt) for fmt in self.formats()}

    def not_evaluated(self) -> dict[str, list[str]]:
        """Everything the checks do not settle, once per format in the pile."""
        return {fmt: rules.load().not_evaluated(fmt) for fmt in self.formats()}

    def coverage(self) -> dict[str, dict[str, list[str]]]:
        """Criterion ids by status, once per format in the pile."""
        return {fmt: rules.load().coverage_summary(fmt) for fmt in self.formats()}

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain types, including the rendered Markdown.

        Per-format lists (evaluated, not evaluated, coverage) and the quoted criteria
        appear once for the pile rather than once per file, so a large pile stays
        readable by the assistant receiving it.
        """
        per_file = ("evaluated", "not_evaluated", "coverage", "criteria", "bounded_claim")
        reports = [
            {k: v for k, v in r.to_dict().items() if k not in per_file} for r in self.reports
        ]
        found = [f.criterion_id for r in self.reports for f in r.findings]
        return {
            "files": len(self.reports),
            "formats": self.formats(),
            "skipped": list(self.skipped),
            "counts_by_route": self.counts_by_route(),
            "systemic": [s.to_dict() for s in self.systemic()],
            "reports": reports,
            "evaluated": self.evaluated(),
            "not_evaluated": self.not_evaluated(),
            "coverage": self.coverage(),
            "criteria": rules.load().criteria_detail(found),
            "bounded_claim": BOUNDED_CLAIM,
            "markdown": render_markdown(self),
            **worklist_fields(self),
        }


def _next_step(finding: Finding) -> str:
    """What the last table column says: who moves next, and how."""
    if finding.route == Route.AUTO_FIX:
        return "tool"
    if "missing-alt" in finding.check:
        return "ask author what it shows"
    if finding.fix_id:
        return "confirm, then apply"
    return "author edits"


def _row(asset: str, finding: Finding) -> str:
    closure = finding.closure_required.value.replace("_", " ")
    draft = _next_step(finding)
    summary = _SENTENCE_END.split(finding.evidence, maxsplit=1)[0].rstrip(".")
    return (
        f"| {asset} | {finding.check} — {summary} | {finding.criterion} | {int(finding.route)} | "
        f"| {closure} | {draft} |"
    )


def render_markdown(batch: Batch) -> str:
    """Render the routed table the skill's §3 asks for, plus Route 5 lines and the claim.

    Args:
        batch: The scanned pile.

    Returns:
        Markdown text.
    """
    lines: list[str] = []
    n_files = len(batch.reports)
    counts = batch.counts_by_route()
    formats = ", ".join(f"{n} {fmt}" for fmt, n in batch.formats().items())
    skipped = f"; {len(batch.skipped)} skipped" if batch.skipped else ""
    lines.append(f"# Triage: {n_files} file{'s' if n_files != 1 else ''} ({formats}{skipped})")
    lines.append("")
    lines.append(
        "Findings by route: "
        + " · ".join(f"Route {r}: {n}" for r, n in counts.items())
        + ". Routes 3 and 4 are always 0 here: the tool cannot see them, a person adds them. "
        + "Owner column is blank on purpose: it wants a name."
    )
    lines.append("")
    lines.append(
        "| File | Finding | Criterion | Route | Owner (a name) | Closure needed | Next step |"
    )
    lines.append("| :--- | :--- | :--- | :-: | :--- | :--- | :--- |")
    for report in batch.reports:
        for finding in report.findings:
            lines.append(_row(report.asset, finding))
    if not any(r.findings for r in batch.reports):
        lines.append(
            "| | nothing found in the criteria evaluated; the not-evaluated list below still "
            "applies | | | | | |"
        )

    systemic = batch.systemic()
    lines.append("")
    lines.append("## Route 5: fix once at the source")
    lines.append("")
    if systemic:
        for s in systemic:
            lines.append(
                f"- **{s.check}** ({s.criterion}) in {s.files} of {s.total} files. {s.proposal}"
            )
    else:
        lines.append("- none: no check recurs across enough files to point at a template")

    if batch.skipped:
        lines.append("")
        lines.append("## Skipped")
        lines.append("")
        for item in batch.skipped:
            lines.append(f"- {item['path']}: {item['reason']}")

    lines.append("")
    lines.append("## Not evaluated")
    lines.append("")
    lines.append(
        "Nothing below was checked, and the table above is bounded by it. The JSON result's "
        "`not_evaluated` says what each criterion needs and who can judge it."
    )
    for fmt, n in batch.formats().items():
        lines.append("")
        lines.append(rules.load().markdown_not_evaluated(fmt, files=n, details="the JSON result"))

    lines.append("")
    lines.append("## What you may say")
    lines.append("")
    lines.append(f"> {BOUNDED_CLAIM}")
    lines.append("")
    lines.append(f"*{CLOSING_SENTENCE}*")
    lines.append("")
    return "\n".join(lines)


# ----- the work order ------------------------------------------------------------------------

# Which part of the six-part template a check's findings belong to. Anything not named here is
# a page-by-page item.
_WHOLE_DOCUMENT = {
    "missing-title",
    "missing-language",
    "untagged",
    "no-headings",
    "scanned-no-text",
}
_PICTURES = {"image-missing-alt", "picture-untagged"}
_FIELDS = {"form-field-no-name"}

# What "finished" means, in the person's words, for each closure state.
_FINISHED_WHEN = {
    Closure.AUTOMATICALLY_VERIFIED: "the setting is changed",
    Closure.CONTENT_OWNER_VERIFIED: "you've confirmed or edited it",
    Closure.EXPERT_VERIFIED: "someone with Acrobat and a screen reader checks it",
    Closure.USER_TASK_VERIFIED: "they complete the task",
}

_CHECKERS = {
    "pdf": "Acrobat: Prepare for accessibility › Check for accessibility, with *Create "
    "accessibility report* ticked",
    "docx": "Word: Review › Check Accessibility",
    "pptx": "PowerPoint: Review › Check Accessibility",
}

# Where a person changes a setting the tool can also set in a copy, by check id.
_SETTING_PATHS = {
    "docx.missing-title": "File › Info › Properties › Title",
    "pptx.missing-title": "File › Info › Properties › Title",
    "pdf.missing-title": "File › Properties › Description › Title, then Initial View › Show: "
    "Document Title",
    "docx.missing-language": "Select all, then Review › Language › Set Proofing Language",
    "pdf.missing-language": "File › Properties › Advanced › Language",
}

_PLACE = re.compile(r"^(page|slide)s? (\d+)", re.IGNORECASE)
_COUNTED = re.compile(r"^(paragraph|table|hyperlink) (\d+)$")
_COUNTED_NAMES = {"paragraph": "Paragraph", "table": "Table", "hyperlink": "Link"}


@dataclass
class WorkItem:
    """One numbered item of the work order, with what an agent needs to act on it.

    Attributes:
        number: The item's number in the rendered list.
        part: Which part of the template it sits in, 1 to 6.
        asset: The file.
        where: The place as a person finds it: "Slide 4, Picture 2", "Paragraph 14".
        finding: The scan's finding.
        fix_id: The fix the tool can apply once the person agrees, or None.
    """

    number: int
    part: int
    asset: str
    where: str
    finding: Finding | None
    fix_id: str | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain types."""
        return {
            "number": self.number,
            "part": self.part,
            "file": self.asset,
            "where": self.where,
            "check": self.finding.check if self.finding else None,
            "locator": self.finding.locator if self.finding else None,
            "fix_id": self.fix_id,
        }


def _where(locator: str) -> str:
    """A locator as a person would look for it. The scanner counts from 0; people from 1."""
    counted = _COUNTED.match(locator)
    if counted:
        return f"{_COUNTED_NAMES[counted.group(1)]} {int(counted.group(2)) + 1}"
    return locator[:1].upper() + locator[1:]


def _part(finding: Finding) -> int:
    kind = finding.check.split(".", 1)[1]
    if kind in _WHOLE_DOCUMENT:
        return 1
    if kind in _PICTURES:
        return 3
    if kind in _FIELDS:
        return 4
    return 2


def _place_key(locator: str) -> tuple[int, int]:
    """Page or slide order, so part 2 runs first page to last; other places keep scan order."""
    place = _PLACE.match(locator)
    return (0, int(place.group(2))) if place else (1, 0)


def _first_sentence(text: str) -> str:
    return _SENTENCE_END.split(text, maxsplit=1)[0].rstrip(".") + "."


def worklist(batch: Batch) -> list[WorkItem]:
    """The work order's items, numbered straight through, file by file and part by part.

    Args:
        batch: The scanned pile.

    Returns:
        Every finding as a numbered item, then one *Check your work* item per file.
    """
    items: list[WorkItem] = []
    for report in batch.reports:
        by_part: dict[int, list[Finding]] = defaultdict(list)
        for finding in report.findings:
            by_part[_part(finding)].append(finding)
        for part in (1, 2, 3, 4):
            ordered = sorted(by_part[part], key=lambda f: _place_key(f.locator))
            for finding in ordered:
                where = "" if part == 1 else _where(finding.locator)
                items.append(
                    WorkItem(len(items) + 1, part, report.asset, where, finding, finding.fix_id)
                )
        items.append(WorkItem(len(items) + 1, 5, report.asset, "", None, None))
    return items


def _item_lines(item: WorkItem, heading: str | None = None) -> list[str]:
    finding = item.finding
    assert finding is not None
    check = rules.load().checks[finding.check]
    where = item.where
    if heading and where == heading:
        where = ""
    elif heading and where.startswith(f"{heading}, "):
        where = where[len(heading) + 2 :]
    title = f"{where} · {check.finding}" if where else check.finding
    who = "you"
    if finding.closure_required == Closure.EXPERT_VERIFIED:
        who = "you, or someone with Acrobat"
    recommendation = finding.proposal or check.remedy
    path = _SETTING_PATHS.get(finding.check)
    if path and finding.fix_id == "set-language":
        who = "you, or I can set it in a copy once you name the language"
        recommendation = f"{path}. I never guess a language: tell me which it is."
    elif path:
        who = "you, or I can set it in a copy"
        recommendation = f"{path}."
    return [
        f"{item.number}. **{title}**",
        f"   - **Finding:** {finding.evidence}",
        f"   - **Recommendation:** {recommendation}",
        f"   - **WCAG** {finding.criterion} · **Who:** {who} · **Finished when:** "
        f"{_FINISHED_WHEN[finding.closure_required]}",
    ]


def render_worklist(batch: Batch) -> str:
    """Render the six-part work order from the scan's facts, in the person's words.

    No route numbers, check ids or fix ids appear: ``worklist_fields`` carries those for
    the agent. What a scan cannot know is left as a marked gap for the agent to fill from
    reading every page: what each picture shows, the words-only items, *Do first*, names,
    and the screen-reader task.

    Args:
        batch: The scanned pile.

    Returns:
        Markdown text.
    """
    items = worklist(batch)
    found = sum(1 for i in items if i.finding)
    pictures = sum(1 for i in items if i.part == 3)
    fields = sum(1 for i in items if i.part == 4)
    lines = [
        f"**In these files:** {found} items from the scan · pictures to settle: {pictures} · "
        f"pages with fields to name: {fields} · reading every page adds the rest",
        "",
    ]
    titles = {
        1: "1 · Entire document",
        2: "2 · Page by page",
        3: "3 · Pictures, in order",
        4: "4 · Fill-in fields",
        5: "5 · Check your work",
        6: "6 · Try it with a screen reader",
    }
    gaps = {
        2: "*Add what reading every page finds: links, colour or position, headings, tables, "
        "reading order.*",
        3: "*Look at each picture: describe it, then Decorative or a DRAFT alt text. Add any "
        "drawing made of shapes, which the scan cannot count.*",
        4: "*Add each field's printed label: that is the name to give it.*",
        6: "*Name one task in the file that matters most.*",
    }
    for report in batch.reports:
        mine = [i for i in items if i.asset == report.asset]
        lines += [f"**`{report.asset}`**", ""]
        for part in range(1, 7):
            lines += [f"**{titles[part]}**", ""]
            in_part = [i for i in mine if i.part == part]
            if part == 5:
                item = in_part[0]
                lines += [
                    f"{item.number}. **The program's own checker:** {_CHECKERS[report.format]}. "
                    "Upload the report, paste it, or send a screenshot, and I'll add anything "
                    "it found that this list doesn't have.",
                    "",
                ]
                continue
            heading: str | None = None
            for item in in_part:
                place = _PLACE.match(item.finding.locator) if item.finding else None
                page = f"{place.group(1).title()} {place.group(2)}" if place else None
                if part == 2 and page and page != heading:
                    lines += [f"**{page}**", ""]
                    heading = page
                if part in (3, 4):
                    assert item.finding is not None
                    lines.append(
                        f"{item.number}. **{item.where}:** {_first_sentence(item.finding.evidence)}"
                    )
                else:
                    lines += [*_item_lines(item, heading), ""]
            if part in (3, 4) and in_part:
                lines.append("")
            if part in gaps:
                lines += [gaps[part], ""]
            elif not in_part:
                lines += ["*None.*", ""]
    lines.append(
        "*Not checked by the scan, and still to judge: everything under `not_evaluated` in the "
        "result.*"
    )
    lines.append("")
    return "\n".join(lines)


def worklist_fields(batch: Batch) -> dict[str, Any]:
    """The work order for a result: the rendered list and the map from number to fix id.

    Args:
        batch: The scanned pile.

    Returns:
        ``worklist`` (Markdown) and ``worklist_items`` (one entry per numbered item).
    """
    return {
        "worklist": render_worklist(batch),
        "worklist_items": [item.to_dict() for item in worklist(batch)],
    }
