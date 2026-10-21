# Document Accessibility Triage

*An open toolkit for working through a pile of course files (Word, PowerPoint and PDF) against
WCAG 2.1 AA without pretending the work is finished before it is. It runs as a BoodleBox bot, as a
skill inside the AI assistant you already use, or as an MCP server on your own computer.*

Picture an associate professor of biology three weeks before the spring term. She is a composite,
not a real person, but there is nothing unusual in her folder. She has forty-one files in it: syllabi for three sections, a decade of lecture decks, lab
handouts, and a stack of PDFs, some exported from Word last year and some scanned from a book
chapter in 2014. An email from the provost's office has told her, politely, that all of it needs
to meet WCAG 2.1 AA, and she has heard enough about the federal rule to know the date is real.
What she wants, and what any of us would want in her chair, is a button. Point a tool at the
folder, let it find what is wrong, let it fix what is wrong, and get back to the lab she has been
meaning to revise for two years. When a member campus of the Council of Independent Colleges asked
for a tool that would detect and fix accessibility problems in course content, written for a
faculty member who will take the easiest route available, that button is what they were asking
for, and it is a completely reasonable thing to ask for.

This repository is my answer, and it does not contain that button. The button would be easy to
build, and plenty of products sell one. The trouble is what the button says when it finishes. It
says *fixed*, and *fixed* tells the professor something nobody has checked. The cost of that
sentence lands later and on someone else: on a student with a screen reader in week two, when the
lab handout's table reads aloud as a stream of unlabeled numbers and the quiz PDF arrives with no
structure at all. So this tool does triage instead. It reads the pile, finds the defects a machine
can actually see, repairs the small number whose repair invents no meaning, drafts proposals for
the ones only the author can settle, and routes everything else to a named person along with the
evidence they will need before anyone may call it done. And then, in plain words, it lists
everything it did not check, because the list of what was not checked is the part of a report
that keeps everyone honest.

## What comes back when you run it

Triage can sound like a slower way of saying no, and the first time you run it on a real folder it
can feel like one, so it helps to see what actually comes back. Every finding gets a **route**,
and the route is decided by what the fix needs from a person, never by how easy the fix looks. A
missing document title and a missing alt text are both small, but one can be repaired by anyone
who can read the file's properties and the other can only be written by someone who knows what the
picture is doing in this course. The routes put that difference on the page:

| Route | Who acts | What it looks like |
| :-: | :--- | :--- |
| 1 | The tool, with a before-and-after record | A missing document title; a missing document language, once you name the language |
| 2 | The person who made the file; the tool drafts | Alt text, table header rows, bold lines doing a heading's job, "click here" links |
| 3 | A person using a screen reader, with a named task | Reading order, keyboard operation, whether a student can actually finish the quiz |
| 4 | Whoever can act today; it overrides every other route | A file a currently enrolled student with an accommodation needs this week |
| 5 | Whoever owns the template or the export setting | The same missing header row in forty syllabi copied from one master |

The tool assigns Routes 1, 2 and 5. Routes 3 and 4 are always added by a person, because no scanner
can see that a student needs the file on Monday or that a quiz is impossible to finish with a
keyboard. Route 5 is where most of the time comes back: when three syllabi share the same defect,
the triage points at the template they were copied from, and one corrected template retires the
same finding in every section that used it. What you get for the pile is one table, with a column
for the owner that is left blank on purpose because it wants a person's name rather than an
office's, and a column saying what closes each row. There are four ways a finding may be closed
(the tool verified a deterministic repair, the author confirmed a proposal, an expert checked it
with the file open, or a person using assistive technology completed a named task), and *the
scanner no longer reports it* is deliberately not one of them.

Picture the instructional designer who opens that table on a Monday morning, a little grudgingly,
expecting a score and finding a work queue instead. She can see that three of the professor's
syllabi share a template, that the PDF from 2014 has no text layer at all, and that the alt text
for the cell diagram is waiting on the one person who knows what the diagram is meant to teach.
None of that is a verdict on the course. All of it is something a specific person can do this
week, which is the point. And at the bottom of every report sits the one sentence the campus may
honestly say about the files afterwards: *This file was checked for the criteria listed under
`evaluated` only. Route 1 findings can be repaired by the tool and re-scanned; Route 2 findings
carry proposals that a person who knows the content must confirm; criteria under `not_evaluated`
were not checked at all. A clean report is not a conformance claim.*

## Why it will never call a file compliant

That last sentence is the one people push back on, and I understand why. A scanner that has just
read every file in the folder sounds like it ought to be able to say whether the folder passes.
If it can find forty missing alt texts, the reasoning goes, surely it can tell me when there are
none left, and surely *none left* is what the provost's email was asking for. The research on
automated accessibility testing says otherwise, and one study in particular makes the reason easy
to feel, because it lets you watch two scanners look at the same thing and come back with
different worlds.

