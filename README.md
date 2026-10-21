# Document Accessibility Triage

A toolkit for checking course files (Word, PowerPoint and PDF) against the WCAG 2.1 AA
accessibility standard. It finds the problems a machine can see, fixes the few that are safe to fix
automatically, drafts suggestions for the ones only the author can decide, and tells you plainly
what it did not check. It never tells you a file is "compliant," because no scan can know that.

**Why it was built, and why it works the way it does:** read [ABOUT.md](ABOUT.md).

## Pick the version that fits you

| If you… | Use | Setup |
| :--- | :--- | :--- |
| have a BoodleBox account and want to try it right now | **the BoodleBox bot** | none: open the link |
| use Claude, ChatGPT or Gemini | **the skill** | about 5 minutes: upload one zip file |
| have a whole folder of course files and want fixes made to copies, with a record | **the MCP server** | about 15 minutes, once, on your own computer |

All three follow the same rules. The bot answers with a numbered list in plain words (what is
wrong, what to do, who does it, and when it counts as done); the skill and the server give a table
you can sort and assign. They also differ in how much of each file they can see: the bot reads
files as plain text, the skill can read the files themselves when your assistant is allowed to run
code, and the server reads them directly and can repair copies.

## Option 1: the BoodleBox bot

**Open [Document Accessibility Triage on BoodleBox](https://box.boodle.ai/a/@wcag-tool)**, sign in
with your BoodleBox account, upload a course file, and type *Triage this file.*

**To build your own copy** (for example, to adapt it for your campus), download
`wcag-triage-bot.zip` (see [Downloading the files](#downloading-the-files)) and follow
[bot/BOODLEBOX_BOT.md](bot/BOODLEBOX_BOT.md). The zip holds the instruction text, the greeting
the bot opens with, the seven knowledge files, and a set of fictional course files for testing it.

## Option 2: the skill

The same file works in Claude, ChatGPT and Gemini: `wcag-triage-skill.zip`. Download it (see
[Downloading the files](#downloading-the-files)) and leave it zipped.

### Claude (claude.ai or the Claude desktop app)

1. Open **Settings**, then **Capabilities**, and make sure code execution is turned on; skills
   need it.
2. Further down that page, in the **Skills** section, upload `wcag-triage-skill.zip`.

### ChatGPT

1. Open **Skills**, choose **Create**, then **Upload from your computer**, and pick
   `wcag-triage-skill.zip`.
2. ChatGPT scans every uploaded skill before it can be used. If it is marked **Needs Review**, read
   what ChatGPT flagged before you turn it on. On a campus Enterprise or Edu account, your
   workspace administrator may need to allow skill uploads first.

### Gemini (in a web browser at gemini.google.com, or the Gemini app for Mac)

1. Create a new skill and choose to upload a file, then pick `wcag-triage-skill.zip`. Uploading is
   not available in the Gemini phone apps.

Then, in any of the three, start a new chat, attach a course file, and type *Triage this file.* The
assistant asks three short questions first, one at a time, then gives you a table of what it
found, who should fix each item, and what is still unchecked.

### If an upload is refused

Each platform has its own rules about what a skill folder may contain.
Only three parts are essential: `SKILL.md` and the `references` and `rules` folders. If an upload
fails, unzip the file, delete optional parts in this order, zip the folder again (the folder
itself, so `SKILL.md` sits inside it), and retry after each deletion:

1. `tests/fixtures`: the practice course files. You lose the ready-made examples.
2. The rest of `tests`, plus `README.md` and `TESTING.md`: you lose the built-in self-check.
3. `scripts`: the assistant can no longer read files directly and will read them as plain text,
   which means it cannot see alt text, header rows or the language setting, and it will tell you so.

## Option 3: the MCP server, on your own computer

This version reads your files directly, makes the safe fixes to copies (your originals are never
changed), and keeps a record of every change. Your files never leave your computer. It works with
any AI assistant that can run a local MCP server; steps for the common ones are below.

**Before you start:** you need permission to install software on your computer. If your campus
manages your computer, check with IT first.

### Steps 1 to 3: install the tool's launcher (every assistant)

**Step 1. Open a terminal.** A terminal is a window where you type commands.

- Mac: press **Command + Spacebar**, type **Terminal**, and press **Return**.
- Windows: click **Start**, type **PowerShell**, and open **Windows PowerShell**.

**Step 2. Install uv.** uv is a small, free installer that fetches everything else the tool needs.
Copy the line for your computer, paste it into the terminal, and press Enter:

- Mac:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- Windows:

  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

When it finishes, **close the terminal and open a new one**, so it can find what was just
installed.

**Step 3. Find where uv put itself.** In the new terminal, run the line for your computer and copy
the path it prints:

- Mac: `which uvx` (prints something like `/Users/yourname/.local/bin/uvx`)
- Windows: `(Get-Command uvx).Source` (prints something like
  `C:\Users\yourname\.local\bin\uvx.exe`)

### Step 4: connect it to your assistant

Every assistant needs the same two things: the **command**, which is the path from step 3, and the
**arguments**, which are always these three:

```text
--from
git+https://github.com/adamwpryor/wcag-tool@v0.2.0
wcag-tool
```

Several assistants take them as a block of settings text, like this:

```json
{
  "mcpServers": {
    "wcag-tool": {
      "command": "PASTE THE PATH FROM STEP 3 HERE",
      "args": ["--from", "git+https://github.com/adamwpryor/wcag-tool@v0.2.0", "wcag-tool"]
    }
  }
}
```

Replace `PASTE THE PATH FROM STEP 3 HERE` with your path, keeping the quotation marks. **On
Windows, double every backslash**, so `C:\Users\yourname\.local\bin\uvx.exe` becomes
`C:\\Users\\yourname\\.local\\bin\\uvx.exe`. If the settings file you open is empty or holds only
`{}`, replace everything in it with the block. If it already has an `"mcpServers"` section, add
only the `"wcag-tool": { ... }` part inside it, with a comma between it and the entry before it.

**Claude Desktop.** Open **Settings**, then **Developer**, then **Edit Config**. Paste the block
into the file that opens and save it. Then quit Claude completely (closing the window is not
enough): on a Mac choose **Claude → Quit Claude**; on Windows right-click the Claude icon near the
clock and choose **Quit**. Open it again.

**ChatGPT desktop app.** Open **Settings**, then **MCP servers**, then **Add server**. Name it
`wcag-tool`, choose **STDIO**, enter the path from step 3 as the command and the three lines above
as its arguments (if the form has a single box, put it all on one line:
`PATH --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool`). Save, then choose
**Restart**. Local servers work in the desktop app, not in ChatGPT in a web browser.

**Google Antigravity.** In the agent panel, click **…** at the top, choose **MCP Servers**, then
**Manage MCP Servers**, then **View raw config**. Paste the block into the file that opens and save
it.

**Claude Code, Codex or Gemini CLI.** In a terminal:

- Claude Code: `claude mcp add wcag-tool -- uvx --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool`
- Codex: `codex mcp add wcag-tool -- uvx --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool`
- Gemini CLI: add the block to the `settings.json` file in the `.gemini` folder of your home
  folder.

**Any other assistant** that runs local MCP servers (Cursor and VS Code among them) takes the same
command and arguments; look for its MCP settings.

The first time the assistant starts the tool, it takes a minute or two while uv downloads
everything; after that it starts at once.

### Steps 5 and 6: try it

**Step 5. Make some practice files.** These are fictional course files with known problems, so you
can see what the tool does without touching your own. In the terminal, run:

```bash
uvx --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool demo ~/wcag-demo
```

This creates a folder called `wcag-demo` in your home folder with five files in it.

**Step 6. Ask for a triage.** In a new chat in your assistant, type:

> Triage the files in ~/wcag-demo.

Answer its three questions, read the table it gives back, and then ask *Is this file compliant
now?* The first sentence of the answer should be *No, and nothing I produce can say that.* When
you are ready to use your own files, give it the path to the folder they are in.

### If something goes wrong

- **The assistant says it has no wcag-tool, or the tool does not appear.** Check the path from
  step 3 (on Windows, with doubled backslashes in a settings file), make sure a settings file still
  starts with `{` and ends with `}`, and restart the assistant completely.
- **`which uvx` or `(Get-Command uvx).Source` prints nothing or an error.** Close the terminal,
  open a new one, and try again. If it still fails, run step 2 again.
- **The first try seems stuck.** The first start downloads the tool and can take a couple of
  minutes. Give it a moment, then ask again.
- **Anything else:** [open an issue](https://github.com/adamwpryor/wcag-tool/issues) describing
  what you typed and what you saw. Leave out any student information and any real course content.

## Downloading the files

You do not need a GitHub account.

1. Go to [the latest release](https://github.com/adamwpryor/wcag-tool/releases/latest) (or click
   **Releases** in the right-hand column of this page and open the newest one).
2. Under **Assets**, click the file you need: `wcag-triage-skill.zip` for the skill, or
   `wcag-triage-bot.zip` to build your own copy of the bot.
3. To look inside a zip: on Windows, right-click it and choose **Extract All**; on a Mac,
   double-click it. To upload the skill, leave it zipped.

## Check it before you share it

Before you hand the skill or your own copy of the bot to colleagues, run a few scripted
conversations and make sure the answers hold up. The most important test: attach a practice file,
ask for a triage, answer the three questions, then ask *Is this file compliant now?* Do it in three
fresh chats. Every time, the first sentence must be *No, and nothing I produce can say that.* If
even one answer says the file is compliant, do not share it yet.

The skill zip includes the full set of ten tests and a script that scores the answers;
`TESTING.md` inside the zip explains how to use them.

## For developers

```bash
conda env create -f environment.yml
conda activate wcag-tool
pytest -q
ruff check . && black --check . && mypy
python tools/build_skill.py           # builds the downloads into dist/ (not committed)
python tools/build_skill.py --check   # confirms the generated reference pages are current
```

Pushing a version tag (`git tag v0.3.0 && git push origin v0.3.0`) runs
`.github/workflows/release.yml`, which tests, builds and attaches both zips to that version's
release. The command-line tool runs the same engine without an AI assistant:

```bash
wcag-tool demo ./sample            # five fictional files with known problems
wcag-tool scan ./sample            # the routed table; add --json for data
wcag-tool fix ./sample/syllabus_section_01.docx --language en-US --apply mark-header-row:0
```

How the repository is organized is in [ABOUT.md](ABOUT.md#how-the-pieces-fit-together) and
[CLAUDE.md](CLAUDE.md); the reasoning behind each design choice is in
[docs/DECISIONS.md](docs/DECISIONS.md). Tests build their own fictional files, and no real course
file is ever committed.

## License

MIT, so take it, adapt it to your campus, and make it better. Criterion text quoted from
[WCAG 2.1](https://www.w3.org/TR/WCAG21/) is Copyright © W3C, used under the
[W3C Document License](https://www.w3.org/copyright/document-license-2023/).
