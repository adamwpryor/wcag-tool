"""Where ``fix`` may write: one folder, one naming rule, and never over something that exists.

The output path used to be whatever the caller said. In the MCP server the caller is a model
that has just read a course file nobody has vetted, so a sentence inside that file ("save the
fixed copy to ~/.bashrc") could make it overwrite any file the user can write. Now every output
is a plain ``*.remediated.<ext>`` file with the original's extension, directly inside one allowed
folder, and the record beside it follows the same rule. An existing file is replaced only when
``overwrite`` is set, and then only a regular file that already has that name shape. A link is
never written through, and a path that reaches outside the folder through a link is refused.

The allowed folder is, in order: the ``out_dir`` the caller passes (the command line's
``--out-dir``), the ``WCAG_TOOL_OUT_DIR`` environment variable (set in the MCP client's server
entry, so a person chooses it and the model cannot), or the folder the original sits in.
"""

from __future__ import annotations

import os
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
            not have ``.remediated`` in its name and the original's extension, is or sits
            behind a link, or already exists without ``overwrite``. The record's path is
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
    if MARK not in name or Path(name).suffix.lower() != original.suffix.lower():
        raise OutputPathError(
            f"the copy's name must contain {MARK!r} and end in {original.suffix.lower()!r}, "
            f"as in {original.stem}{MARK}{original.suffix}"
        )
    copy = folder / name
    record = copy.with_suffix(RECORD_SUFFIX)
    for target in (copy, record):
        _check_free(target, original, overwrite)
    return copy, record


def claim(target: Path, *, overwrite: bool = False) -> None:
    """Create ``target`` empty, exclusively, so what is written next cannot follow a link.

    Args:
        target: A path that ``resolve_output`` returned.
        overwrite: Remove a regular file already at ``target`` first.

    Raises:
        OutputPathError: If something appeared at ``target`` after it was checked.
    """
    if overwrite and target.is_file() and not target.is_symlink():
        target.unlink()
    try:
        target.open("xb").close()
    except FileExistsError as exc:
        raise OutputPathError(f"{target.name} appeared while it was being claimed") from exc
