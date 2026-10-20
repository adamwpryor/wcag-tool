"""Extract the WCAG 2.1 Level A and AA success criteria into ``src/wcag_tool/rules/wcag21.json``.

The criteria text is W3C's, quoted, not ours. This script reads the published
Recommendation and writes one record per success criterion: number, name,
level, the normative text, and the Understanding document's URL. Re-running it
against the same page produces the same file, so the data can be checked
against its source at any time.

Copyright © W3C (MIT, ERCIM, Keio, Beihang). Quoted under the W3C Document
License: https://www.w3.org/copyright/document-license-2023/

Example:
    curl -sSL -o wcag21.html https://www.w3.org/TR/WCAG21/
    python tools/extract_wcag.py wcag21.html
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from lxml import html
from lxml.html import HtmlElement

logger = logging.getLogger(__name__)

SOURCE_URL = "https://www.w3.org/TR/WCAG21/"
LICENSE_URL = "https://www.w3.org/copyright/document-license-2023/"
LEVELS = ("A", "AA")
_SC_HEADING = re.compile(r"Success Criterion (\d+\.\d+\.\d+)")
_LEVEL = re.compile(r"\(Level (A+)\)")
_DATE = re.compile(r"W3C Recommendation (\d{2} \w+ \d{4})")
_SKIP_CLASSES = {"header-wrapper", "doclinks", "conformance-level", "note"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normative_text(section: HtmlElement) -> str:
    """The criterion's own words: paragraphs and lists, without notes or links."""
    parts: list[str] = []
    for child in section:
        classes = set((child.get("class") or "").split())
        if classes & _SKIP_CLASSES or child.tag in ("section", "h4"):
            continue
        if child.tag == "dl":
            for term in child.findall("dt"):
                definition = term.getnext()
                dd = _clean(definition.text_content()) if definition is not None else ""
                parts.append(f"- {_clean(term.text_content())}: {dd}")
        elif child.tag in ("ul", "ol"):
            parts.extend(f"- {_clean(li.text_content())}" for li in child.findall("li"))
        elif child.tag == "p":
            text = _clean(child.text_content())
            if text:
                parts.append(text)
    return "\n".join(parts)


def extract(page: str) -> dict[str, Any]:
    """Parse the Recommendation and return the A and AA criteria.

    Args:
        page: The HTML of https://www.w3.org/TR/WCAG21/.

    Returns:
        The document written to ``wcag21.json``.

    Raises:
        ValueError: If the page does not hold 30 Level A and 20 Level AA criteria.
    """
    tree = html.fromstring(page)
    date = _DATE.search(tree.text_content())
    criteria: list[dict[str, str]] = []
    for heading in tree.iter("h4"):
        match = _SC_HEADING.search(heading.text_content())
        if not match:
            continue
        section = heading.getparent().getparent()
        level_el = section.find("p[@class='conformance-level']")
        level_match = _LEVEL.search(level_el.text_content()) if level_el is not None else None
        if level_match is None or level_match.group(1) not in LEVELS:
            continue
        name = _clean(heading.text_content()[match.end() :])
        understanding = section.find("div[@class='doclinks']/a")
        criteria.append(
            {
                "id": match.group(1),
                "name": name,
                "level": level_match.group(1),
                "text": _normative_text(section),
                "understanding": understanding.get("href") if understanding is not None else "",
            }
        )
    counts = {lvl: sum(1 for c in criteria if c["level"] == lvl) for lvl in LEVELS}
    if counts != {"A": 30, "AA": 20}:
        raise ValueError(f"expected 30 A and 20 AA criteria, found {counts}")
    return {
        "source": SOURCE_URL,
        "source_date": date.group(1) if date else "",
        "copyright": (
            "Copyright © W3C® (MIT, ERCIM, Keio, Beihang). Criterion text quoted from the "
            "WCAG 2.1 Recommendation under the W3C Document License."
        ),
        "license": LICENSE_URL,
        "criteria": criteria,
    }


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("html_file", type=Path, help="a saved copy of the WCAG 2.1 page")
    parser.add_argument(
        "--out", type=Path, default=_repo_root() / "src" / "wcag_tool" / "rules" / "wcag21.json"
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    data = extract(args.html_file.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    logger.info("wrote %d criteria to %s", len(data["criteria"]), args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
