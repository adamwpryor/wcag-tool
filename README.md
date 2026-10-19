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

```bash
pip install wcag-tool          # or: conda env create -f environment.yml
wcag-tool                      # runs over stdio; your client launches it
```

Claude Desktop configuration, for example:

```json
{
  "mcpServers": {
    "wcag-tool": { "command": "wcag-tool" }
  }
}
```

Three tools: `scan_document(path)`, `fix_document(path, apply=[...])`, `describe_routes()`.
`fix_document` writes a copy next to the original and a JSON record of before and after. The
original is never overwritten. Route 2 fixes are applied only when you name their `fix_id` after
confirming the proposal.

### 2. The skill, in any assistant

`dist/wcag-triage.md` is one file to paste into Claude, ChatGPT, Gemini, or a BoodleBox bot's
instructions. `dist/wcag-triage-skill.zip` is the same material as a skill folder. Build them with:

```bash
python tools/build_skill.py
```

The rules live in `skill/`. See `skill/README.md` for how to use the set.

### 3. The BoodleBox bot

`bot/BOODLEBOX_BOT.md` is the build sheet: the instruction file to paste, the files to attach, the
settings, and the five-question known-answer test to run before publishing.

## Development

```bash
conda env create -f environment.yml
conda activate wcag-tool
pytest -q
ruff check . && black --check .
```

Tests generate their own fixtures. No real course file is ever committed; `.gitignore` refuses
`.docx`, `.pptx` and `.pdf`.

## Why it exists

Built for the CIC AI Ready *All Campus Essentials* series as the October 2026 "Name the Problem,
Build the Tool" subject, from a member's request for a tool faculty could point at their files
ahead of the ADA Title II deadline of April 26, 2027. The skill, the bot and the server are three
renderings of one rule set, so that a campus on any platform gets the same triage.

Adapt freely. MIT licensed.
