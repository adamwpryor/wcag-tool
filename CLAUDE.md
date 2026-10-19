# wcag-tool: Claude Code Context

## What this repo is

Three renderings of one rule set for triaging course documents (DOCX, PPTX, PDF) against WCAG 2.1
AA, built for the CIC AI Ready *All Campus Essentials* October 2026 Week 3 build segment and
published so any campus can use it:

| Artifact | Lives in | Built by | Consumed as |
| :--- | :--- | :--- | :--- |
| **Skill** (the rules) | `skill/SKILL.md` + `skill/references/` | `python tools/build_skill.py` → `dist/` | Pasteable file, skill zip, README |
| **BoodleBox bot** | `bot/BOODLEBOX_BOT.md` (build sheet only) | By hand, from `dist/wcag-triage.md` | Hosted bot, no install |
| **MCP server** | `src/wcag_tool/` | `pip install -e .` → `wcag-tool` | Local stdio server in any MCP client |

**`skill/` is the source of truth for the rules.** The MCP tool descriptions, the bot
instructions, and the reference pages must say the same thing. If a route or a closure state
changes, change `skill/references/routes.md` and `src/wcag_tool/findings.py` in the same commit.

The origin and the session-facing materials stay in the private `ace-1` repo
(`output/ace/2026.10/October_Build/`). This repo never carries session logistics, speaker names,
sponsor material, or anything from a real course file.

## Non-negotiables

1. **Never certify.** No output, docstring, README line or test name may describe a clean report
   as conformance. The bounded claim in `skill/references/bounded-claim.md` is the ceiling.
2. **Route 1 is title and language only** until a new check passes all four tests in
   `routes.md`: deterministic, invents no meaning, reversible and re-scannable, cannot alter an
   assessment. Everything else is Route 2 with a `proposal`, applied only when its `fix_id` is
   named in `apply`.
3. **The original file is never overwritten.** `engine.fix` writes `<stem>.remediated<ext>` and a
   `.remediation.json` record beside it.
4. **PDF tagging is out of scope.** The tool says so in the words from `checks.md`. Do not add a
   fix that implies otherwise.
5. **Not evaluated is reported, never silently passed.** Every scanner module keeps an
   `EVALUATED` and a `NOT_EVALUATED` list and they ship in every report.
6. **No real course file enters the repo.** Tests build fixtures in `tmp_path`. `.gitignore`
   refuses `.docx`, `.pptx`, `.pdf`.
7. **Stdout is the MCP wire.** Logging is JSON to stderr via `wcag_tool.log`. No `print()`.

## Environment

- Conda-first: `conda env create -f environment.yml`, env name `wcag-tool`. On this machine conda
  is not on PATH; use `%USERPROFILE%\anaconda3\Scripts\conda.exe` and
  `%USERPROFILE%\anaconda3\envs\wcag-tool\python.exe`.
- `mcp` is the one pip dependency (PyPI first). Move it to the conda-forge block when the v2
  feedstock is current.
- MCP Python SDK **v2**: `from mcp.server import MCPServer`. The v1 `FastMCP` import is gone.
- `pyproject.toml` exists so `pip install wcag-tool` works for people outside this machine.
  `environment.yml` stays primary for development.
- Black and Ruff at line length 100, Google docstrings, type hints on every signature.

## Commands

```bash
pytest -q                              # tests build their own fixtures
ruff check . && black --check .
python tools/build_skill.py            # regenerates dist/ (gitignored)
wcag-tool                              # starts the stdio server; blocks waiting for a client
```

## Adding a check

1. Add it to the format's `scan()` with a `check` id of the form `<format>.<kebab-name>`, the
   WCAG criterion, a route, a closure state, a confidence, and a `proposal` if Route 2.
2. Add the criterion to that module's `EVALUATED` list, or the gap to `NOT_EVALUATED`.
3. Add the row to `skill/references/checks.md` in the same commit.
4. Add a fixture defect in `tests/conftest.py` and an assertion.
5. If it carries a `fix_id`, add the fix to the format's `apply()` and decide its route honestly.

## Where things were left

See `docs/HANDOFF_2026-10-19.md` for the compacted history and the next steps, and
`docs/DECISIONS.md` for why the repo is shaped this way.
