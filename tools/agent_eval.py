"""Run the MCP tier's conversation cases through a real agent, then judge what it did to the files.

The chat tiers are judged by reading replies. An agent's work is files, so it can be judged
exactly. For each case in ``skill/tests/evals.json`` that carries an ``agent`` block, this
script:

1. writes the case's fictional files into a fresh folder and fingerprints them;
2. runs Claude Code headless in that folder, with only the wcag-tool MCP server loaded and
   Bash, Edit and Write denied, typing the case's turns one at a time;
3. judges the folder: every original byte-identical, nothing new but remediated copies and
   their records, no fix applied that the scripted person did not agree to, no language
   invented, every agreed fix present, and each record matching a fresh scan of its copy.

The agent's last reply is saved as ``<case>.run<n>.txt`` in ``--out`` so ``grade.py --for mcp``
can grade the words too. It runs on the Claude subscription login: API keys are removed from
the agent's environment, and the run refuses to start unless ``claude auth status`` shows a
subscription with no API key source (``--use-api-key`` opts into a billed run). It still uses
plan time, so nothing runs it automatically; ``tests/test_agent_eval.py`` tests the judge alone.

Example:
    python tools/agent_eval.py --claude path/to/claude.exe
    python tools/agent_eval.py --claude claude KAT-17 --runs 3 --skill
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wcag_tool import engine
from wcag_tool.demo import make_test_set

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "skill" / "tests" / "evals.json"
SKILL = ROOT / "skill" / "SKILL.md"

# What the agent may use. Reading is allowed so it can look around the folder; changing a
# file any way but fix_document is denied, which is the rule the instructions state.
ALLOWED_TOOLS = [
    "mcp__wcag-tool__scan_document",
    "mcp__wcag-tool__scan_folder",
    "mcp__wcag-tool__fix_document",
    "mcp__wcag-tool__show_asset",
    "mcp__wcag-tool__extract_content",
    "mcp__wcag-tool__compare_rebuild",
    "mcp__wcag-tool__describe_routes",
    "mcp__wcag-tool__explain_criterion",
    "Read",
    "Glob",
    "Grep",
]
DENIED_TOOLS = ["Bash", "Edit", "Write", "NotebookEdit", "WebFetch", "WebSearch", "Agent"]

# API keys stay out of the agent's environment unless --use-api-key is given, so the runs use
# the Claude subscription login: headless Claude Code bills ANTHROPIC_API_KEY silently whenever
# it is set.
_API_KEY_VARS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "GEMINI_API_KEY", "GOOGLE_API_KEY")

# The only files an agent may add: a remediated copy and its record.
_NEW_FILE = re.compile(r".+\.remediated\.(docx|pptx|pdf|remediation\.json)$")
_TURN_TIMEOUT = 900


@dataclass
class Expectation:
    """What a case allows the agent to do, from its ``agent`` block.

    Attributes:
        allowed: Fix id kinds (the part before any ``:``) the scripted person agreed to.
        required: Fix id kinds that must be in the final copy.
        language: The language the person named, or None if they named none.
    """

    allowed: set[str]
    required: set[str] = field(default_factory=set)
    language: str | None = None

    @classmethod
    def from_case(cls, case: dict[str, Any]) -> Expectation:
        """Build from an evals.json case with an ``agent`` block."""
        agent = case["agent"]
        return cls(
            allowed=set(agent["allowed_fix_ids"]),
            required=set(agent.get("required_fix_ids", [])),
            language=agent.get("language"),
        )


def snapshot(folder: Path) -> dict[str, str]:
    """SHA-256 of every file directly in a folder, by name."""
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.iterdir())
        if p.is_file()
    }


def _kind(fix_id: str) -> str:
    return fix_id.split(":", 1)[0]


def judge(folder: Path, before: dict[str, str], expect: Expectation) -> list[str]:
    """Everything the agent did to the folder that breaks a rule.

    Args:
        folder: The case's folder after the agent ran.
        before: ``snapshot(folder)`` taken before it ran.
        expect: What the case allows.

    Returns:
        One line per problem; empty when the agent kept every rule.
    """
    problems: list[str] = []
    now = snapshot(folder)
    for name, digest in before.items():
        if name not in now:
            problems.append(f"original removed: {name}")
        elif now[name] != digest:
            problems.append(f"original changed: {name}")
    for name in sorted(set(now) - set(before)):
        if not _NEW_FILE.match(name):
            problems.append(f"unexpected file written: {name}")

    applied_kinds: set[str] = set()
    for record_path in sorted(folder.glob("*.remediation.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        label = record_path.name
        for fix_id in record["applied"]:
            applied_kinds.add(_kind(fix_id))
            if _kind(fix_id) not in expect.allowed:
                problems.append(f"{label}: applied {fix_id} without a yes")
        if record["unknown_fix_ids"]:
            problems.append(
                f"{label}: asked for fix ids the scan never offered: "
                f"{record['unknown_fix_ids']}"
            )
        if record["language"] is not None and record["language"] != expect.language:
            named = expect.language or "none"
            problems.append(
                f"{label}: language {record['language']!r}, but the person named " f"{named}"
            )
        output = Path(record["output"])
        if not output.exists():
            problems.append(f"{label}: its copy {output.name} is missing")
            continue
        rescanned = {(f.check, f.locator) for f in engine.scan(output).findings}
        recorded = {(f["check"], f["locator"]) for f in record["after"]["findings"]}
        if rescanned != recorded:
            problems.append(f"{label}: does not match a fresh scan of {output.name}")
    for kind in sorted(expect.required - applied_kinds):
        problems.append(f"never applied {kind}, which the person asked for")
    return problems


def agent_env(use_api_key: bool = False) -> dict[str, str]:
    """The environment the agent runs in: this one, without model API keys unless asked."""
    env = dict(os.environ)
    if not use_api_key:
        for name in _API_KEY_VARS:
            env.pop(name, None)
    return env


def login_problem(status: dict[str, Any], use_api_key: bool = False) -> str | None:
    """Why ``claude auth status`` output is not the login this run should use, or None.

    Args:
        status: The parsed JSON from ``claude auth status``.
        use_api_key: True when the person asked for an API-key run.

    Returns:
        A sentence saying what is wrong, or None when the login is right.
    """
    if not status.get("loggedIn"):
        return "Claude Code is not signed in; run `claude auth login` with the subscription."
    if use_api_key:
        return None
    if status.get("apiKeySource"):
        return (
            f"Claude Code would use an API key from {status['apiKeySource']}, not the subscription."
        )
    if status.get("authMethod") != "claude.ai":
        method = status.get("authMethod")
        return f"Claude Code is signed in with {method!r}, not a Claude subscription."
    return None


def _check_login(claude: str, env: dict[str, str], use_api_key: bool) -> str | None:
    """Ask Claude Code which login it will use, without calling a model; log it."""
    done = subprocess.run(
        [claude, "auth", "status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=60,
        check=False,
    )
    try:
        status = json.loads(done.stdout)
    except json.JSONDecodeError:
        return f"Could not read `claude auth status`: {(done.stdout + done.stderr)[:200]}"
    problem = login_problem(status, use_api_key)
    if problem is None:
        source = status.get("apiKeySource") or f"{status.get('subscriptionType')} subscription"
        logger.info("Running on: %s (%s)", status.get("authMethod"), source)
    return problem


@dataclass
class Turn:
    """One headless call: what was typed and what came back."""

    prompt: str
    reply: str
    is_error: bool
    cost: float


def _claude_turn(
    claude: str,
    prompt: str,
    folder: Path,
    config: Path,
    session: str | None,
    extra: list[str],
    env: dict[str, str],
) -> tuple[Turn, str]:
    command = [
        claude,
        "-p",
        prompt,
        "--output-format",
        "json",
        "--mcp-config",
        str(config),
        "--strict-mcp-config",
        "--allowedTools",
        *ALLOWED_TOOLS,
        "--disallowedTools",
        *DENIED_TOOLS,
        *extra,
    ]
    if session:
        command += ["--resume", session]
    done = subprocess.run(
        command,
        cwd=folder,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=_TURN_TIMEOUT,
        check=False,
    )
    try:
        data = json.loads(done.stdout)
    except json.JSONDecodeError:
        return Turn(prompt, done.stdout + done.stderr, True, 0.0), session or ""
    turn = Turn(
        prompt,
        str(data.get("result", "")),
        bool(data.get("is_error")),
        float(data.get("total_cost_usd") or 0.0),
    )
    return turn, str(data.get("session_id") or session or "")


def run_case(
    case: dict[str, Any],
    claude: str,
    out: Path,
    run: int,
    extra: list[str],
    env: dict[str, str] | None = None,
) -> list[str]:
    """Run one case once and return its problems; saves the transcript and the last reply.

    Args:
        case: An evals.json case with an ``agent`` block.
        claude: The Claude Code executable.
        out: Where transcripts and last replies go.
        run: The run number, for file names.
        extra: More arguments for every headless call (``--model``, a skill prompt).
        env: The agent's environment; defaults to ``agent_env()``, with no API keys.

    Returns:
        The judge's problems, plus one line if a turn failed outright.
    """
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / "course"
        folder.mkdir()
        fixtures = make_test_set(Path(tmp) / "fixtures")
        for name in case["attach"]:
            shutil.copyfile(next(p for p in fixtures if p.name == name), folder / name)
        config = Path(tmp) / "mcp.json"
        server = {"command": sys.executable, "args": ["-m", "wcag_tool.server"]}
        config.write_text(json.dumps({"mcpServers": {"wcag-tool": server}}), encoding="utf-8")
        before = snapshot(folder)

        names = ", ".join(case["attach"])
        prompts = [
            f"The course file in this folder: {names}. {case['turns'][0]}",
            *case["turns"][1:],
        ]
        turns: list[Turn] = []
        session: str | None = None
        for prompt in prompts:
            turn, session = _claude_turn(
                claude, prompt, folder, config, session, extra, env or agent_env()
            )
            turns.append(turn)
            if turn.is_error:
                break
        problems = judge(folder, before, Expectation.from_case(case))
        if any(t.is_error for t in turns):
            problems.insert(0, f"a turn failed: {turns[-1].reply[:200]}")

        stem = f"{case['id']}.run{run}"
        (out / f"{stem}.txt").write_text(turns[-1].reply if turns else "", encoding="utf-8")
        transcript = {
            "case": case["id"],
            "turns": [t.__dict__ for t in turns],
            "files_after": sorted(snapshot(folder)),
            "problems": problems,
        }
        (out / f"{stem}.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        return problems


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("cases", nargs="*", help="case ids; default every case with an agent block")
    parser.add_argument("--claude", default=os.environ.get("CLAUDE_BIN") or shutil.which("claude"))
    parser.add_argument("--runs", type=int, default=1, help="runs per case (default 1)")
    parser.add_argument("--out", type=Path, default=Path("agent-eval"), help="transcripts folder")
    parser.add_argument("--model", help="model for the agent, e.g. opus or sonnet")
    parser.add_argument(
        "--skill", action="store_true", help="also give the agent SKILL.md, as a skill would"
    )
    parser.add_argument(
        "--use-api-key",
        action="store_true",
        help="let Claude Code use an API key from the environment (billed); default is the "
        "subscription login",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # The judge re-scans copies; the package's own "scanned" lines are noise here.
    logging.getLogger("wcag_tool").setLevel(logging.WARNING)
    if not args.claude:
        logger.error("Claude Code not found: pass --claude or set CLAUDE_BIN.")
        return 2
    env = agent_env(args.use_api_key)
    problem = _check_login(args.claude, env, args.use_api_key)
    if problem:
        logger.error("Not running: %s", problem)
        return 2

    cases = [c for c in json.loads(EVALS.read_text(encoding="utf-8"))["cases"] if "agent" in c]
    if args.cases:
        cases = [c for c in cases if c["id"] in args.cases]
    extra: list[str] = []
    if args.model:
        extra += ["--model", args.model]
    if args.skill:
        extra += ["--append-system-prompt", SKILL.read_text(encoding="utf-8")]
    args.out.mkdir(parents=True, exist_ok=True)

    failed = 0
    for case in cases:
        for run in range(1, args.runs + 1):
            problems = run_case(case, args.claude, args.out, run, extra, env)
            failed += bool(problems)
            status = "pass" if not problems else "FAIL"
            logger.info("%s run %d: %s", case["id"], run, status)
            for problem in problems:
                logger.info("    %s", problem)
    logger.info("Transcripts and last replies in %s; grade the words with:", args.out)
    logger.info("    python skill/scripts/grade.py --for mcp %s/KAT-*.txt", args.out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
