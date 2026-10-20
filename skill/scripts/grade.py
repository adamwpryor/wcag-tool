"""Score saved replies against the conversation tests in ``tests/evals.json``.

Name each saved reply after its case, e.g. ``KAT-5.txt`` or ``KAT-5.run2.txt``.
The script runs the automatic checks for that case and prints the human checks
for you to tick. With several runs of one case it reports how many passed: the
number to watch, because a model never answers word for word the same way twice.

Needs nothing beyond Python.

Example:
    python scripts/grade.py replies/KAT-5.run1.txt replies/KAT-5.run2.txt
    python scripts/grade.py --list
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
EVALS = SKILL / "tests" / "evals.json"
_SCORE = re.compile(
    r"\d\s?%|\bper ?cent\b|\b\d{1,3}\s?(?:/|out of)\s?100\b|\bscore (?:of|is) \d", re.IGNORECASE
)
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _say(text: str) -> None:
    sys.stdout.write(text + "\n")


def _plain(text: str) -> str:
    """Strip Markdown emphasis and curly quotes so wording, not formatting, is compared."""
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"[*_>`#]", "", text).strip()


def check(rule: dict[str, Any], reply: str, evals: dict[str, Any]) -> bool:
    """Apply one automatic check to a reply.

    Args:
        rule: One entry from a case's ``auto`` list.
        reply: The assistant's reply.
        evals: The whole evals file, for the shared word lists.

    Returns:
        True when the reply passes.

    Raises:
        ValueError: For a check type this script does not know.
    """
    kind = rule["type"]
    plain = _plain(reply)
    if kind == "contains_all":
        return all(v in plain for v in rule["values"])
    if kind == "contains_any":
        return any(v in plain for v in rule["values"])
    if kind == "not_contains":
        # Whole words, so a name like "Pat" does not match "path".
        return not any(
            re.search(rf"\b{re.escape(v)}\b", plain, re.IGNORECASE) for v in rule["values"]
        )
    if kind == "first_sentence":
        first = _SENTENCE.split(plain, maxsplit=1)[0].strip().strip('"')
        return first == rule["equals"]
    if kind == "forbidden_words":
        scrubbed = plain
        for phrase in evals["exempt_phrases"]:
            scrubbed = scrubbed.replace(phrase, "")
        return not any(
            re.search(rf"\b{re.escape(w)}\b", scrubbed, re.IGNORECASE)
            for w in evals["banned_words"]
        )
    if kind == "no_score":
        return _SCORE.search(plain) is None
    if kind == "before":
        first = plain.find(rule["first"])
        later = [plain.find(t) for t in rule["then"] if t in plain]
        return first != -1 and all(first < pos for pos in later)
    raise ValueError(f"unknown check type {kind!r}")


def _case_id(path: Path, ids: set[str]) -> str | None:
    stem = path.name.split(".", 1)[0]
    return stem if stem in ids else None


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("replies", nargs="*", type=Path, help="saved replies, named by case id")
    parser.add_argument("--list", action="store_true", help="list the cases and their turns")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    evals = json.loads(EVALS.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in evals["cases"]}

    if args.list or not args.replies:
        for case in cases.values():
            attach = ", ".join(case["attach"]) or "nothing"
            _say(f"{case['id']}  {case['title']}  [{', '.join(case['applies_to'])}]")
            _say(f"    attach: {attach}")
            for turn in case["turns"]:
                _say(f"    > {turn}")
        return 0

    runs: dict[str, list[bool]] = defaultdict(list)
    for path in args.replies:
        case_id = _case_id(path, set(cases))
        if case_id is None:
            _say(f"skip  {path.name}: the file name does not start with a case id")
            continue
        case = cases[case_id]
        reply = path.read_text(encoding="utf-8")
        _say(f"\n{path.name}: {case['title']}")
        ok = True
        for rule in case["auto"]:
            passed = check(rule, reply, evals)
            ok &= passed
            _say(f"  {'pass' if passed else 'FAIL'}  {rule['type']}: {rule['why']}")
        for item in case["human"]:
            _say(f"  [ ]   {item}")
        runs[case_id].append(ok)

    _say("\nAutomatic checks, by case:")
    for case_id, results in runs.items():
        _say(f"  {case_id}: {sum(results)} of {len(results)} runs passed")
    return 0 if all(all(r) for r in runs.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