In 2022, Rita Ismailova and Yavuz Inal set out to learn how far the free online accessibility
checkers that campuses and governments rely on actually agree with one another. They took 41
government websites from different countries and ran each one through six evaluation tools,
counting the violations each tool reported against the WCAG guidelines
([Ismailova and Inal, 2022](https://doi.org/10.1109/ACCESS.2022.3179375)). The question
underneath was a practical one, the same one a provost asks when a vendor hands over a dashboard:
whether running a different checker would produce a different answer.

Try it yourself before reading the result. Two well-established checkers scan the same 41 sites,
looking only for Level A problems, the most basic tier of the standard. How far apart would you
expect their totals to be? If I'm honest, my own guess the first time would have been somewhere
between "about the same" and "maybe double," which is a sensible guess about two instruments
measuring the same thing.

One tool, Mauve, reported 14,927 Level A violations. Another, Examinator, reported 291. That is a
factor of roughly fifty, on the same pages, against the same tier of the same standard, and most
of Mauve's count fell under four criteria (non-text content, link purpose, page language, and
name, role, value). Neither tool was broken. Each one counted what it was built to see and was
silent about the rest, and the authors' own conclusion was that tools complement each other and
that more than one is needed for reliable data. Which means a single score tells you at least as
much about the scanner's boundary as it does about the site. Apply that to the professor's folder
and the problem with *compliant* becomes plain: whatever number a scanner hands her measures the
scanner first.

The boundary itself has been measured. A systematic mapping by Delvani Mateus and colleagues
gathered 38 studies (from an initial search of 304 articles) that had evaluated websites and
mobile apps with automated tools, with expert inspection, or by testing with users, and compared
which kinds of barriers each method turned up
([Mateus et al., 2021](https://doi.org/10.5753/jis.2021.1778)). On websites they documented 56
types of barrier. Automated tools detected 21 of those 56 types, a little over a third, and
fourteen types were found by both experts and users while no automated tool caught them at all.
On mobile apps the automated share was lower still. So even a perfect scan of the professor's
folder would be a perfect reading of about a third of what a student might run into.

A second study from the same research group looked at what happens when this goes to court. The
team read 124 federal digital-accessibility cases in the United States and found that every one
ended in a settlement agreement, most of them with obligations lasting months or years
([Mateus et al., 2024](https://doi.org/10.5753/jbcs.2024.3259)). Those agreements called for
automated evaluation in 31 cases, a quarter of them. They called for testing with users with
disabilities in 108, or 87.1 percent. When the question that decides a case is whether a person
can complete a task, the remedy reaches for people, and that is why every report this tool writes
ends by saying the files that matter most still need one person with a screen reader and a named
task.

None of this makes scanners useless. This tool is a scanner, and the defects it finds are real
defects worth fixing; a missing header row is missing whatever else the file gets right. But a
scan is a lead, not a verdict, and a toolkit built for campuses has to say plainly which one it is
handing over. A campus that files a lead as a verdict stops looking, and it stops looking in
exactly the places the scanner could not see, which are the places a student is still stuck.

## Why it fixes so little on its own

The same honesty shapes what the tool will change without asking. It repairs exactly two things
by itself: the document title, and the document language once a person has said what the language
is. Both pass the four tests that every automatic repair here has to pass. The rule is
deterministic, the repair invents no meaning, it can be undone and scanned again, and it cannot
quietly change an assessment or a student's task. Everything else fails at least one of those
tests, usually the second. Marking a bold line as a heading asserts that the author meant it as
the start of a section, and at a particular level. Marking a table's first row as its header row
asserts that the row holds column names rather than data. Writing alt text asserts what an image
is for in this course, and the tool was not in the lecture. So the tool proposes each of those,
labels every draft as a draft, and applies one only when the person who owns the file names that
specific fix. A yes to the whole batch counts as a yes to nothing.

The language is the case that taught me the most. An earlier version wrote `en-US` into every file
by default, which seemed harmless until a review pass caught that it is a fact the tool made up,
and a wrong language setting makes a screen reader mispronounce every word in a Spanish course
reader. Now the language repair waits until someone names the language, and the report says it is
waiting. The original file is never written to either: every repair goes into a copy saved beside
it, with a record of what was found before, what was changed, and what is still open after.

PDFs get the shortest answer, and the tool gives it in the same words every time. *A PDF is the
end of the line, not the place to fix things. The fastest honest path is back to the Word or
PowerPoint file, fix it there, and export again. If that file is gone, the PDF needs a person with
Acrobat, and the tool will not pretend otherwise.* It will set a PDF's title and language, and it
will tell you whether the file is tagged at all, but it will not build a tag tree, because
open-source tools cannot build one well and a weak one implies a repaired file that is not there.

## One set of rules, three ways to run them

Campuses meet AI through whatever their institution has licensed. Some use BoodleBox, some have
campus licenses for Claude or ChatGPT or Gemini, and some faculty
have nothing but a browser, a personal account and a deadline. A toolkit that runs in only one of
those places works for almost nobody, and the professor with forty-one files will not switch
platforms to use it. So the same rules are rendered three ways, and each one can do a little more
than the last, depending on what the platform allows.

| | BoodleBox bot | Skill | MCP server |
| :--- | :--- | :--- | :--- |
| Install | Nothing | Nothing, or upload a zip | About ten minutes |
| Reads your file | As text | As text, or the file itself where the assistant can run code | The file itself |
| Changes your file | Never | Never | The title automatically, the language once you name it, the rest only by named fix, always in a copy |
| Best for | Trying the triage on one file today | Faculty and staff in Claude, ChatGPT or Gemini | A whole folder, with a record of every change |

The difference that matters most is the second row. Read as plain text, a Word file hides most of
what a screen reader depends on: whether an image has alt text, whether a table's header row is
marked, what language the document declares, whether a line is a real heading or just bold. The
bot cannot see any of that, and it says so in its first answer, which is why it is the gentlest
place to start and the least complete. The skill can read the file itself wherever the assistant
is allowed to run code, and the server reads it directly and can repair the copy. The rules that
must never break (never certify, never invent meaning, route before you fix) sit in the
instruction text of every version, never only in an attached file, because an assistant searching
its attachments may not retrieve the one paragraph that tells it to refuse.

### The BoodleBox bot

No installation at all. `bot/BOODLEBOX_BOT.md` is the build sheet: the instruction text to paste
(built into `dist/wcag-triage-bot/instructions.md`), the seven knowledge files to attach (in
`dist/wcag-triage-bot/knowledge/`), the settings, and the conversation tests to run before
sharing it. Build the folder with `python tools/build_skill.py`.

### The skill

`dist/wcag-triage-skill.zip` is a skill folder for assistants that take one. Where the assistant
can run code, `scripts/scan.py` reads the files themselves without changing them, and
`scripts/selftest.py` checks the scanner against seven fictional files whose defects are known in
advance. `TESTING.md` inside the zip walks whoever receives it through checking that it works
before they share it. `dist/wcag-triage.md` is the same instructions and reference pages joined
into one file, for pasting into any chat. The prose behind both lives in `skill/`.

### The MCP server, on your own computer

This is the version that does the most, and your files never leave your machine. It works with
any assistant that accepts MCP servers, including Claude Desktop, Claude Code, ChatGPT desktop,
Gemini CLI, Cursor and VS Code. The quick start uses [uv](https://docs.astral.sh/uv/), which
fetches the right version of Python and the tool the first time it runs, so there is nothing else
to set up.

1. Install uv, once.
   - macOS or Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Find where it put `uvx`: `which uvx` on macOS or Linux, `where uvx` on Windows. Claude Desktop
   does not read your shell's PATH, so the configuration below uses that full path.
3. In Claude Desktop, open *Settings → Developer → Edit Config* and add the following, with your
   path in `command`:

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
   backslash doubled. In Claude Code, run this instead:
   `claude mcp add wcag-tool -- uvx --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool`
4. Restart Claude Desktop. The first launch takes a minute while uv downloads everything; after
   that it starts at once. Make some fictional files to try it on:
   `uvx --from git+https://github.com/adamwpryor/wcag-tool@v0.2.0 wcag-tool demo ~/wcag-demo`
5. In a new chat, type *"Triage the files in ~/wcag-demo."* Then ask whether a file is compliant
   now, and read the first sentence of the answer.

If you would rather use pip or conda, `pip install git+https://github.com/adamwpryor/wcag-tool`
(or `conda env create -f environment.yml` in a clone) installs a `wcag-tool` command, and the
configuration uses the full path to it in place of `uvx`.

The server gives the assistant five tools. `scan_folder` is the place to start: it reads every
Word, PowerPoint and PDF file under a folder and returns the routed table ready to fill in, with
the Route 5 lines that point at shared templates. `scan_document` does the same for one file.
`fix_document` writes the repaired copy and its record, and applies a Route 2 fix only when its
`fix_id` is named after the owner has confirmed it. `describe_routes` explains the routes and the
closure states. `explain_criterion("1.3.1")` quotes W3C's own wording for a criterion and says what
the tool can and cannot judge about it in each format, which is what the assistant should reach
for when the professor asks why any of this matters.

Without an MCP client, the same engine runs from the command line:

```bash
wcag-tool demo ./sample            # five fictional files with known defects
wcag-tool scan ./sample            # the routed table as Markdown; --json for the data
wcag-tool fix ./sample/syllabus_section_01.docx --language en-US --apply mark-header-row:0
```

## Why the rules live in data files

Three versions of one triage only help if they say the same thing, and the first version of this
repository kept the rules the way most projects do, typed by hand into each place that needed
them. The scanner had its list, the reference page had its table, the template proposals had their
own map, and the bot would have had a fourth copy. Nothing checked that they agreed, and when I
finally compared them, one already disagreed with itself: the check for skipped heading levels
reported its findings under one WCAG criterion while the list of what the tool evaluates filed the
same check under another. It was a small error, and the kind that never announces itself. A
report would have looked complete and been quietly wrong about which criterion it had checked.

So the rules now live in three data files in `src/wcag_tool/rules/`. `wcag21.json` holds all 50
Level A and AA success criteria in W3C's own words, extracted from the published standard by a
script anyone can re-run. `checks.json` holds every check the scanner runs, with its criterion, its
route, its closure state, its fix and its wording. `coverage.json` holds, for every criterion in
every file format, whether a check covers part of it, what a person still has to judge, and who
that person is. The tool refuses to start if the three disagree, the reference pages and the bot's
knowledge files are generated from them, and the build fails if any page falls behind. One
consequence I like a great deal: every report now names all 50 criteria, either as checked in
part or as not checked, so nothing can read as passed simply because it was left off the list.

I did consider a vector database here, a searchable index of the WCAG documents that an assistant
could query for context. It turned out to be the wrong tool for this particular job. Every finding
already knows its criterion number, so the explanation is a lookup by number rather than a search,
and a lookup returns the same text every time. A similarity search would occasionally hand back
the criterion next door (1.3.2 for a 1.3.1 finding), and nothing in the report would flag it. For
a triage whose whole value is that it says the same thing on Tuesday that it said on Monday, exact
beats clever. The reasoning behind this and the other design choices is written up in
`docs/DECISIONS.md`.

## Checking that it works before you share it

Repeatability is the other half of trust, so the toolkit ships with its own tests and they are
meant for the people receiving it, not only for whoever maintains the code. The scanner half is
exact: `python skill/scripts/selftest.py` runs the checks against seven fictional course files
and compares every finding with a saved expected result, and any difference is printed. The
conversation half cannot be exact, because a language model never answers word for word the same
way twice, so it is measured instead. `skill/tests/evals.json` holds ten short scripted
conversations, and `python skill/scripts/grade.py` scores the saved replies, checking for the
banned words, for any score or percentage, and for the scripted first sentence when someone asks
whether a file is compliant. Run each conversation three times and look at the pass rate. The
compliance question has to pass every single run, because a bot that says *compliant* once in three
tries will eventually say it to a dean.

## Working on the code

```bash
conda env create -f environment.yml
conda activate wcag-tool
pytest -q
ruff check . && black --check . && mypy
python tools/build_skill.py --check     # generated reference pages are current
```

The tests build their own fictional fixtures, two of them drive the server over the real MCP
protocol, and no real course file is ever committed (`.gitignore` refuses `.docx`, `.pptx` and
`.pdf`). `CLAUDE.md` describes how the repository is laid out and the steps for adding a check.

## Where this came from

I built this as the October 2026 subject of "Name the Problem, Build the Tool," the build segment
of the CIC AI Ready *All Campus Essentials* series, where each month we name one problem campuses
keep running into and build a tool for it in the open (I lead those build sessions, and this
month's problem arrived as a request from a member campus). The request came with a date
attached. The Department of
Justice's rule under Title II of the Americans with Disabilities Act names WCAG 2.1 AA as the
standard for the websites, apps and online course content of public colleges and universities,
and an interim final rule this April moved its compliance dates to April 26, 2027 for public
entities serving 50,000 people or more and April 26, 2028 for smaller ones and special districts
([Federal Register, April 20, 2026](https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web)).
Most CIC members are private colleges, which that rule does not bind directly, and the request
came from one of them anyway, because a federal rule with a named standard and a named date gets
heard well beyond the institutions it covers. None of this is legal advice; what applies to your
campus is a question for your accessibility coordinator or your counsel.

The toolkit is MIT licensed, so take it, adapt it to your campus, and make it better. Criterion
text in `skill/references/criteria.md` and `src/wcag_tool/rules/wcag21.json` is quoted from
[WCAG 2.1](https://www.w3.org/TR/WCAG21/), Copyright © W3C, under the
[W3C Document License](https://www.w3.org/copyright/document-license-2023/).

*A disclosure, since this page names a company: through my work with CIC, I've had relationships
with several AI companies, including BoodleBox. The triage is not built around any one of them,
and every version runs on the same rules.*
