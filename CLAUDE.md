# wcag-tool: Claude Code Context

## What this repo is

Three renderings of one rule set for triaging course documents (DOCX, PPTX, PDF) against WCAG 2.1
AA, built for the CIC AI Ready *All Campus Essentials* October 2026 Week 3 build segment and
published so any campus can use it:

| Artifact | Lives in | Built by | Consumed as |
| :--- | :--- | :--- | :--- |
| **Skill** (the prose) | `skill/SKILL.md` + `skill/references/` + `skill/scripts/` + `skill/tests/` | `python tools/build_skill.py` → `dist/` | Pasteable file, skill zip (with a read-only scanner and a test kit), README |
| **BoodleBox bot** | `bot/BOODLEBOX_BOT.md` (build sheet) + `bot/instructions.md` (session flow) | By hand, from `dist/wcag-triage-bot/` | Hosted bot, no install, no code, never a tool |
| **MCP server + CLI** | `src/wcag_tool/` | `pip install -e .` → `wcag-tool` | Local stdio server in any MCP client (no args), or `scan` / `fix` / `demo` subcommands |

**The rules are data in `src/wcag_tool/rules/`**: `wcag21.json` (W3C's text, extracted by
`tools/extract_wcag.py`), `checks.json` (every check), `coverage.json` (every criterion × format).
`wcag_tool.rules` refuses to load if they disagree. The scanners, the tables in `checks.md`, the
whole of `criteria.md`, the Route 5 proposals and the bot's knowledge files are built from them.
**`skill/` is the source of truth for the prose.** The MCP tool descriptions, the bot
instructions, and the reference pages must say the same thing. If a route or a closure state
changes, change `skill/references/routes.md`, `src/wcag_tool/findings.py`, `rules.py` and the
schemas in the same commit. Never hand-edit a `<!-- generated -->` block or `criteria.md`.

**The bot is the one exception to a shared session flow.** BoodleBox never gets an MCP server or
a code sandbox, so `bot/instructions.md` is written for a bot with no tool: its own opening,
one-turn intake, triage layout and length limits, and no tool names. The never-break rules are
not rewritten there: an `<!-- include:SKILL.md#... -->` line splices them in word for word at
build time, and a test fails if the splice is missing or a tool name leaks in. Change the rules
in `SKILL.md`; change how the bot talks in `bot/instructions.md`.

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
pytest -q                              # tests build their own fixtures; two run the real MCP wire
ruff check . && black --check . && mypy
python tools/build_skill.py            # regenerates checks.md blocks, criteria.md, and dist/
python tools/build_skill.py --check    # exit 1 if a generated page is stale (a test runs this)
python skill/scripts/selftest.py       # scanner vs tests/expected; --update after a deliberate change
wcag-tool                              # starts the stdio server; blocks waiting for a client
wcag-tool demo ./sample                # five fictional files for the live demo
wcag-tool scan ./sample                # routed table with Route 5 lines; --json for data
```

## Module map

| Module | Owns |
| :--- | :--- |
| `rules.py` + `rules/*.json` | The rule set as data: load, cross-check, evaluated / not-evaluated lists, Markdown renderers |
| `findings.py` | `Finding` (built with `Finding.from_check`), `Report`, the routes and closure enums, the bounded claim |
| `report.py` | `Batch` (a pile), Route 5 aggregation, `render_markdown` |
| `engine.py` | dispatch by extension, `scan`, `scan_many`, `scan_folder`, `fix` |
| `docx_checks.py` / `docx_fixes.py`, `pptx_checks.py`, `pdf_checks.py` | per-format checks and fixes |
| `alt.py` | alt text that is present but says nothing (filenames, auto phrases) |
| `demo.py` | minimal fictional fixture files, shared by tests, the selftest and the `demo` command |
| `course_pack.py` | a realistic fictional course pack for testing the bot by hand; built into `dist/wcag-triage-bot/test-files/` |
| `server.py` | the five MCP tools |
| `cli.py` | the console entry point |

## Adding a check

1. Add the check to `src/wcag_tool/rules/checks.json`: id `<format>.<kebab-name>`, criterion,
   route, closure, confidence, `fix_id` template, wording, `template_fix`, `from_text`.
2. Set that criterion's cell in `coverage.json` to `checked_in_part`, with what a person still
   judges. `rules.load()` refuses a check whose cell says otherwise.
3. In the format's `scan()`, append `Finding.from_check("<id>", asset=, locator=, evidence=)`.
   Everything else comes from the JSON.
4. Add the defect to a fixture builder in `src/wcag_tool/demo.py`: the demo pile if it belongs
   in the live demo (then update the expected values in ace-1's `October_Build/20_Test_Kit.md`),
   otherwise `make_test_set`. A test fails if any check never fires.
5. Run `python tools/build_skill.py` (regenerates `checks.md` and `criteria.md`) and
   `python skill/scripts/selftest.py --update`, and read the diff of `skill/tests/expected/`.
6. If it carries a `fix_id`, add the fix to the format's `apply()` and decide its route honestly.

## Where things were left

See `docs/HANDOFF_2026-10-19.md` for the compacted history and the next steps, and
`docs/DECISIONS.md` for why the repo is shaped this way (§8–11 cover the rules-as-data move,
the decision against a vector database, pypdf, and the three tiers).
