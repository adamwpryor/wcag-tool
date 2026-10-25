"""Dispatch by file type, and the fix loop: scan, apply, save a copy, re-scan, record.

The original file is never overwritten. The remediated copy sits beside it with
``.remediated`` in the name, and a JSON record of the before and after findings
sits beside that. That record is the evidence a Route 1 closure needs. Where the copy
may go, and when an existing file may be replaced, is decided in ``outputs``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from wcag_tool import docx_checks, docx_fixes, limits, outputs, pdf_checks, pptx_checks
from wcag_tool.findings import Report, Route
from wcag_tool.report import Batch

logger = logging.getLogger(__name__)

Scanner = Callable[[Path], Report]
Fixer = Callable[[Path, list[str], Path, str, str | None], dict]

_HANDLERS: dict[str, tuple[Scanner, Fixer]] = {
    ".docx": (docx_checks.scan, docx_fixes.apply),
    ".pptx": (pptx_checks.scan, pptx_checks.apply),
    ".pdf": (pdf_checks.scan, pdf_checks.apply),
}

SUPPORTED = tuple(_HANDLERS)


class UnsupportedFormatError(ValueError):
    """Raised for a file type the tool does not read."""


def _handlers(path: Path) -> tuple[Scanner, Fixer]:
    try:
        return _HANDLERS[path.suffix.lower()]
    except KeyError as exc:
        raise UnsupportedFormatError(
            f"{path.suffix or 'no extension'} is not supported; supported: {', '.join(SUPPORTED)}"
        ) from exc


def scan(path: Path) -> Report:
    """Scan one file.

    Args:
        path: The file to scan.

    Returns:
        The routed report.

    Raises:
        FileNotFoundError: If the path does not exist.
        UnsupportedFormatError: If the extension is not handled.
        limits.InputLimitError: If the file is over a size, package or page limit.
    """
    if not path.is_file():
        raise FileNotFoundError(str(path))
    scanner, _ = _handlers(path)
    limits.preflight(path)
    report = scanner(path)
    logger.info(
        "scanned",
        extra={
            "data": {
                "asset": path.name,
                "findings": len(report.findings),
                "routes": report.by_route(),
            }
        },
    )
    return report


def scan_many(paths: list[Path]) -> Batch:
    """Scan several files into one batch, recording the ones that could not be scanned.

    Args:
        paths: Files to scan. Unsupported or missing paths are recorded, not raised.

    Returns:
        The batch.
    """
    batch = Batch()
    for path in paths:
        try:
            batch.reports.append(scan(path))
        except (FileNotFoundError, UnsupportedFormatError, limits.InputLimitError) as exc:
            batch.skipped.append({"path": str(path), "reason": str(exc)})
        except Exception as exc:  # a corrupt file must not stop the pile
            logger.warning("skipped", extra={"data": {"path": str(path), "error": repr(exc)}})
            batch.skipped.append({"path": str(path), "reason": f"could not open: {exc}"})
    return batch


def iter_supported(folder: Path, recursive: bool = True) -> list[Path]:
    """List the supported files under a folder, skipping Office lock files and our own outputs.

    Args:
        folder: The folder to walk.
        recursive: Whether to descend into subfolders.

    Returns:
        Sorted paths.
    """
    pattern = folder.rglob if recursive else folder.glob
    out: list[Path] = []
    for path in sorted(pattern("*")):
        if not path.is_file() or path.suffix.lower() not in _HANDLERS:
            continue
        if path.name.startswith("~$") or ".remediated" in path.name:
            continue
        out.append(path)
    return out


def scan_folder(folder: Path, recursive: bool = True) -> Batch:
    """Scan every supported file under a folder.

    Args:
        folder: The folder to walk.
        recursive: Whether to descend into subfolders.

    Returns:
        The batch.

    Raises:
        NotADirectoryError: If ``folder`` is not a directory.
    """
    if not folder.is_dir():
        raise NotADirectoryError(str(folder))
    return scan_many(iter_supported(folder, recursive=recursive))


def _same_fix(requested: str, carried: str) -> bool:
    """True when a requested id names the fix a finding carries.

    ``apply-heading:<paragraph>:<level>`` matches on the paragraph alone, so a
    person can confirm a heading at a different level than the one proposed.
    """
    if requested == carried:
        return True
    r, c = requested.split(":"), carried.split(":")
    return r[0] == c[0] == "apply-heading" and len(r) == len(c) == 3 and r[1] == c[1]


def _open_finding(finding: Any) -> dict[str, Any]:
    return {
        "check": finding.check,
        "criterion": finding.criterion,
        "locator": finding.locator,
        "route": int(finding.route),
        "closure_required": finding.closure_required.value,
        "fix_id": finding.fix_id,
        "proposal": finding.proposal,
    }


def fix(
    path: Path,
    apply: list[str] | None = None,
    output: Path | None = None,
    language: str | None = None,
    title: str | None = None,
    out_dir: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Apply fixes to a copy of the file, re-scan it, and write a record.

    Route 1 fixes are applied by default, with one exception: ``set-language``
    is held until a person names the language, because writing ``en-US`` into a
    file nobody has looked at invents a fact. Any fix carried by a Route 2
    finding is applied only when its ``fix_id`` appears in ``apply``.

    Args:
        path: The original file. Never overwritten.
        apply: Fix ids a person has confirmed, taken from a prior scan. Pass
            ``[]`` or nothing to apply only the Route 1 defaults.
        output: A name for the copy, inside the output folder, containing ``.remediated``
            and ending in the original's extension. Defaults to ``<stem>.remediated<suffix>``.
            Must not be the original.
        language: Language code for ``set-language`` (``en-US``, ``es-ES``). When
            omitted, ``set-language`` is reported under ``held`` and left open.
        title: The title the person named for ``set-title``. When omitted, the title is
            taken from the file (a heading, the first slide title, or the file name) and
            the applied note says where it came from and asks for a check.
        out_dir: The one folder the copy and record may be written to. Defaults to
            ``WCAG_TOOL_OUT_DIR`` if set, else the original's folder.
        overwrite: Replace a copy and record the tool wrote earlier under the same name.
            Without it, an existing file is never replaced.

    Returns:
        A record: paths, ``applied``, ``failed``, ``unknown_fix_ids``, ``held``,
        ``needs_person`` (every finding still open after the fix), and the before
        and after reports.

    Raises:
        outputs.OutputPathError: A ``ValueError``. If ``output`` is the original, is outside
            the output folder, is not named like a remediated copy, goes through a link, or
            names a file that already exists and ``overwrite`` is not set.
    """
    before = scan(path)
    _, fixer = _handlers(path)
    requested = list(dict.fromkeys(apply or []))

    out, record_path = outputs.resolve_output(path, output, out_dir, overwrite=overwrite)

    to_apply: list[str] = []
    held: list[dict[str, Any]] = []
    matched: set[str] = set()
    for finding in before.findings:
        if finding.fix_id is None:
            continue
        chosen = next((r for r in requested if _same_fix(r, finding.fix_id)), None)
        if chosen is not None:
            matched.add(chosen)
        if finding.fix_id == "set-language" and language is None:
            held.append(
                {
                    "fix_id": "set-language",
                    "reason": "no language named; pass language='en-US' or another code",
                }
            )
            continue
        if finding.route == Route.AUTO_FIX or chosen is not None:
            to_apply.append(chosen or finding.fix_id)
    unknown = [r for r in requested if r not in matched]

    named_title = (title or "").strip() or None
    claimed: list[Path] = []
    try:
        for target in (out, record_path):
            outputs.claim(target, overwrite=overwrite)
            claimed.append(target)
        result = fixer(path, to_apply, out, language or "en-US", named_title)
        after = scan(out)

        record = {
            "original": str(path),
            "output": str(out),
            "language": language,
            "title": named_title,
            "applied": result["applied"],
            "failed": result["failed"],
            "unknown_fix_ids": unknown,
            "held": held,
            "needs_person": [_open_finding(f) for f in after.findings],
            "before": before.to_dict(),
            "after": after.to_dict(),
        }
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    except BaseException:
        for target in claimed:  # a failed fix leaves no half-written copy behind
            target.unlink(missing_ok=True)
        raise
    logger.info(
        "fixed",
        extra={
            "data": {
                "asset": path.name,
                "applied": len(result["applied"]),
                "failed": len(result["failed"]),
                "before": len(before.findings),
                "after": len(after.findings),
            }
        },
    )
    return record
