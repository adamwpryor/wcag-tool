"""fix writes only where it may: one folder, a fixed naming rule, and never over a file."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from mcp import Client

from wcag_tool import cli, engine, outputs
from wcag_tool.server import mcp

SENTINEL = b"do not touch"


def _symlink(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=target.is_dir())
    except (OSError, NotImplementedError):
        pytest.skip("this account cannot create symbolic links")


def _tree(folder: Path) -> set[str]:
    return {str(p.relative_to(folder)) for p in folder.rglob("*")}


def _mcp_fix(args: dict) -> object:
    async def run() -> object:
        async with Client(mcp) as client:
            return await client.call_tool("fix_document", args)

    return asyncio.run(run())


# --- the default, and a configured folder ----------------------------------------------------


def test_the_copy_still_lands_beside_the_original(bad_docx: Path) -> None:
    record = engine.fix(bad_docx, language="en-US")
    copy = Path(record["output"])
    assert copy.parent == bad_docx.parent.resolve()
    assert copy.name == "bad_syllabus.remediated.docx"
    assert copy.with_suffix(".remediation.json").is_file()


def test_out_dir_is_where_the_copy_and_record_go(bad_docx: Path, tmp_path: Path) -> None:
    folder = tmp_path / "fixed copies"
    record = engine.fix(bad_docx, out_dir=folder)
    copy = Path(record["output"])
    assert copy.parent == folder.resolve()
    assert copy.is_file() and copy.with_suffix(".remediation.json").is_file()
    assert not (bad_docx.parent / copy.name).exists()


def test_the_environment_names_the_folder_too(
    bad_docx: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(outputs.ENV_OUT_DIR, str(tmp_path / "from env"))
    copy = Path(engine.fix(bad_docx)["output"])
    assert copy.parent == (tmp_path / "from env").resolve()


def test_the_command_line_takes_out_dir_and_refuses_with_a_message(
    bad_docx: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "cli out"
    assert cli.main(["fix", str(bad_docx), "--out-dir", str(folder)]) == 0
    assert (folder / "bad_syllabus.remediated.docx").is_file()
    capsys.readouterr()
    assert cli.main(["fix", str(bad_docx), "--out-dir", str(folder)]) == 2
    assert "already exists" in capsys.readouterr().err
    assert cli.main(["fix", str(bad_docx), "--out-dir", str(folder), "--overwrite"]) == 0


# --- traversal, naming and the original ------------------------------------------------------


@pytest.mark.parametrize(
    "where",
    [
        "../evil.remediated.docx",
        "sub/inside.remediated.docx",
        "..\\evil.remediated.docx",
    ],
)
def test_a_relative_path_that_leaves_the_folder_is_refused(bad_docx: Path, where: str) -> None:
    folder = bad_docx.parent
    (folder / "sub").mkdir()
    before = _tree(folder.parent)
    with pytest.raises(outputs.OutputPathError, match="inside"):
        engine.fix(bad_docx, output=Path(where))
    assert _tree(folder.parent) == before


def test_an_absolute_path_elsewhere_is_refused(bad_docx: Path, tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    target = elsewhere / "x.remediated.docx"
    with pytest.raises(outputs.OutputPathError, match="inside"):
        engine.fix(bad_docx, output=target)
    assert list(elsewhere.iterdir()) == []


def test_a_folder_that_does_not_exist_is_not_created_by_an_output_path(bad_docx: Path) -> None:
    with pytest.raises(outputs.OutputPathError):
        engine.fix(bad_docx, output=bad_docx.parent / "new" / "x.remediated.docx")
    assert not (bad_docx.parent / "new").exists()


@pytest.mark.parametrize(
    "name",
    [
        "notes.docx",
        ".bashrc",
        "x.remediated.txt",
        "x.remediated",
        # near misses: the mark has to be the whole of the last-but-one part of the name
        "a.remediatedX.docx",
        "a.remediated-old.docx",
        "remediated.docx",
        "x.remediated.docx.bak",
    ],
)
def test_a_name_that_is_not_a_remediated_copy_is_refused(bad_docx: Path, name: str) -> None:
    target = bad_docx.parent / name
    target.write_bytes(SENTINEL)
    with pytest.raises(outputs.OutputPathError, match="remediated"):
        engine.fix(bad_docx, output=target, overwrite=True)
    assert target.read_bytes() == SENTINEL


def test_the_original_is_never_the_output_even_with_overwrite(bad_docx: Path) -> None:
    original_bytes = bad_docx.read_bytes()
    with pytest.raises(ValueError, match="never overwritten"):
        engine.fix(bad_docx, output=bad_docx, overwrite=True)
    with pytest.raises(ValueError, match="never overwritten"):
        engine.fix(bad_docx, output=Path(bad_docx.name), overwrite=True)
    assert bad_docx.read_bytes() == original_bytes


def test_a_named_copy_inside_the_folder_is_allowed(bad_docx: Path) -> None:
    record = engine.fix(bad_docx, output=Path("my.remediated.docx"))
    assert Path(record["output"]) == (bad_docx.parent / "my.remediated.docx").resolve()


def test_the_name_rule_ignores_the_case_of_the_extension(tmp_path: Path) -> None:
    from wcag_tool.demo import make_bad_docx

    original = make_bad_docx(tmp_path / "Upper.DOCX")
    copy = Path(engine.fix(original, output=Path("Upper.remediated.DOCX"))["output"])
    assert copy.name == "Upper.remediated.DOCX"


# --- overwrite -------------------------------------------------------------------------------


def test_an_existing_copy_is_refused_and_left_alone(bad_docx: Path) -> None:
    first = Path(engine.fix(bad_docx)["output"])
    kept = first.read_bytes()
    with pytest.raises(outputs.OutputPathError, match="already exists"):
        engine.fix(bad_docx)
    assert first.read_bytes() == kept


def test_overwrite_replaces_the_earlier_copy_and_record(bad_docx: Path) -> None:
    first = engine.fix(bad_docx)
    assert "set-language" not in first["applied"]
    second = engine.fix(bad_docx, language="en-US", overwrite=True)
    assert "set-language" in second["applied"]
    record = json.loads(Path(second["output"]).with_suffix(".remediation.json").read_text("utf-8"))
    assert "set-language" in record["applied"]


def test_an_unrelated_file_with_the_same_name_is_not_replaced_without_overwrite(
    bad_docx: Path,
) -> None:
    target = bad_docx.parent / "bad_syllabus.remediated.docx"
    target.write_bytes(SENTINEL)
    with pytest.raises(outputs.OutputPathError):
        engine.fix(bad_docx)
    assert target.read_bytes() == SENTINEL
    assert not target.with_suffix(".remediation.json").exists()


def test_a_taken_record_name_stops_the_run_before_anything_is_written(bad_docx: Path) -> None:
    record = bad_docx.parent / "bad_syllabus.remediated.remediation.json"
    record.write_bytes(SENTINEL)
    with pytest.raises(outputs.OutputPathError, match="remediation.json"):
        engine.fix(bad_docx)
    assert record.read_bytes() == SENTINEL
    assert not (bad_docx.parent / "bad_syllabus.remediated.docx").exists()


def test_a_clean_run_leaves_only_the_copy_and_its_record(bad_docx: Path) -> None:
    before = {p.name for p in bad_docx.parent.iterdir()}
    engine.fix(bad_docx)
    engine.fix(bad_docx, overwrite=True)
    added = {p.name for p in bad_docx.parent.iterdir()} - before
    assert added == {"bad_syllabus.remediated.docx", "bad_syllabus.remediated.remediation.json"}


def test_overwrite_does_not_replace_a_directory(bad_docx: Path) -> None:
    (bad_docx.parent / "bad_syllabus.remediated.docx").mkdir()
    with pytest.raises(outputs.OutputPathError, match="regular file"):
        engine.fix(bad_docx, overwrite=True)


def test_a_failed_fix_leaves_no_half_written_copy(
    bad_docx: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scanner, _ = engine._HANDLERS[".docx"]

    def broken(*_args: object) -> dict:
        raise RuntimeError("the fixer failed")

    monkeypatch.setitem(engine._HANDLERS, ".docx", (scanner, broken))
    before = _tree(bad_docx.parent)
    with pytest.raises(RuntimeError):
        engine.fix(bad_docx)
    assert _tree(bad_docx.parent) == before


def _failing_fixer(monkeypatch: pytest.MonkeyPatch, *, writes: bytes | None) -> None:
    """Swap the .docx fixer for one that fails: raising at once, or after writing ``writes``."""
    scanner, _ = engine._HANDLERS[".docx"]

    def broken(_path: Path, _ids: list[str], output: Path, *_rest: object) -> dict:
        if writes is not None:
            output.write_bytes(writes)
            return {"applied": {}, "failed": {}}
        raise RuntimeError("the fixer failed")

    monkeypatch.setitem(engine._HANDLERS, ".docx", (scanner, broken))


@pytest.mark.parametrize("writes", [None, b"not a document"], ids=["fixer-raises", "bad-output"])
def test_a_failed_overwrite_leaves_the_earlier_copy_and_record_as_they_were(
    bad_docx: Path, monkeypatch: pytest.MonkeyPatch, writes: bytes | None
) -> None:
    first = engine.fix(bad_docx, language="en-US")
    copy = Path(first["output"])
    record = copy.with_suffix(".remediation.json")
    kept = (copy.read_bytes(), record.read_bytes())
    before = _tree(bad_docx.parent)

    _failing_fixer(monkeypatch, writes=writes)
    with pytest.raises(Exception):  # noqa: B017,PT011 - the fixer's own error, or the parser's
        engine.fix(bad_docx, overwrite=True)

    assert (copy.read_bytes(), record.read_bytes()) == kept
    assert _tree(bad_docx.parent) == before  # and no temporary folder is left behind


# --- links -----------------------------------------------------------------------------------


def test_a_link_is_refused_even_when_overwrite_is_set(
    bad_docx: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Runs everywhere: the check is "is this a link", answered here by the filesystem or,
    # where the account cannot make links, by a stand-in for exactly that one question.
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.docx"
    victim.write_bytes(SENTINEL)
    link = bad_docx.parent / "go.remediated.docx"
    try:
        os.symlink(victim, link)
    except (OSError, NotImplementedError):
        link.write_bytes(SENTINEL)
        real = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda self: self.name == link.name or real(self))
    with pytest.raises(outputs.OutputPathError, match="link"):
        engine.fix(bad_docx, output=link, overwrite=True)
    assert victim.read_bytes() == SENTINEL


def test_a_dangling_link_is_refused_too(bad_docx: Path, tmp_path: Path) -> None:
    link = bad_docx.parent / "dangling.remediated.docx"
    _symlink(link, tmp_path / "nowhere" / "new.docx")
    with pytest.raises(outputs.OutputPathError, match="link"):
        engine.fix(bad_docx, output=link)
    assert not (tmp_path / "nowhere").exists()


def test_a_symlinked_subfolder_cannot_carry_the_copy_out(bad_docx: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    _symlink(bad_docx.parent / "door", outside)
    with pytest.raises(outputs.OutputPathError, match="inside"):
        engine.fix(bad_docx, output=Path("door") / "x.remediated.docx")
    assert list(outside.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="a junction is the Windows way to point out")
def test_a_junction_cannot_carry_the_copy_out_either(bad_docx: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    door = bad_docx.parent / "door"
    made = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(door), str(outside)], capture_output=True, check=False
    )
    if made.returncode != 0:
        pytest.skip("could not make a junction")
    with pytest.raises(outputs.OutputPathError, match="inside"):
        engine.fix(bad_docx, output=Path("door") / "x.remediated.docx")
    assert list(outside.iterdir()) == []


# --- the MCP tool ----------------------------------------------------------------------------


def test_the_tool_refuses_a_path_the_model_picked_outside_the_folder(
    bad_docx: Path, tmp_path: Path
) -> None:
    elsewhere = tmp_path / "home"
    elsewhere.mkdir()
    victim = elsewhere / ".bashrc"
    victim.write_bytes(SENTINEL)
    result = _mcp_fix({"path": str(bad_docx), "output_path": str(victim), "overwrite": True})
    assert result.is_error  # type: ignore[attr-defined]
    assert victim.read_bytes() == SENTINEL
    assert not list(bad_docx.parent.glob("*.remediated.*"))


def test_the_tool_needs_overwrite_to_run_twice(bad_docx: Path) -> None:
    first = _mcp_fix({"path": str(bad_docx)})
    assert not first.is_error  # type: ignore[attr-defined]
    again = _mcp_fix({"path": str(bad_docx)})
    assert again.is_error  # type: ignore[attr-defined]
    assert "already exists" in again.content[0].text  # type: ignore[attr-defined]
    replaced = _mcp_fix({"path": str(bad_docx), "language": "en-US", "overwrite": True})
    assert not replaced.is_error  # type: ignore[attr-defined]
