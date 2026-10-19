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


_SYSTEMIC_PROPOSALS = {
    "docx.missing-title": "Set the title in the template's document properties.",
    "docx.missing-language": "Set the default language in the template's styles.",
    "docx.table-no-header": "Mark the header row in the template's table style, once.",
    "docx.fake-heading": (
        "Put Heading styles on the template's section titles so copies inherit them."
    ),
    "docx.link-text": "Fix the shared link text in the template or the source the files copy from.",
    "docx.empty-heading": "Remove the empty heading from the template; every copy inherited it.",
    "docx.heading-skip": "Fix the heading levels in the template's outline once.",
    "docx.image-missing-alt": (
        "If the same image is in every file (a logo, a banner), set its alt text or mark it "
        "decorative in the template."
    ),
    "pptx.image-missing-alt": (
        "If the same image is on every slide (a logo), set its alt text or mark it decorative in "
        "the slide master."
    ),
    "pptx.table-no-header": "Mark the header row in the slide master's table style.",
    "pptx.missing-title": "Set the title in the slide master's presentation properties.",
    "pptx.slide-no-title": "Give every layout in the slide master a title placeholder.",
    "pdf.untagged": (
        "Fix the export: 'Document structure tags for accessibility' on in Word and PowerPoint."
    ),
    "pdf.missing-language": "Set the language in the source files; the export carries it.",
    "pdf.missing-title": "Set the title in the source files; the export carries it.",
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
                        proposal=_SYSTEMIC_PROPOSALS.get(
                            check, "Find what these files have in common and fix it there."
                        ),
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

    def not_evaluated(self) -> list[str]:
        """The union of every file's not-evaluated list, in first-seen order."""
        seen: list[str] = []
        for report in self.reports:
            for item in report.not_evaluated:
                if item not in seen:
                    seen.append(item)
        return seen

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain types, including the rendered Markdown."""
        return {
            "files": len(self.reports),
            "skipped": list(self.skipped),
            "counts_by_route": self.counts_by_route(),
            "systemic": [s.to_dict() for s in self.systemic()],
            "reports": [r.to_dict() for r in self.reports],
            "not_evaluated": self.not_evaluated(),
            "bounded_claim": BOUNDED_CLAIM,
            "markdown": render_markdown(self),
        }


def _row(asset: str, finding: Finding) -> str:
    closure = finding.closure_required.value.replace("_", " ")
    draft = "yes" if finding.proposal else ("tool" if finding.fix_id else "")
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
    lines.append(f"# Triage: {n_files} file{'s' if n_files != 1 else ''}")
    lines.append("")
    lines.append(
        "Findings by route: "
        + " · ".join(f"Route {r}: {n}" for r, n in counts.items())
        + ". Owner column is blank on purpose: it wants a name."
    )
    lines.append("")
    lines.append(
        "| File | Finding | Criterion | Route | Owner (a name) | Closure needed | Draft? |"
    )
    lines.append("| :--- | :--- | :--- | :-: | :--- | :--- | :-: |")
    for report in batch.reports:
        for finding in report.findings:
            lines.append(_row(report.asset, finding))
    if not any(r.findings for r in batch.reports):
        lines.append("| | no findings in the evaluated criteria | | | | | |")

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
    for note in batch.not_evaluated():
        lines.append(f"- {note}")

    lines.append("")
    lines.append("## What you may say")
    lines.append("")
    lines.append(f"> {BOUNDED_CLAIM}")
    lines.append("")
    lines.append(f"*{CLOSING_SENTENCE}*")
    lines.append("")
    return "\n".join(lines)
