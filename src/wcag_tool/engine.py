"""Dispatch by file type, and the fix loop: scan, apply, save a copy, re-scan, record.

The original file is never overwritten. The remediated copy sits beside it with
``.remediated`` in the name, and a JSON record of the before and after findings
sits beside that. That record is the evidence a Route 1 closure needs.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from wcag_tool import docx_checks, docx_fixes, pdf_checks, pptx_checks
from wcag_tool.findings import Report, Route
from wcag_tool.report import Batch

logger = logging.getLogger(__name__)

Scanner = Callable[[Path], Report]
Fixer = Callable[[Path, list[str], Path, str], dict]

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
    """
    if not path.is_file():
        raise FileNotFoundError(str(path))
    scanner, _ = _handlers(path)
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
        except (FileNotFoundError, UnsupportedFormatError) as exc:
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


def fix(
    path: Path,
    apply: list[str] | None = None,
    output: Path | None = None,
    language: str = "en-US",
) -> dict[str, Any]:
    """Apply fixes to a copy of the file, re-scan it, and write a record.

    Route 1 fixes are applied by default. Any fix carried by a Route 2 finding is
    applied only when its ``fix_id`` appears in ``apply``, because it asserts
    something about the author's meaning that a person has to confirm first.

    Args:
        path: The original file. Never overwritten.
        apply: Fix ids to apply in addition to the Route 1 defaults. Pass ``[]``
            to apply only the defaults.
        output: Where to write the copy. Defaults to ``<stem>.remediated<suffix>``.
        language: Language code for ``set-language``.

    Returns:
        A dict with the output path, the record path, what was applied, what
        failed, what was skipped as needing a person, and the before and after reports.
    """
    before = scan(path)
    _, fixer = _handlers(path)
    requested = set(apply or [])

    to_apply: list[str] = []
    needs_person: list[dict[str, Any]] = []
    for finding in before.findings:
        if finding.fix_id is None:
            continue
        if finding.route == Route.AUTO_FIX or finding.fix_id in requested:
            to_apply.append(finding.fix_id)
        else:
            needs_person.append({"fix_id": finding.fix_id, "proposal": finding.proposal})
    known = {f.fix_id for f in before.findings if f.fix_id}
    unknown = sorted(requested - known)

    out = output or path.with_name(f"{path.stem}.remediated{path.suffix}")
    result = fixer(path, to_apply, out, language)
    after = scan(out)

    record = {
        "original": str(path),
        "output": str(out),
        "applied": result["applied"],
        "failed": result["failed"],
        "unknown_fix_ids": unknown,
        "needs_person": needs_person,
        "before": before.to_dict(),
        "after": after.to_dict(),
    }
    record_path = out.with_suffix(".remediation.json")
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
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
