# Document accessibility triage: the rules, as files you can take anywhere

These files are the rules behind the document accessibility triage, written so that you can run
the same triage in whichever AI assistant your campus already uses. Nothing here certifies
anything; it is a structured way of turning a pile of course files into a work queue where every
problem has an owner and the evidence it needs before it can be called done.

## What is in the set

| File | What it is |
| :--- | :--- |
| `wcag-triage.md` | **Everything in one file.** The instructions and all five reference pages, joined. Paste it into a chat, or attach it, and say *"triage these files."* |
| `wcag-triage-skill.zip` | The skill folder, and the most capable way to run it without installing anything else: `SKILL.md`, the reference pages, the rules as JSON, a read-only scanner the assistant can run where it can run code, and a test kit (`TESTING.md`) to check it works before you share it. |
| `wcag-triage-gemini.zip` | The same skill for Gemini, which cannot run the script files a skill carries. The scanner is in `scanner/` as Markdown; Gemini saves it into its code sandbox and checks every part before it scans. No test kit: its checks run Python scripts. |
| `wcag-triage-bot/` | The BoodleBox bot: `instructions.md` for the instruction field, and `knowledge/` to attach. |
| `README.md` | This page. |

## How to use it

**In a chat assistant.** Claude, ChatGPT, Gemini, or whichever you have. Start a new conversation,
attach `wcag-triage.md` or paste its contents, and type: *"Triage these files."* It asks only
what you have not already told it, reads every page, and gives you one list to work through:
the whole document first, then page by page, each item with the clicks to make and draft alt
text where a picture needs it. Read as text, a file hides some of what matters (alt text, header
rows, the language setting); those items say so and tell you how to check.

**As a skill, where the assistant can run code** (claude.ai with code execution, Claude Code).
Upload `wcag-triage-skill.zip` as a skill. The assistant then runs `scripts/scan.py` on your files
and sees what a text paste cannot, then reads every page for what no scan sees (colour-only
instructions, "click here" links, pictures of text). It still changes nothing. In Gemini,
upload `wcag-triage-gemini.zip` instead; it runs the same scanner from Markdown.

**With the wcag-tool connected.** If your assistant takes MCP servers, install `wcag-tool` and
the same instructions also apply the safe repairs (title and language) to a copy of each file, on
your own machine. Your files never leave it. See the repository README.

**In BoodleBox.** See `bot/BOODLEBOX_BOT.md` in the repository: paste `instructions.md`, attach
the files in `knowledge/`.

**With colleagues.** Send them the zip and tell them to run `TESTING.md` first. Nothing in it is
specific to you or your campus.

## Two rules while you use it

1. **Describe the course, never the students.** The triage needs to know what a file is for; it
   never needs a student's name, accommodation letter, or grade. Do not paste those anywhere.
2. **Use an account you are allowed to use for institutional work.** The triage runs on whichever
   platform you put it in, under that platform's terms. If you are unsure which account that is,
   your campus accessibility coordinator or IT office will know.

## What you get at the end

One list in plain words, file by file and page by page: every finding with where it is, the
change to make, its WCAG criterion, who does it, and what counts as finished, plus the pages
that had nothing to list. Ask and it becomes a `triage.csv` to check off in Excel or Google
Sheets. Where the tool is connected, the deterministic fixes applied to a copy of each file,
with a record. Drafts of alt text for you to keep, edit, or mark decorative. The list of every
WCAG criterion the triage did not settle, so nothing reads as passed. And the one sentence your
campus can honestly say about the files afterwards, which is narrower than "compliant" and stays
true.

---

*Developed for the CIC AI Ready network. Adapt freely for your own campus. Criterion text in
`criteria.md` and `rules/wcag21.json` is quoted from WCAG 2.1, Copyright © W3C, under the W3C
Document License.*
