"""Checks and fixes for PowerPoint decks (.pptx).

Reading order is the defect that matters most in slides and the one the tool
cannot judge, so it is listed under not-evaluated with instructions rather than
guessed at.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from wcag_tool.alt import is_missing_or_placeholder
from wcag_tool.findings import Closure, Confidence, Finding, Report, Route

EVALUATED = [
    "1.1.1 Non-text Content (alt text present and not a filename or auto-generated phrase)",
    "1.3.1 Info and Relationships (every slide has a title placeholder with text)",
    "2.4.2 Page Titled (presentation title)",
]

NOT_EVALUATED = [
    "1.3.2 Meaningful Sequence: reading order follows the selection pane and only a person "
    "can judge it",
    "1.4.3 Contrast: not analyzed yet",
    "1.2.x Audio and video: embedded media captions are not analyzed",
    "Tables: header rows in slide tables are not analyzed yet",
]


def scan(path: Path) -> Report:
    """Scan one .pptx file and return a routed report.

    Args:
        path: Path to the deck.

    Returns:
        The report.
    """
    prs = Presentation(str(path))
    asset = path.name
    report = Report(asset=asset, format="pptx", evaluated=EVALUATED, not_evaluated=NOT_EVALUATED)
    f = report.findings

    if not (prs.core_properties.title or "").strip():
        f.append(
            Finding(
                check="pptx.missing-title",
                criterion="2.4.2 Page Titled",
                asset=asset,
                locator="core properties",
                evidence="The presentation title property is empty.",
                route=Route.AUTO_FIX,
                closure_required=Closure.AUTOMATICALLY_VERIFIED,
                confidence=Confidence.HIGH,
                fix_id="set-title",
            )
        )

    for number, slide in enumerate(prs.slides, start=1):
        title_shape = slide.shapes.title
        if title_shape is None or not title_shape.has_text_frame or not title_shape.text.strip():
            f.append(
                Finding(
                    check="pptx.slide-no-title",
                    criterion="1.3.1 Info and Relationships",
                    asset=asset,
                    locator=f"slide {number}",
                    evidence=(
                        "No title placeholder with text; screen readers announce the slide by "
                        "number only."
                    ),
                    route=Route.CONTENT_OWNER,
                    closure_required=Closure.CONTENT_OWNER_VERIFIED,
                    confidence=Confidence.HIGH,
                    proposal=(
                        "Give the slide a unique title in the title placeholder. It may be "
                        "visually hidden, but it must exist."
                    ),
                )
            )
        for shape in slide.shapes:
            if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                continue
            c_nv_pr = shape._element.xpath(".//p:cNvPr")
            descr = c_nv_pr[0].get("descr") if c_nv_pr else None
            if not is_missing_or_placeholder(descr):
                continue
            evidence = (
                "The picture has no alt text."
                if not (descr or "").strip()
                else (
                    "The alt text is a filename or an auto-generated phrase: "
                    f"{(descr or '').strip()[:60]!r}."
                )
            )
            f.append(
                Finding(
                    check="pptx.image-missing-alt",
                    criterion="1.1.1 Non-text Content",
                    asset=asset,
                    locator=f"slide {number}, {shape.name}",
                    evidence=evidence,
                    route=Route.CONTENT_OWNER,
                    closure_required=Closure.CONTENT_OWNER_VERIFIED,
                    confidence=Confidence.HIGH,
                    proposal=(
                        "Write one sentence saying what this picture conveys on this slide, or "
                        "mark it decorative."
                    ),
                )
            )
    return report


def apply(path: Path, fix_ids: list[str], output: Path, language: str = "en-US") -> dict:
    """Apply the named fixes and save to ``output``.

    Args:
        path: The original deck. Never overwritten.
        fix_ids: Fix identifiers. Only ``set-title`` exists for decks today.
        output: Where the remediated copy is written.
        language: Unused for decks; kept for a uniform signature.

    Returns:
        A dict with ``applied`` and ``failed``.
    """
    del language
    prs = Presentation(str(path))
    applied: dict[str, str] = {}
    failed: dict[str, str] = {}
    for fix_id in fix_ids:
        if fix_id == "set-title":
            first = next(
                (
                    s.shapes.title.text.strip()
                    for s in prs.slides
                    if s.shapes.title is not None and s.shapes.title.text.strip()
                ),
                path.stem.replace("_", " ").replace("-", " "),
            )
            prs.core_properties.title = first
            applied[fix_id] = f"title set to {first!r}"
        else:
            failed[fix_id] = "unknown fix"
    prs.save(str(output))
    return {"applied": applied, "failed": failed}
