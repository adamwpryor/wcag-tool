# Check that this skill works before you rely on it

Two checks. The first is the scanner, which should give the same answer every time; it takes a
minute. The second is the conversation, which never gives exactly the same answer twice; it
takes about twenty minutes and is the one that catches the dangerous failure.

## 1. The scanner (needs Python)

From this folder:

```bash
python scripts/selftest.py
```

It scans the seven fictional files in `tests/fixtures/` and compares each result with
`tests/expected/`. You should see `8 of 8 match the expected results.` If a library is missing it
stops and prints the one install line you need.

In an assistant that runs code (claude.ai with code execution, Claude Code), upload this folder and
ask it to *"run scripts/selftest.py and show me the last line."*

Nothing in `tests/fixtures/` is a real course, a real person or a real institution.

## 2. The conversation (needs a chat window)

```bash
python scripts/grade.py --list
```

lists ten short cases. For each one:

1. Start a **fresh** conversation with the skill loaded.
2. Attach the fixture the case names, from `tests/fixtures/`.
3. Type each line under the case, one per turn.
4. Copy the assistant's **last** reply into a text file named after the case, such as
   `KAT-5.txt`. Run each case three times: `KAT-5.run1.txt`, `KAT-5.run2.txt`, `KAT-5.run3.txt`.

Then grade them all at once:

```bash
python scripts/grade.py replies/*.txt
```

Each reply gets `pass` or `FAIL` on the automatic checks and a short list of things for you to
tick by eye. The summary reports how many runs of each case passed.

**What good looks like.** Every run of KAT-5 (*"Is this file compliant now?"*) passes. That case
is the one that matters: a skill that says *compliant* once in three runs will say it to a dean.
For the rest, three of three is the target; two of three means a sentence in `SKILL.md` needs
work, and the failing reply shows which.

**Which cases apply.** `--list` shows `[skill, bot, mcp]` beside each case. KAT-9 and KAT-10 need
the wcag-tool MCP server connected; skip them otherwise.

## When you change something

- Changed a check or its wording: run `python scripts/selftest.py`. If the difference is the
  change you meant, `python scripts/selftest.py --update` records it as the new expected result.
- Changed `SKILL.md`: run the conversation cases again, KAT-5 first.
