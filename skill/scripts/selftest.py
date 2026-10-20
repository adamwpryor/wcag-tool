"""Check that the scanner gives the expected answer on files whose defects are known.

Scans every file in ``tests/fixtures/`` (fictional; built from the package's
``demo`` module) and compares each result with ``tests/expected/<file>.json``,
then compares the pile's Route 5 aggregation with ``tests/expected/_pile.json``.
Any difference is printed and the exit status is 1.

If ``tests/fixtures/`` is not there (a checkout of the repository, where course
file formats are never committed), the fixtures are built into a temporary
folder first.

Example:
    python scripts/selftest.py
    python scripts/selftest.py --update     # after a deliberate change to a check
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from _setup import SKILL, ready

ready()

from wcag_tool import engine  # noqa: E402  (ready() puts the checks on the path)
from wcag_tool.demo import make_test_set  # noqa: E402

EXPECTED = SKILL / "tests" / "expected"
FIXTURES = SKILL / "tests" / "fixtures"
_FINDING_KEYS = (
    "check",
    "criterion",
    "locator",
    "evidence",
    "route",
    "closure_required",
    "confidence",
    "fix_id",
    "proposal",
)


def _say(text: str) -> None:
    sys.stdout.write(text + "\n")


def file_result(path: Path) -> dict[str, Any]:
    """The parts of one file's report that must not change without a decision."""
    data = engine.scan(path).to_dict()
    return {
        "asset": data["asset"],
        "format": data["format"],
        "counts_by_route": {str(k): v for k, v in data["counts_by_route"].items()},
        "findings": [{k: f[k] for k in _FINDING_KEYS} for f in data["findings"]],
        "coverage": data["coverage"],
    }


def pile_result(paths: list[Path]) -> dict[str, Any]:
    """The parts of the pile's result that must not change without a decision."""
    data = engine.scan_many(paths).to_dict()
    return {
        "files": data["files"],
        "formats": data["formats"],
        "counts_by_route": {str(k): v for k, v in data["counts_by_route"].items()},
        "systemic": data["systemic"],
    }


def _differences(expected: Any, actual: Any, where: str = "") -> list[str]:
    if isinstance(expected, dict) and isinstance(actual, dict):
        out = []
        for key in sorted(set(expected) | set(actual), key=str):
            if key not in actual:
                out.append(f"{where}.{key}: missing")
            elif key not in expected:
                out.append(f"{where}.{key}: unexpected")
            else:
                out += _differences(expected[key], actual[key], f"{where}.{key}")
        return out
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return [f"{where}: expected {len(expected)} items, got {len(actual)}"]
        return [
            d
            for i, (e, a) in enumerate(zip(expected, actual, strict=True))
            for d in _differences(e, a, f"{where}[{i}]")
        ]
    return [] if expected == actual else [f"{where}: expected {expected!r}, got {actual!r}"]


def run(fixtures: Path, update: bool) -> int:
    """Compare (or, with ``update``, rewrite) every expected result.

    Args:
        fixtures: Folder holding the fixture files.
        update: Write the current results as the new expected results.

    Returns:
        Exit status: 0 when everything matches.
    """
    paths = sorted(p for p in fixtures.iterdir() if p.suffix in (".docx", ".pptx", ".pdf"))
    results = {p.name: file_result(p) for p in paths}
    results["_pile"] = pile_result(paths)
    failures = 0
    for name, actual in results.items():
        target = EXPECTED / f"{name}.json"
        if update:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(actual, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            _say(f"updated  {target.name}")
            continue
        if not target.is_file():
            _say(f"FAIL  {name}: no expected result at tests/expected/{target.name}")
            failures += 1
            continue
        diffs = _differences(json.loads(target.read_text(encoding="utf-8")), actual)
        _say(f"{'FAIL' if diffs else 'pass'}  {name}")
        for diff in diffs[:10]:
            _say(f"        {diff}")
        failures += bool(diffs)
    if not update:
        _say(f"\n{len(results) - failures} of {len(results)} match the expected results.")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--fixtures", type=Path, default=None, help="folder of fixture files")
    parser.add_argument("--update", action="store_true", help="rewrite the expected results")
    args = parser.parse_args(argv)
    if args.fixtures is not None:
        return run(args.fixtures, args.update)
    if FIXTURES.is_dir():
        return run(FIXTURES, args.update)
    with tempfile.TemporaryDirectory() as tmp:
        make_test_set(Path(tmp))
        return run(Path(tmp), args.update)


if __name__ == "__main__":
    sys.exit(main())
