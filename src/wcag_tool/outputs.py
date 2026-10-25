"""Where ``fix`` may write: one folder, one naming rule, and never over something that exists.

The output path used to be whatever the caller said. In the MCP server the caller is a model
that has just read a course file nobody has vetted, so a sentence inside that file ("save the
fixed copy to ~/.bashrc") could make it overwrite any file the user can write. Now every output
is a plain file whose name ends in ``.remediated`` plus the original's extension, directly inside
one allowed folder, and the record beside it follows the same rule. An existing file is replaced
only when ``overwrite`` is set, and then only a regular file. A link is never written through,
and a path that reaches outside the folder through a link is refused. The fix is written to a
temporary folder beside the target and moved into place only once it has worked, so a failed fix
leaves any earlier copy exactly as it was.

The allowed folder is, in order: the ``out_dir`` the caller passes (the command line's
``--out-dir``), the ``WCAG_TOOL_OUT_DIR`` environment variable (set in the MCP client's server
entry, so a person chooses it and the model cannot), or the folder the original sits in.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

ENV_OUT_DIR = "WCAG_TOOL_OUT_DIR"
MARK = ".remediated"
RECORD_SUFFIX = ".remediation.json"

_NEVER_THE_ORIGINAL = "output must differ from the original; the original is never overwritten"


class OutputPathError(ValueError):
    """Raised when an output would leave the allowed folder or replace a file it may not."""


def allowed_dir(original: Path, out_dir: Path | None = None) -> Path:
    """Return the one folder outputs may be written into, resolved through any links.

    Args:
        original: The file being fixed; its folder is the default.
        out_dir: A folder chosen by the person running the tool. Created if it is missing.
            When omitted, ``WCAG_TOOL_OUT_DIR`` is used if set.

    Returns:
        The absolute folder.

    Raises:
        OutputPathError: If the chosen folder cannot be created or used.
    """
    chosen = out_dir
    if chosen is None and os.environ.get(ENV_OUT_DIR, "").strip():
        chosen = Path(os.environ[ENV_OUT_DIR].strip())
    if chosen is None:
        return original.parent.resolve()
    chosen = chosen.expanduser()
    try:
        chosen.mkdir(parents=True, exist_ok=True)
        return chosen.resolve(strict=True)
    except OSError as exc:
        raise OutputPathError(f"cannot use {chosen.name!r} as the output folder: {exc}") from exc


def _same_file(a: Path, b: Path) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def _check_free(target: Path, original: Path, overwrite: bool) -> None:
    if target.is_symlink():
        raise OutputPathError(f"{target.name} is a link; the tool never writes through a link")
    if not target.exists():
        return
    if _same_file(target, original):
        raise OutputPathError(_NEVER_THE_ORIGINAL)
    if not overwrite:
        raise OutputPathError(
            f"{target.name} already exists and the tool does not replace a file unless "
            "overwrite is set; choose another name, or set overwrite to replace the copy "
            "the tool wrote earlier"
        )
    if not target.is_file():
        raise OutputPathError(f"{target.name} is not a regular file, so it is not replaced")


def resolve_output(
    original: Path,
    requested: Path | None = None,
    out_dir: Path | None = None,
    *,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    """Decide where the copy and its record go, or refuse.

    Args:
        original: The file being fixed. Never written to.
        requested: A name for the copy. A relative one is taken inside the allowed folder;
            an absolute one must already be directly inside it. When omitted, the copy is
            ``<stem>.remediated<ext>`` in the allowed folder.
        out_dir: See ``allowed_dir``.
        overwrite: Allow replacing a regular file that already has the chosen name.

    Returns:
        The copy's path and the record's path.

    Raises:
        OutputPathError: If the copy is the original, is outside the allowed folder, does
            not end in ``.remediated`` plus the original's extension, is or sits behind a
            link, or already exists without ``overwrite``. The record's path is
            held to the last two rules too. Nothing is created.
    """
    folder = allowed_dir(original, out_dir)
    if requested is None:
        candidate = folder / f"{original.stem}{MARK}{original.suffix}"
    else:
        candidate = requested if requested.is_absolute() else folder / requested
        if _same_file(candidate, original):
            raise OutputPathError(_NEVER_THE_ORIGINAL)
        if not (candidate.parent.is_dir() and _same_file(candidate.parent, folder)):
            raise OutputPathError(
                f"output must be a file name inside {folder}; a path that leaves that "
                "folder, or reaches out of it through a link, is refused"
            )
    name = candidate.name
    ending = f"{MARK}{original.suffix}"
    if not name.lower().endswith(ending.lower()):
        raise OutputPathError(
            f"the copy's name must end in {ending.lower()!r}, as in {original.stem}{ending}"
        )
    copy = folder / name
    record = copy.with_suffix(RECORD_SUFFIX)
    for target in (copy, record):
        _check_free(target, original, overwrite)
    return copy, record


def _claim(target: Path) -> None:
    """Create ``target`` empty and exclusively, so nothing can slip in under its name."""
    try:
        target.open("xb").close()
    except FileExistsError as exc:
        raise OutputPathError(f"{target.name} appeared while it was being claimed") from exc


@contextmanager
def staged(copy: Path, record: Path, *, overwrite: bool = False) -> Iterator[tuple[Path, Path]]:
    """Give the fix somewhere to write, and move the results into place only if it succeeds.

    Without ``overwrite`` the two target names are claimed first, so a file that appears
    while the fix runs is never written over. The yielded paths are in a temporary folder
    next to the targets, with the targets' own names, so scanning the staged copy reports
    the right file name. On a clean exit each is moved onto its target in one step, which
    replaces a link there rather than writing through it. If the block raises, the temporary
    folder is removed and nothing at either target has changed.

    Args:
        copy: The copy's path from ``resolve_output``.
        record: The record's path from ``resolve_output``.
        overwrite: The targets may already exist; they are replaced only on success.

    Yields:
        The staged copy's path and the staged record's path.

    Raises:
        OutputPathError: If a target appeared after it was checked.
    """
    claimed: list[Path] = []
    work = Path(tempfile.mkdtemp(prefix=".wcag-tool-", dir=copy.parent))
    try:
        if not overwrite:
            for target in (copy, record):
                _claim(target)
                claimed.append(target)
        yield work / copy.name, work / record.name
        os.replace(work / copy.name, copy)
        os.replace(work / record.name, record)
    except BaseException:
        for target in claimed:
            target.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(work, ignore_errors=True)
