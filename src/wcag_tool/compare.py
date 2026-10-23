"""Check a rebuilt document against its original before anyone relies on it.

When a PDF's source is gone, an agent can rebuild it from its content (``content.extract``)
into a new, properly structured file. The agent authors; it cannot be trusted alone to keep
every word. ``compare`` is the check: every word of the original in the rebuild, in order,
with nothing added; the same pictures, each tagged with alt text or set aside as decoration;
the same link targets; the same fill-in fields, now named; and a scan of the rebuild.

Differences are reported verbatim, never summarised, so a dropped or reworded sentence is
visible. Passing the check makes the rebuild a structured copy whose content was checked
against the original. It is not a conformance claim, and the screen-reader task still applies.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject

from wcag_tool import content, engine

CLAIM = (
    "The rebuild is a structured copy whose words, pictures, links and fields were checked "
    "against the original by the tool; the author confirmed every alt text, heading and header "
    "row. This is not a conformance claim: criteria the scan does not evaluate still need a "
    "person, and the file still needs one person with a screen reader and a named task."
)

_WORD = re.compile(r"\w+(?:['’]\w+)*")
_MAX_RUNS = 40


def _n(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _words(text: str) -> list[str]:
    return _WORD.findall(text.replace("’", "'"))


def _block_text(block: dict[str, Any]) -> list[str]:
    parts = [block.get("text", ""), block.get("text_boxes", "")]
    parts += [cell for row in block.get("rows", []) for cell in row]
    return [p for p in parts if p]


def _profile(path: Path) -> dict[str, Any]:
    """What compare needs from one file: words, pictures, link targets, fields."""
    data = content.extract(path)
    words: list[str] = []
    pictures = 0
    missing_alt: list[str] = []
    links: list[str] = []
    fields: list[dict[str, Any]] = []
    for unit in data["units"]:
        for block in unit["blocks"]:
            for text in _block_text(block):
                words += _words(text)
            kind = block["kind"]
            if kind == "picture":
                pictures += 1
                if not block["alt"] and not block["decorative"]:
                    missing_alt.append(block["where"])
            elif kind == "pictures":
                pictures += block["count"]
            elif kind == "field":
                fields.append(block)
            elif kind == "link":
                links.append(block["target"])
            links += [link["target"] for link in block.get("links", [])]
    return {
        "data": data,
        "words": words,
        "pictures": pictures,
        "missing_alt": missing_alt,
        "links": [t for t in links if not t.startswith("#")],
        "fields": fields,
    }


def _figures(node: Any, out: list[bool], depth: int = 0) -> None:
    """Collect, for each Figure in a PDF's tag tree, whether it carries alt text."""
    if depth > 200:
        return
    node = node.get_object() if hasattr(node, "get_object") else node
    if isinstance(node, ArrayObject):
        for child in node:
            _figures(child, out, depth + 1)
        return
    if not isinstance(node, DictionaryObject):
        return
    if node.get("/S") == "/Figure":
        out.append(bool(str(node.get("/Alt") or "").strip()))
    if "/K" in node:
        _figures(node["/K"], out, depth + 1)


def _pdf_figures(path: Path) -> list[bool]:
    tree = PdfReader(str(path)).root_object.get("/StructTreeRoot")
    out: list[bool] = []
    if tree is not None:
        _figures(tree.get_object().get("/K"), out)
    return out


def _runs(tokens: list[str], spans: list[tuple[int, int]]) -> list[str]:
    return [" ".join(tokens[start:end]) for start, end in spans[:_MAX_RUNS]]


def _remove(tokens: list[str], phrases: list[list[str]]) -> list[str]:
    """Drop every occurrence of each phrase (compared case-insensitively) from a word list."""
    keys = [t.casefold() for t in tokens]
    keep = [True] * len(tokens)
    for phrase in phrases:
        target = [w.casefold() for w in phrase]
        n = len(target)
        if not n:
            continue
        for i in range(len(keys) - n + 1):
            if keys[i : i + n] == target:
                for j in range(i, i + n):
                    keep[j] = False
    return [t for t, k in zip(tokens, keep, strict=True) if k]


