import json
from pathlib import Path

import pytest

from wcag_tool import cli


def test_demo_then_scan_markdown(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["demo", str(tmp_path / "pile")]) == 0
    written = capsys.readouterr().out.strip().splitlines()
    assert len(written) == 5
    assert cli.main(["scan", str(tmp_path / "pile")]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Triage: 5 files")


def test_scan_single_file_json(bad_pdf: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["scan", "--json", str(bad_pdf)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["files"] == 1
    assert {f["check"] for f in data["reports"][0]["findings"]} >= {"pdf.untagged"}


def test_fix_writes_record(bad_docx: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["fix", str(bad_docx), "--apply", "mark-header-row:0"]) == 0
    record = json.loads(capsys.readouterr().out)
    assert "mark-header-row:0" in record["applied"]
    assert Path(record["output"]).exists()


def test_unsupported_file_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "x.txt"
    path.write_text("x", encoding="utf-8")
    assert cli.main(["fix", str(path)]) == 2
    assert "not supported" in capsys.readouterr().err
