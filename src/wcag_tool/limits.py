"""Limits on what the parsers are asked to open, checked before they open it.

Course files come from anywhere: a download, a shared drive, an email. The readers behind this
tool (python-docx, python-pptx, pypdf) load a whole file into memory and set no ceiling of their
own, so one hostile or merely enormous file could stop a ``scan_folder`` over a pile, or fill the
model's context through ``extract_content``. The checks here are cheap and run first.

Every file: a size cap. Word and PowerPoint (ZIP packages): a cap on the number of parts, on
their declared uncompressed sizes added together, and on the compression ratio of any large
part, and only stored or deflated parts are accepted (CPython unpacks bzip2 and lzma parts with
no output limit). PDF: a cap on pages and on objects. The defaults are generous for course
material; each can be raised with an environment variable in the MCP client's server entry.
"""

from __future__ import annotations

import os
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MIB = 1024 * 1024
OOXML = (".docx", ".pptx")

# The one-record tail of a ZIP file: signature, then the fields read below.
_EOCD = b"PK\x05\x06"
_EOCD_SEARCH = 22 + 0xFFFF  # the record plus the longest comment a ZIP may carry
_ZIP64_MARK = 0xFFFF


class InputLimitError(ValueError):
    """Raised when a file is larger or more complex than this tool will open."""


@dataclass(frozen=True)
class Limits:
    """The ceilings, each with the environment variable that raises it."""

    max_file_bytes: int = 50 * MIB  # WCAG_TOOL_MAX_FILE_MB
    max_zip_members: int = 2_000  # WCAG_TOOL_MAX_ZIP_MEMBERS
    max_zip_uncompressed: int = 200 * MIB  # WCAG_TOOL_MAX_ZIP_UNCOMPRESSED_MB
    max_zip_ratio: int = 100  # WCAG_TOOL_MAX_ZIP_RATIO, for parts over ratio_floor_bytes
    ratio_floor_bytes: int = 1 * MIB
    max_pdf_pages: int = 500  # WCAG_TOOL_MAX_PDF_PAGES
    max_pdf_objects: int = 250_000  # WCAG_TOOL_MAX_PDF_OBJECTS

    @classmethod
    def from_env(cls) -> Limits:
        """Read the ceilings, taking any set in the environment over the defaults.

        Returns:
            The limits.

        Raises:
            ValueError: If a variable is set to something other than a positive whole number.
        """
        base = cls()

        def number(name: str, default: int, unit: int = 1) -> int:
            raw = os.environ.get(name, "").strip()
            if not raw:
                return default
            if not raw.isdigit() or int(raw) < 1:
                raise ValueError(f"{name} must be a positive whole number, not {raw!r}")
            return int(raw) * unit

        return cls(
            max_file_bytes=number("WCAG_TOOL_MAX_FILE_MB", base.max_file_bytes, MIB),
            max_zip_members=number("WCAG_TOOL_MAX_ZIP_MEMBERS", base.max_zip_members),
            max_zip_uncompressed=number(
                "WCAG_TOOL_MAX_ZIP_UNCOMPRESSED_MB", base.max_zip_uncompressed, MIB
            ),
            max_zip_ratio=number("WCAG_TOOL_MAX_ZIP_RATIO", base.max_zip_ratio),
            max_pdf_pages=number("WCAG_TOOL_MAX_PDF_PAGES", base.max_pdf_pages),
            max_pdf_objects=number("WCAG_TOOL_MAX_PDF_OBJECTS", base.max_pdf_objects),
        )


def _mb(size: int) -> str:
    return f"{size / MIB:,.0f} MB"


def _declared_central_directory(path: Path) -> tuple[int, int] | None:
    """The entry count and byte size a ZIP's end record declares, without reading the rest.

    ``zipfile`` builds an object for every entry in the central directory before a caller can
    count them, so a small file full of tiny entries is cheaper to refuse from the end record.
    """
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - _EOCD_SEARCH))
        tail = handle.read()
    at = tail.rfind(_EOCD)
    if at < 0 or len(tail) < at + 22:
        return None
    entries, directory_bytes = struct.unpack_from("<HI", tail, at + 10)
    return entries, directory_bytes