def compare(original: Path, rebuilt: Path, ignore: list[str] | None = None) -> dict[str, Any]:
    """Check a rebuilt file against its original.

    Args:
        original: The file the rebuild was made from. Read, never written.
        rebuilt: The rebuild. Read, never written.
        ignore: Phrases to leave out of the word check on both sides, such as a running
            footer the rebuild deliberately does not repeat on every page.

    Returns:
        ``words`` (counts, and the runs missing from or added to the rebuild, verbatim),
        ``pictures``, ``links``, ``fields``, ``rebuilt_findings`` (a scan of the rebuild),
        ``problems`` (one line each; empty when nothing was found), and ``claim``.

    Raises:
        ValueError: If both paths are the same file.
    """
    if original.resolve() == rebuilt.resolve():
        raise ValueError("compare needs the original and a separate rebuilt file")
    before, after = _profile(original), _profile(rebuilt)
    phrases = [_words(p) for p in ignore or []]
    a = _remove(before["words"], phrases)
    b = _remove(after["words"], phrases)
    matcher = difflib.SequenceMatcher(
        None, [w.casefold() for w in a], [w.casefold() for w in b], autojunk=False
    )
    missing: list[tuple[int, int]] = []
    added: list[tuple[int, int]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("delete", "replace"):
            missing.append((i1, i2))
        if tag in ("insert", "replace"):
            added.append((j1, j2))

    problems: list[str] = []
    if not a and before["pictures"]:
        problems.append(
            "The original has no text to compare against (a scan): a person must read the "
            "rebuild against the original page by page."
        )
    if missing:
        problems.append(
            _n(sum(e - s for s, e in missing), "word") + " of the original missing from the "
            "rebuild or changed; see words.missing."
        )
    if added:
        problems.append(
            _n(sum(e - s for s, e in added), "word") + " in the rebuild not in the original; "
            "see words.added."
        )

    if after["pictures"] != before["pictures"]:
        problems.append(
            f"The original draws {_n(before['pictures'], 'picture')} and the rebuild "
            f"{after['pictures']}; drawings made of shapes are not counted on either side."
        )
    figures: list[bool] = []
    if rebuilt.suffix.lower() == ".pdf":
        figures = _pdf_figures(rebuilt)
        without = figures.count(False)
        if without:
            problems.append(f"{_n(without, 'figure')} in the rebuild with no alt text.")
    elif after["missing_alt"]:
        problems.append(
            "Pictures in the rebuild with no alt text and not marked decorative: "
            + ", ".join(after["missing_alt"])
        )

    lost = sorted(set(before["links"]) - set(after["links"]))
    if lost:
        problems.append("Link targets of the original missing from the rebuild: " + ", ".join(lost))
    if len(after["fields"]) != len(before["fields"]):
        problems.append(
            f"The original has {_n(len(before['fields']), 'fill-in field')} and the rebuild "
            f"{len(after['fields'])}."
        )
    unnamed = [f["where"] for f in after["fields"] if not f.get("tooltip")]
    if unnamed:
        problems.append(
            _n(len(unnamed), "fill-in field")
            + " in the rebuild with no name: "
            + ", ".join(sorted(set(unnamed)))
        )

    findings = [
        {"check": f.check, "locator": f.locator, "evidence": f.evidence}
        for f in engine.scan(rebuilt).findings
    ]
    if findings:
        problems.append(
            f"The scan of the rebuild still finds {_n(len(findings), 'thing')}; see "
            "rebuilt_findings."
        )

    return {
        "original": str(original),
        "rebuilt": str(rebuilt),
        "words": {
            "original": len(a),
            "rebuilt": len(b),
            "missing": _runs(a, missing),
            "added": _runs(b, added),
            "ignored": ignore or [],
        },
        "pictures": {
            "original": before["pictures"],
            "rebuilt": after["pictures"],
            "figures_tagged": len(figures),
            "figures_without_alt": figures.count(False),
        },
        "links": {"original": sorted(set(before["links"])), "rebuilt": sorted(set(after["links"]))},
        "fields": {
            "original": len(before["fields"]),
            "rebuilt": len(after["fields"]),
            "rebuilt_unnamed": len(unnamed),
        },
        "rebuilt_findings": findings,
        "problems": problems,
        "claim": CLAIM,
    }
