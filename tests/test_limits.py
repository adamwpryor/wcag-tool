"""Size, zip-bomb and page limits: refused before the parsers are asked to open the file."""

import asyncio
import struct
import time
import zipfile
from pathlib import Path

import pytest
from mcp import Client
from pypdf import PdfWriter

from wcag_tool import assets, content, engine, limits
from wcag_tool.server import mcp

MIB = limits.MIB


def _zip(path: Path, members: dict[str, bytes], method: int = zipfile.ZIP_DEFLATED) -> Path:
    with zipfile.ZipFile(path, "w", compression=method) as package:
        for name, data in members.items():
            package.writestr(name, data)
    return path


def _declare_size(path: Path, size: int) -> None:
    """Rewrite the central directory so the first part claims to unpack to ``size`` bytes.

    The file stays a few hundred bytes: nothing is ever expanded.
    """
    raw = bytearray(path.read_bytes())
    at = raw.index(b"PK\x01\x02")
    struct.pack_into("<I", raw, at + 24, size)
    path.write_bytes(bytes(raw))


def _declare_entries(path: Path, entries: int) -> None:
    raw = bytearray(path.read_bytes())
    at = raw.rindex(b"PK\x05\x06")
    struct.pack_into("<H", raw, at + 10, entries)
    path.write_bytes(bytes(raw))


def _pdf(path: Path, pages: int) -> Path:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    with path.open("wb") as handle:
        writer.write(handle)
    return path


def _tiny_docx(tmp_path: Path) -> Path:
    return _zip(tmp_path / "tiny.docx", {"[Content_Types].xml": b"<Types/>", "word/a.xml": b"<a/>"})


# --- the ceilings and how they are set --------------------------------------------------------


def test_the_defaults() -> None:
    d = limits.Limits()
    assert d.max_file_bytes == 50 * MIB
    assert d.max_zip_members == 2_000 and d.max_zip_uncompressed == 200 * MIB
    assert d.max_pdf_pages == 500


def test_the_environment_raises_a_ceiling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WCAG_TOOL_MAX_FILE_MB", "80")
    monkeypatch.setenv("WCAG_TOOL_MAX_PDF_PAGES", "900")
    from_env = limits.Limits.from_env()
    assert from_env.max_file_bytes == 80 * MIB and from_env.max_pdf_pages == 900
    assert from_env.max_zip_members == 2_000


