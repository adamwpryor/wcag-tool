# wcag-tool

Finds WCAG 2.1 AA problems in course documents (Word, PowerPoint, PDF), fixes the ones whose
repair invents no meaning, drafts proposals for the ones that need the author, and routes the rest
to a named person with the evidence each needs before it can be called done.

It never claims conformance. That is a feature.

## The honest version of "detect and fix"

Automated checks find roughly a third of the barrier types people actually hit, and different
scanners disagree about the same pages by very large factors. So this tool does not produce a
score. Every finding gets a **route**:

| Route | Who acts | Example |
| :-: | :--- | :--- |
| 1 | The tool, with a before-and-after record | Missing document title, missing document language |
| 2 | The person who made the file; the tool drafts | Alt text, table header rows, fake headings, "click here" links |
| 3 | A person with a screen reader and a named task | Reading order, keyboard operation |
| 4 | Whoever can act today; overrides the rest | A file a currently enrolled student needs |
| 5 | Whoever owns the template | The same defect in forty syllabi |

And every closure needs one of four evidence states. "No longer reported by the scanner" is not
one of them.

**PDF is the end of the line, not the place to fix things.** The tool sets a PDF's title and
language. It will not pretend to tag one. An untagged PDF is routed back to its Word or
PowerPoint source for re-export, or to a person with Acrobat.

## Three ways to use it

### 1. The MCP server, on your own machine, with your own assistant

Files never leave your computer. Any MCP client works: Claude Desktop, Claude Code, ChatGPT
desktop, Gemini CLI, Cursor, VS Code.

**Quick start: about ten minutes, no Python setup.** It uses
[uv](https://docs.astral.sh/uv/), which fetches the right Python and the tool on first launch.

1. Install uv, once.
   - macOS or Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Find where it put `uvx`: `which uvx` on macOS or Linux, `where uvx` on Windows. Claude Desktop
   does not read your shell's PATH, so the configuration below uses that full path.
3. In Claude Desktop, open *Settings → Developer → Edit Config* and add, with your path in
   `command`:

   ```json
   {
     "mcpServers": {
       "wcag-tool": {
         "command": "/Users/you/.local/bin/uvx",
         "args": ["--from", "git+https://github.com/adamwpryor/wcag-tool@v0.2.0", "wcag-tool"]
       }
     }
   }
   ```

   On Windows the path looks like `"C:\\Users\\you\\.local\\bin\\uvx.exe"`, with every
   backslash doubled. In Claude Code instead:
   `claude mcp add wcag-tool -- uvx --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool`
4. Restart Claude Desktop. The first launch takes a minute while uv downloads; after that it is
   instant. Make some fictional files to try it on:
   `uvx --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool demo ~/wcag-demo`
5. In a new chat: *"Triage the files in ~/wcag-demo."* Then try *"Is it compliant now?"*

**With pip or conda instead:** `pip install git+https://github.com/adamwpryor/wcag-tool` (or
`conda env create -f environment.yml` in a clone), then `"command": "wcag-tool"` with the full
path to that executable.

Five tools: `scan_document(path)`, `scan_folder(path)`, `fix_document(path, apply=[...])`,
`describe_routes()`, `explain_criterion(criterion)`. `scan_folder` is the one to start with: it
adds Route 5 candidates (a defect that recurs across files, so the fix is the template) and
returns the routed table ready to fill in. `fix_document` writes a copy next to the original and a
JSON record of before and after. The original is never overwritten. Route 2 fixes are applied only
when you name their `fix_id` after confirming the proposal. `explain_criterion("1.3.1")` quotes
W3C's text for a criterion and says what the tool can and cannot judge about it in each format.

**No MCP client? The same engine runs from the command line.**

```bash
wcag-tool demo ./sample            # five fictional files with known defects
wcag-tool scan ./sample            # the routed table as Markdown; --json for the data
wcag-tool fix ./sample/syllabus_section_01.docx --language en-US --apply mark-header-row:0
```

Without `--language` the language fix is held and reported, not guessed. The tool never writes a
fact nobody stated.

### 2. The skill, in any assistant

`dist/wcag-triage.md` is one file to paste into Claude, ChatGPT or Gemini.
`dist/wcag-triage-skill.zip` is the skill folder, and it does more: where the assistant can run
code, `scripts/scan.py` reads the files themselves (read-only), and `scripts/selftest.py` checks
the scanner against fictional files with known answers. `TESTING.md` inside it says how to check
the skill works before you share it. Build them with:

```bash
python tools/build_skill.py
```

The prose lives in `skill/`; the rules live as data in `src/wcag_tool/rules/`. See
`skill/README.md` for how to use the set.

### 3. The BoodleBox bot

`bot/BOODLEBOX_BOT.md` is the build sheet: the instruction file to paste, the knowledge files to
attach (all built into `dist/wcag-triage-bot/`), the settings, and the tests to run before
publishing.

## The rules, as data

`src/wcag_tool/rules/` holds three JSON files with schemas: `wcag21.json` (the 50 A and AA
criteria, quoted from W3C), `checks.json` (every check: criterion, route, closure, fix, wording),
and `coverage.json` (for every criterion in every format, what is checked in part, what is not,
and who judges the rest). The scanner, the skill's reference pages and the bot's knowledge files
are all built from them, and the build fails if they disagree. See `docs/DECISIONS.md` §8.

## Development

```bash
conda env create -f environment.yml
conda activate wcag-tool
pytest -q
ruff check . && black --check . && mypy
python tools/build_skill.py --check     # generated reference pages are current
```

Tests generate their own fixtures. No real course file is ever committed; `.gitignore` refuses
`.docx`, `.pptx` and `.pdf`.

## Why it exists

Built for the CIC AI Ready *All Campus Essentials* series as the October 2026 "Name the Problem,
Build the Tool" subject, from a member's request for a tool faculty could point at their files
ahead of the ADA Title II deadline of April 26, 2027. The skill, the bot and the server are three
renderings of one rule set, so that a campus on any platform gets the same triage.

Adapt freely. MIT licensed.
