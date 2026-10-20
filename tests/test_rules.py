import dataclasses
import json
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest

from wcag_tool import engine, rules
from wcag_tool.demo import make_test_set
from wcag_tool.findings import Closure, Confidence, Finding, Route


def _data(name: str) -> dict:
    return json.loads((files("wcag_tool") / "rules" / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["wcag21", "checks", "coverage"])
def test_rule_files_match_their_schemas(name: str) -> None:
    jsonschema.validate(_data(f"{name}.json"), _data(f"{name}.schema.json"))


def test_rules_load_and_agree() -> None:
    rule_set = rules.load()
    assert len(rule_set.criteria) == 50
    assert set(rule_set.coverage) == set(rule_set.criteria)
    assert all(c.criterion in rule_set.criteria for c in rule_set.checks.values())


def test_schema_enums_match_the_python_enums() -> None:
    assert set(rules.CLOSURES) == {c.value for c in Closure}
    assert set(rules.CONFIDENCES) == {c.value for c in Confidence}
    assert set(rules.ROUTES) == {Route.AUTO_FIX.value, Route.CONTENT_OWNER.value}
    item = _data("checks.schema.json")["properties"]["checks"]["items"]["properties"]
    assert set(item["closure"]["enum"]) == set(rules.CLOSURES)
    assert set(item["route"]["enum"]) == set(rules.ROUTES)


def test_route_one_is_title_and_language_only() -> None:
    route_one = {c.fix_id for c in rules.load().checks.values() if c.route == 1}
    assert route_one == {"set-title", "set-language"}


def test_validate_refuses_a_check_coverage_does_not_know() -> None:
    rule_set = rules.load()
    coverage = {cid: dict(cells) for cid, cells in rule_set.coverage.items()}
    coverage["2.4.2"]["docx"] = rules.Cell("not_checked", "author", "contradiction")
    broken = dataclasses.replace(rule_set, coverage=coverage)
    with pytest.raises(rules.RulesError, match="docx.missing-title"):
        broken.validate()


def test_validate_refuses_coverage_claiming_a_check_that_does_not_exist() -> None:
    rule_set = rules.load()
    coverage = {cid: dict(cells) for cid, cells in rule_set.coverage.items()}
    coverage["1.4.3"]["pdf"] = rules.Cell("checked_in_part", "author", "no such check")
    broken = dataclasses.replace(rule_set, coverage=coverage)
    with pytest.raises(rules.RulesError, match="no check exists"):
        broken.validate()


def test_fix_ids_must_match_their_template() -> None:
    rule_set = rules.load()
    assert rule_set.resolve_fix_id("docx.missing-title", None) == "set-title"
    assert rule_set.resolve_fix_id("docx.table-no-header", "mark-header-row:3") == (
        "mark-header-row:3"
    )
    with pytest.raises(rules.RulesError):
        rule_set.resolve_fix_id("docx.table-no-header", None)
    with pytest.raises(rules.RulesError):
        rule_set.resolve_fix_id("docx.table-no-header", "apply-heading:3:2")
    with pytest.raises(rules.RulesError):
        rule_set.resolve_fix_id("docx.link-text", "set-title")


def test_finding_takes_everything_but_evidence_from_the_rules() -> None:
    finding = Finding.from_check(
        "docx.table-no-header",
        asset="a.docx",
        locator="table 0",
        evidence="x",
        fix_id="mark-header-row:0",
    )
    assert finding.criterion == "1.3.1 Info and Relationships"
    assert finding.route == Route.CONTENT_OWNER
    assert finding.closure_required == Closure.CONTENT_OWNER_VERIFIED
    assert finding.proposal


def test_every_check_fires_on_the_test_set(tmp_path: Path) -> None:
    fired = {f.check for p in make_test_set(tmp_path) for f in engine.scan(p).findings}
    assert fired == set(rules.load().checks)


@pytest.mark.parametrize("fmt", rules.FORMATS)
def test_not_evaluated_names_every_criterion(fmt: str) -> None:
    # Nothing is silently passed: every A and AA criterion appears, checked or not.
    lines = rules.load().not_evaluated(fmt)
    assert len(lines) == 50
    for cid, line in zip(rules.load().criteria, lines, strict=True):
        assert line.startswith(f"{cid} ")


def test_report_coverage_partitions_the_criteria(bad_docx: Path) -> None:
    coverage = engine.scan(bad_docx).to_dict()["coverage"]
    ids = [cid for group in coverage.values() for cid in group]
    assert sorted(ids) == sorted(rules.load().criteria)