def check_zip(path: Path, limits: Limits) -> None:
    """Refuse a Word or PowerPoint package that looks like a zip bomb.

    Args:
        path: The ``.docx`` or ``.pptx`` file.
        limits: The ceilings.

    Raises:
        InputLimitError: If it has too many parts, declares too much uncompressed data, has a
            large part that compresses implausibly well, or uses a compression method other
            than stored or deflated. A file that is not a ZIP is left for the reader to report.
    """
    declared = _declared_central_directory(path)
    if declared is not None:
        entries, directory_bytes = declared
        if (
            entries == _ZIP64_MARK
            or entries > limits.max_zip_members
            or directory_bytes > limits.max_zip_members * 1024
        ):
            raise InputLimitError(
                f"{path.name} has too many parts to be a course document "
                f"(the limit is {limits.max_zip_members:,})."
            )
    try:
        with zipfile.ZipFile(path) as package:
            parts = package.infolist()
    except zipfile.BadZipFile:
        return
    if len(parts) > limits.max_zip_members:
        raise InputLimitError(
            f"{path.name} has {len(parts):,} parts; the limit is {limits.max_zip_members:,}."
        )
    total = sum(p.file_size for p in parts)
    if total > limits.max_zip_uncompressed:
        raise InputLimitError(
            f"{path.name} would unpack to {_mb(total)}; the limit is "
            f"{_mb(limits.max_zip_uncompressed)}. It may be a decompression bomb."
        )
    for part in parts:
        if part.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            raise InputLimitError(
                f"{path.name} uses a compression method Word and PowerPoint do not use."
            )
        ratio = part.file_size / max(part.compress_size, 1)
        if part.file_size > limits.ratio_floor_bytes and ratio > limits.max_zip_ratio:
            raise InputLimitError(
                f"{path.name} has a part that unpacks to {_mb(part.file_size)} from "
                f"{ratio:,.0f} times less; it may be a decompression bomb."
            )


def preflight(path: Path, limits: Limits | None = None) -> None:
    """Check a file's size, and a Word or PowerPoint file's package, before it is opened.

    Args:
        path: The file to be read. It must exist.
        limits: The ceilings. Defaults to the environment's, else the built-in defaults.

    Raises:
        InputLimitError: If the file is over a ceiling.
    """
    limits = limits or Limits.from_env()
    size = path.stat().st_size
    if size > limits.max_file_bytes:
        raise InputLimitError(
            f"{path.name} is {_mb(size)}; the limit is {_mb(limits.max_file_bytes)}. "
            "Split it, or raise WCAG_TOOL_MAX_FILE_MB."
        )
    if path.suffix.lower() in OOXML:
        check_zip(path, limits)


def check_pdf(reader: Any, name: str, limits: Limits | None = None) -> None:
    """Refuse a PDF with too many pages or objects, once its table of contents is read.

    Args:
        reader: An open ``pypdf.PdfReader``.
        name: The file's name, for the message.
        limits: The ceilings. Defaults to the environment's, else the built-in defaults.

    Raises:
        InputLimitError: If the page count or the object count is over a ceiling.
    """
    limits = limits or Limits.from_env()
    pages = len(reader.pages)
    if pages > limits.max_pdf_pages:
        raise InputLimitError(
            f"{name} has {pages:,} pages; the limit is {limits.max_pdf_pages:,}. "
            "Split it, or raise WCAG_TOOL_MAX_PDF_PAGES."
        )
    objects = sum(len(group) for group in getattr(reader, "xref", {}).values()) + len(
        getattr(reader, "xref_objStm", {})
    )
    if objects > limits.max_pdf_objects:
        raise InputLimitError(
            f"{name} holds {objects:,} objects; the limit is {limits.max_pdf_objects:,}."
        )
