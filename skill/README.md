# Document accessibility triage — the rules, as files you can take anywhere

These files are the rules behind the document accessibility triage, written so that you can run
the same triage in whichever AI assistant your campus already uses. Nothing here certifies
anything; it is a structured way of turning a pile of course files into a work queue where every
problem has an owner and the evidence it needs before it can be called done.

## What is in the set

| File | What it is |
| :--- | :--- |
| `wcag-triage.md` | **Everything in one file.** The instructions and all four reference pages, joined. Paste it into a chat, or attach it, and say *"triage these files."* |
| `wcag-triage-skill.zip` | The same material as a skill folder: `SKILL.md` plus a `references/` folder with the four pages. For assistants and platforms that take a skill or project folder rather than a pasted file. |
| `README.md` | This page. |

## How to use it

**In a chat assistant** — Claude, ChatGPT, Gemini, or whichever you have. Start a new conversation,
attach `wcag-triage.md` or paste its contents, and type: *"Triage these files."* It will ask you
three questions, one at a time, then route what it can see and end with a report.

**With the wcag-tool connected.** If your assistant takes MCP servers, install `wcag-tool` and
the same instructions will run the scans and the deterministic repairs for you, on your own
machine. Your files never leave it. See the repository README for the three-line setup.

**In a platform that takes a skill or project folder.** Unzip `wcag-triage-skill.zip`. Use
`SKILL.md` as the instructions and add the four files in `references/` as the knowledge the
assistant can read.

**With colleagues.** Send them the one file. Nothing in it is specific to you or your campus.

## Two rules while you use it

1. **Describe the course, never the students.** The triage needs to know what a file is for; it
   never needs a student's name, accommodation letter, or grade. Do not paste those anywhere.
2. **Use an account you are allowed to use for institutional work.** The triage runs on whichever
   platform you put it in, under that platform's terms. If you are unsure which account that is,
   your campus accessibility coordinator or IT office will know.

## What you get at the end

A routed table: every finding with its criterion, its route, a named owner, and the closure state
it needs. The deterministic fixes applied to a copy of each file, with a record. Drafts of alt
text for you to keep, edit, or mark decorative. And the one sentence your campus can honestly say
about the files afterwards, which is narrower than "compliant" and stays true.

---

*Developed for the CIC AI Ready network. Adapt freely for your own campus.*
