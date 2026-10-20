"""A pile of files: Route 5 aggregation and the routed table the skill asks for.

One file is a report. A pile is a batch. The batch is where Route 5 lives,
because a systemic defect is only visible across files, and it is where the time
goes back: one template fix retires the same finding in every section.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from wcag_tool import rules
from wcag_tool.findings import BOUNDED_CLAIM, Finding, Report, Route

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
