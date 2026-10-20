"""The finding model: one record per defect, routed and carrying a closure state.

This encodes the triage pipeline the tool exists to teach. A finding is never a
score. It has a route (who acts) and a closure state (what evidence is needed
before anyone may call it done). "No longer reported by the scanner" is not a
closure state.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum, StrEnum
from typing import Any

from wcag_tool import rules


class Route(int, Enum):
    """Where a finding goes. Decided by what the fix needs, not by how easy it is."""

    AUTO_FIX = 1
    """Deterministic defect. Reversible repair that invents no meaning."""
    CONTENT_OWNER = 2
    """The machine found a likely problem but cannot establish its meaning."""
    MANUAL_TEST = 3
    """Only a person with assistive technology and a named task can judge it."""
    EXPEDITED = 4
    """A currently enrolled student, a high-stakes task, or a deadline. Overrides."""
    SYSTEMIC = 5
    """Same defect across many files. Fix the template, not the instance."""


class Closure(StrEnum):
    """The four evidence states that may close a finding."""

    AUTOMATICALLY_VERIFIED = "automatically_verified"
    CONTENT_OWNER_VERIFIED = "content_owner_verified"
    EXPERT_VERIFIED = "expert_verified"
    USER_TASK_VERIFIED = "user_task_verified"


class Confidence(StrEnum):
    """How sure the check is that the defect exists at all."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(StrEnum):
    """Lifecycle of a finding inside one run."""

    OPEN = "open"
    FIXED = "fixed"
    PROPOSED = "proposed"
    FAILED = "failed"


@dataclass
class Finding:
    """One defect in one place in one file.

    Attributes:
        check: Stable check id, e.g. ``docx.missing-title``.
        criterion: The WCAG 2.1 success criterion, e.g. ``2.4.2 Page Titled``.
        asset: File name the finding belongs to.
        locator: Where in the file: ``core properties``, ``paragraph 12``, ``slide 3``.
        evidence: What the check saw, in plain words.
        route: The route this finding takes.
        closure_required: The evidence state needed before it can be closed.
        confidence: How sure the check is.
        status: Lifecycle state within this run.
        fix_id: Identifier of a fix the tool can apply, if any.
        proposal: A suggested resolution for a person to confirm. Never applied silently.
        id: Stable short id derived from asset, check and locator.
    """

    check: str
    criterion: str
    asset: str
    locator: str
    evidence: str
    route: Route
    closure_required: Closure
    confidence: Confidence
    status: Status = Status.OPEN
    fix_id: str | None = None
    proposal: str | None = None
    id: str = field(init=False)

    def __post_init__(self) -> None:
        """Derive the stable id."""
        raw = f"{self.asset}|{self.check}|{self.locator}".encode()
        self.id = hashlib.sha1(raw).hexdigest()[:12]  # noqa: S324 - identifier, not security

    @classmethod
    def from_check(
        cls,
        check: str,
        *,
        asset: str,
        locator: str,
        evidence: str,
        fix_id: str | None = None,
        proposal: str | None = None,
    ) -> Finding:
        """Build a finding whose criterion, route, closure and wording come from ``checks.json``.

        The scanner supplies only what it saw: where, and the evidence. Everything the
        skill and the bot must agree on comes from the rule files.

        Args:
            check: A check id from ``checks.json``.
            asset: File name.
            locator: Where in the file.
            evidence: What the check saw.
            fix_id: The filled-in fix id when the check's fix takes arguments.
            proposal: A proposal worded for this instance, replacing the check's default.

        Returns:
            The finding.
        """
        rule_set = rules.load()
        spec = rule_set.checks[check]
        return cls(
            check=check,
            criterion=rule_set.criteria[spec.criterion].label,
            asset=asset,
            locator=locator,
            evidence=evidence,
            route=Route(spec.route),
            closure_required=Closure(spec.closure),
            confidence=Confidence(spec.confidence),
            fix_id=rule_set.resolve_fix_id(check, fix_id),
            proposal=proposal or spec.proposal,
        )

    @property
    def criterion_id(self) -> str:
        """The criterion number alone, e.g. ``2.4.2``."""
        return self.criterion.split(" ", 1)[0]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain JSON-able types."""
        data = asdict(self)
        data["route"] = int(self.route)
        data["closure_required"] = self.closure_required.value
        data["confidence"] = self.confidence.value
        data["status"] = self.status.value
        return data


BOUNDED_CLAIM = (
    "This file was checked for the criteria listed under `evaluated` only. Route 1 findings "
    "can be repaired by the tool and re-scanned; Route 2 findings carry proposals that a "
    "person who knows the content must confirm; criteria under `not_evaluated` were not "
    "checked at all. A clean report is not a conformance claim."
)


@dataclass
class Report:
    """The result of scanning one file.

    Attributes:
        asset: File name.
        format: ``docx``, ``pptx`` or ``pdf``.
        findings: Every finding, open or otherwise.
        evaluated: Criteria the checks actually covered.
        not_evaluated: Everything the checks do not settle, for every A and AA criterion,
            with who can judge it.
        coverage: Criterion ids by status: ``checked_in_part``, ``not_checked``,
            ``if_present``.
    """

    asset: str
    format: str
    findings: list[Finding] = field(default_factory=list)
    evaluated: list[str] = field(default_factory=list)
    not_evaluated: list[str] = field(default_factory=list)
    coverage: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def for_format(cls, asset: str, fmt: str) -> Report:
        """An empty report whose evaluated, not-evaluated and coverage come from the rules."""
        rule_set = rules.load()
        return cls(
            asset=asset,
            format=fmt,
            evaluated=rule_set.evaluated(fmt),
            not_evaluated=rule_set.not_evaluated(fmt),
            coverage=rule_set.coverage_summary(fmt),
        )

    def by_route(self) -> dict[int, int]:
        """Count findings per route."""
        counts: dict[int, int] = {r.value: 0 for r in Route}
        for finding in self.findings:
            counts[int(finding.route)] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain JSON-able types."""
        return {
            "asset": self.asset,
            "format": self.format,
            "findings": [f.to_dict() for f in self.findings],
            "counts_by_route": self.by_route(),
            "evaluated": list(self.evaluated),
            "not_evaluated": list(self.not_evaluated),
            "coverage": {k: list(v) for k, v in self.coverage.items()},
            "criteria": rules.load().criteria_detail([f.criterion_id for f in self.findings]),
            "bounded_claim": BOUNDED_CLAIM,
        }


ROUTES_SUMMARY = """Five routes. The route is decided by what the fix needs, not by how easy it is.

1. Deterministic defect -> automatic repair. The rule is deterministic, the repair invents
   no meaning, it is reversible and re-scannable, and it cannot silently alter an assessment.
   In this tool: document title, and document language once a person names it.
2. Machine finding -> content-owner review. The tool found a likely problem but cannot
   establish its meaning: alt text, link purpose, headings, table structure. The tool may
   propose; the person who made the file confirms.
3. Interaction defect -> manual task testing. Keyboard, focus, reading order, screen-reader
   announcements. Tested against a named task, never a general impression. The tool never
   emits Route 3; a person adds those rows.
4. High-impact or time-sensitive -> expedited review. A currently enrolled student, a
   high-stakes task, accommodation information. Overrides the other routes. The tool never
   emits Route 4; a person overwrites the route for the file that needs it.
5. Recurring systemic defect -> template or source. Fix it once where the copies come from.
   scan_folder lists candidates.

Four closure states: automatically_verified, content_owner_verified, expert_verified,
user_task_verified. Closure is recorded by a person. "No longer reported by the scanner"
is not one of them.
"""