@pytest.mark.parametrize("bad", ["0", "-3", "lots", "1.5"])
def test_a_bad_setting_is_an_error_not_a_silent_default(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    monkeypatch.setenv("WCAG_TOOL_MAX_FILE_MB", bad)
    with pytest.raises(ValueError, match="WCAG_TOOL_MAX_FILE_MB"):
        limits.Limits.from_env()


# --- file size ---------------------------------------------------------------------------------


def test_a_file_over_the_size_cap_is_refused_before_it_is_parsed(tmp_path: Path) -> None:
    big = tmp_path / "huge.docx"  # not a real document: the size check must come first
    with big.open("wb") as handle:
        handle.truncate(50 * MIB + 1)
    with pytest.raises(limits.InputLimitError, match="50 MB"):
        engine.scan(big)


def test_the_size_cap_can_be_raised(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    small = _tiny_docx(tmp_path)
    monkeypatch.setenv("WCAG_TOOL_MAX_FILE_MB", "1")
    limits.preflight(small)
    with pytest.raises(limits.InputLimitError):
        limits.preflight(small, limits.Limits(max_file_bytes=10))


# --- zip bombs in Word and PowerPoint files ----------------------------------------------------


def test_a_small_zip_that_declares_a_four_gigabyte_part_is_refused(tmp_path: Path) -> None:
    path = _tiny_docx(tmp_path)
    _declare_size(path, 0xF0000000)
    assert path.stat().st_size < 4_096
    started = time.perf_counter()
    with pytest.raises(limits.InputLimitError, match="decompression bomb"):
        engine.scan(path)
    assert time.perf_counter() - started < 2


def test_every_way_in_checks_the_package(tmp_path: Path) -> None:
    path = _tiny_docx(tmp_path)
    _declare_size(path, 0xF0000000)
    with pytest.raises(limits.InputLimitError):
        content.extract(path)
    with pytest.raises(limits.InputLimitError):
        assets.extract(path, "Picture 1")


def test_a_part_that_compresses_far_too_well_is_refused(tmp_path: Path) -> None:
    # Two megabytes of zeros: a real ratio of about 1000 to one, and harmless to hold.
    path = _zip(tmp_path / "flat.docx", {"[Content_Types].xml": b"<Types/>", "w": bytes(2 * MIB)})
    with pytest.raises(limits.InputLimitError, match="decompression bomb"):
        limits.preflight(path)


def test_small_repetitive_parts_are_not_mistaken_for_bombs(tmp_path: Path) -> None:
    path = _zip(tmp_path / "ok.docx", {"[Content_Types].xml": b"<Types/>", "w": bytes(200_000)})
    limits.preflight(path)


def test_a_compression_method_office_does_not_use_is_refused(tmp_path: Path) -> None:
    path = _zip(tmp_path / "bz.pptx", {"ppt/a.xml": b"<a/>" * 100}, zipfile.ZIP_BZIP2)
    with pytest.raises(limits.InputLimitError, match="compression method"):
        limits.preflight(path)


def test_too_many_parts_is_refused(tmp_path: Path) -> None:
    path = _zip(tmp_path / "many.docx", {f"p{n}.xml": b"<a/>" for n in range(10)})
    with pytest.raises(limits.InputLimitError, match="parts"):
        limits.preflight(path, limits.Limits(max_zip_members=5))
    limits.preflight(path, limits.Limits(max_zip_members=10))


def test_an_end_record_that_declares_too_many_entries_is_refused_unread(tmp_path: Path) -> None:
    path = _tiny_docx(tmp_path)
    _declare_entries(path, 0xFFFF)
    with pytest.raises(limits.InputLimitError, match="too many parts"):
        limits.preflight(path)


def test_a_file_that_is_not_a_zip_is_left_for_the_reader_to_report(tmp_path: Path) -> None:
    path = tmp_path / "notes.docx"
    path.write_bytes(b"this is not a package")
    limits.preflight(path)
    with pytest.raises(Exception) as caught:  # noqa: B017,PT011 - whatever python-docx says
        engine.scan(path)
    assert not isinstance(caught.value, limits.InputLimitError)


def test_the_demo_files_pass_the_checks(bad_docx: Path, bad_pptx: Path, bad_pdf: Path) -> None:
    for path in (bad_docx, bad_pptx, bad_pdf):
        limits.preflight(path)
        assert engine.scan(path).findings


# --- PDF pages and objects ---------------------------------------------------------------------


def test_a_pdf_with_more_pages_than_the_cap_is_refused_quickly(tmp_path: Path) -> None:
    path = _pdf(tmp_path / "long.pdf", pages=limits.Limits().max_pdf_pages + 1)
    started = time.perf_counter()
    with pytest.raises(limits.InputLimitError, match="501 pages"):
        engine.scan(path)
    with pytest.raises(limits.InputLimitError, match="pages"):
        content.extract(path)
    with pytest.raises(limits.InputLimitError, match="pages"):
        assets.extract(path, "page 1")
    assert time.perf_counter() - started < 5


def test_the_page_cap_can_be_raised(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _pdf(tmp_path / "five.pdf", pages=5)
    monkeypatch.setenv("WCAG_TOOL_MAX_PDF_PAGES", "3")
    with pytest.raises(limits.InputLimitError, match="WCAG_TOOL_MAX_PDF_PAGES"):
        engine.scan(path)
    monkeypatch.setenv("WCAG_TOOL_MAX_PDF_PAGES", "5")
    assert engine.scan(path).asset == "five.pdf"


def test_a_pdf_with_too_many_objects_is_refused(
    bad_pdf: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WCAG_TOOL_MAX_PDF_OBJECTS", "3")
    with pytest.raises(limits.InputLimitError, match="objects"):
        engine.scan(bad_pdf)


# --- what the model and a pile of files see ----------------------------------------------------


def test_a_pile_scan_skips_the_oversize_file_and_says_why(
    demo_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    long = _pdf(demo_dir / "textbook.pdf", pages=6)
    monkeypatch.setenv("WCAG_TOOL_MAX_PDF_PAGES", "5")
    batch = engine.scan_folder(demo_dir)
    assert batch.reports, "the other files are still scanned"
    skipped = {Path(s["path"]).name: s["reason"] for s in batch.skipped}
    assert "6 pages" in skipped[long.name]


def test_the_model_is_told_why_a_file_was_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _pdf(tmp_path / "five.pdf", pages=5)
    monkeypatch.setenv("WCAG_TOOL_MAX_PDF_PAGES", "3")

    async def run() -> None:
        async with Client(mcp) as client:
            for tool in ("scan_document", "extract_content", "fix_document"):
                result = await client.call_tool(tool, {"path": str(path)})
                assert result.is_error
                assert "5 pages; the limit is 3" in result.content[0].text
            shown = await client.call_tool("show_asset", {"path": str(path), "locator": "page 1"})
            assert "5 pages; the limit is 3" in shown.content[0].text
        assert not list(tmp_path.glob("*.remediated.*"))

    asyncio.run(run())
