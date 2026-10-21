# About Document Accessibility Triage

*Why this toolkit exists, why it is designed the way it is, and how its pieces fit together. To
set it up, go back to the [README](README.md).*

Picture an associate professor of biology three weeks before the spring term. She is a composite,
not a real person, but there is nothing unusual in her folder. She has forty-one files in it:
syllabi for three sections, a decade of lecture decks, lab handouts, and a stack of PDFs, some
exported from Word last year and some scanned from a book chapter in 2014. An email from the
provost's office has told her, politely, that all of it needs to meet WCAG 2.1 AA, and she has
heard enough about the federal rule to know the date is real. What she wants, and what any of us
would want in her chair, is a button. Point a tool at the folder, let it find what is wrong, let it
fix what is wrong, and get back to the lab she has been meaning to revise for two years. When a
member campus of the Council of Independent Colleges asked for a tool that would detect and fix
accessibility problems in course content, written for a faculty member who will take the easiest
route available, that button is what they were asking for, and it is a completely reasonable thing
to ask for.

This toolkit is my answer, and it does not contain that button. The button would be easy to build,
and plenty of products sell one. The trouble is what the button says when it finishes. It says
*fixed*, and *fixed* tells the professor something nobody has checked. The cost of that sentence
lands later and on someone else: on a student with a screen reader in week two, when the lab
handout's table reads aloud as a stream of unlabeled numbers and the quiz PDF arrives with no
structure at all. So this tool does triage instead. It reads the pile, finds the defects a machine
can actually see, repairs the small number whose repair invents no meaning, drafts proposals for
the ones only the author can settle, and routes everything else to a named person along with the
evidence they will need before anyone may call it done. And then, in plain words, it lists
everything it did not check, because the list of what was not checked is the part of a report that
keeps everyone honest.

## What the triage does with one file

Routes and closure states are easier to follow with a single file in hand, so take one of the
professor's syllabi and walk it through. When the tool reads it, it finds eight problems. The
document has no title stored in its properties, so a screen reader announces the file name
instead. It declares no language, so the screen reader has to guess how to pronounce every word.
There is a photograph with no description. There is a line in bold, *Course Policies*, that looks
like a heading but is formatted as ordinary text, so a student jumping from heading to heading
skips right past it. There is an empty heading, a heading level that jumps from one straight to
three, a table of weekly readings whose top row is not marked as the row of column names, and a
link that says *click here*. None of these would stop a sighted reader for a second, and every one
of them costs a screen-reader user time, or meaning, or both.

Before reading on, sort those eight yourself into two piles: the ones a machine could fix on its
own without any risk, and the ones that need the professor. I suspect most of us would put more in
the first pile than belongs there, because most of them look trivial. A bold line that reads like
a heading is a heading, surely, and the top row of a reading schedule obviously holds the column
names.

Only two belong in the first pile, the title and the language, and the language only once the
professor has said what language the syllabus is written in. Every other fix asserts something
about what she meant. Turning *Course Policies* into a heading claims it starts a section, at a
particular level in the outline. Marking the table's top row claims those cells are labels rather
than data. Describing the photograph claims to know what it is there to teach, and the tool was
not in the room when she taught with it. All of those fixes are easy to make and none of them is
safe to make unasked, and that difference, between what a fix costs and what it claims, is the
whole idea behind the triage.

So instead of a score, the professor gets her eight problems back as a work list, one row per
problem. Three of the eight rows look like this:

| What was found | WCAG criterion | Route | Next step |
| :--- | :--- | :-: | :--- |
| The document title property is empty; screen readers announce the file name | 2.4.2 Page Titled | 1 | tool |
| The image has no alt text | 1.1.1 Non-text Content | 2 | ask author what it shows |
| Bold text that reads as a heading but is styled as body: *Course Policies* | 1.3.1 Info and Relationships | 2 | confirm, then apply |

The **route** column is the answer to the sorting exercise. Route 1 means the tool can repair the
problem itself and keep a record of the change. Route 2 means the person who made the file has to
decide, though the tool can draft a suggestion for her to accept, edit or reject. The **next step**
column says what that looks like in practice: *tool* (the tool does it), *confirm, then apply* (the
tool makes the change once she says yes to that specific fix), *ask author what it shows* (nothing
is drafted until she describes the image), or *author edits* (no tool fix exists, and she changes
it in Word). The full table has three more columns. One names the file, which matters once there
are forty of them. One is for the name of whoever will fix the problem, left blank on purpose,
because a task assigned to "the department" is a task nobody does. And one says what evidence
closes the row, which comes up below.

The tool only ever assigns Routes 1 and 2 to a single file, and the other three routes come from
looking wider. Route 3 is for problems no scanner can see at all, like whether a student using only
a keyboard can actually get through the online quiz; somebody has to sit down with a screen reader
and try a named task. Route 4 jumps the queue: if a student with an accommodation needs this
syllabus on Monday, every problem in it moves to the top of the list, whatever else is going on.
Routes 3 and 4 always come from a person, because only a person knows about the student and the
quiz. Route 5 comes from the tool reading a whole folder. When it finds the same problem in three
syllabi copied from one template, it says so, and fixing the template once retires the problem in
every section built from it, which is where most of the time in a remediation project comes back.

Last, every row says what it will take to close it, and there are only four acceptable answers:
the tool's own record of a repair it made and re-checked, the author's confirmation of a
suggestion, an expert's check with the file open in its own application, or a person using
assistive technology completing a named task. *The scanner no longer reports it* is deliberately
not one of the four, for reasons the next section makes plain. Picture the instructional designer
who opens the professor's table on a Monday morning, a little grudgingly, expecting a score and
finding a work queue instead. None of it is a verdict on the course. All of it is something a
specific person can do this week, which is the point. And at the bottom of every report sits the
one sentence the campus may honestly say about the files afterwards: *This file was checked for
the criteria listed under `evaluated` only. Route 1 findings can be repaired by the tool and
re-scanned; Route 2 findings carry proposals that a person who knows the content must confirm;
criteria under `not_evaluated` were not checked at all. A clean report is not a conformance
claim.*

## Why it will never call a file compliant

That last sentence is the one people push back on, and I understand why. A scanner that has just
read every file in the folder sounds like it ought to be able to say whether the folder passes. If
it can find forty missing alt texts, the reasoning goes, surely it can tell me when there are none
left, and surely *none left* is what the provost's email was asking for. The research on automated
accessibility testing says otherwise, and one study in particular makes the reason easy to feel,
because it lets you watch two scanners look at the same thing and come back with different worlds.

In 2022, Rita Ismailova and Yavuz Inal set out to learn how far the free online accessibility
checkers that campuses and governments rely on actually agree with one another. They took 41
government websites from different countries and ran each one through six evaluation tools,
counting the violations each tool reported against the WCAG guidelines
([Ismailova and Inal, 2022](https://doi.org/10.1109/ACCESS.2022.3179375)). The question underneath
was a practical one, the same one a provost asks when a vendor hands over a dashboard: whether
running a different checker would produce a different answer.

Try it yourself before reading the result. Two well-established checkers scan the same 41 sites,
looking only for Level A problems, the most basic tier of the standard. How far apart would you
expect their totals to be? If I'm honest, my own guess the first time would have been somewhere
between "about the same" and "maybe double," which is a sensible guess about two instruments
measuring the same thing.

One tool, Mauve, reported 14,927 Level A violations. Another, Examinator, reported 291. That is a
factor of roughly fifty, on the same pages, against the same tier of the same standard, and most of
Mauve's count fell under four criteria (non-text content, link purpose, page language, and name,
role, value). Neither tool was broken. Each one counted what it was built to see and was silent
about the rest, and the authors' own conclusion was that tools complement each other and that more
than one is needed for reliable data. Which means a single score tells you at least as much about
the scanner's boundary as it does about the site. Apply that to the professor's folder and the
problem with *compliant* becomes plain: whatever number a scanner hands her measures the scanner
first.

The boundary itself has been measured. A systematic mapping by Delvani Mateus and colleagues
gathered 38 studies (from an initial search of 304 articles) that had evaluated websites and mobile
apps with automated tools, with expert inspection, or by testing with users, and compared which
kinds of barriers each method turned up
([Mateus et al., 2021](https://doi.org/10.5753/jis.2021.1778)). On websites they documented 56
types of barrier. Automated tools detected 21 of those 56 types, a little over a third, and
fourteen types were found by both experts and users while no automated tool caught them at all. On
mobile apps the automated share was lower still. So even a perfect scan of the professor's folder
would be a perfect reading of about a third of what a student might run into.

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

The same plain speaking shapes what the tool will change without asking. It repairs exactly two
things by itself: the document title, and the document language once a person has said what the
language is. Both pass the four tests that every automatic repair here has to pass. The rule is
deterministic, the repair invents no meaning, it can be undone and scanned again, and it cannot
quietly change an assessment or a student's task. Everything else fails at least one of those
tests, usually the second. Marking a bold line as a heading asserts that the author meant it as the
start of a section, and at a particular level. Marking a table's first row as its header row
asserts that the row holds column names rather than data. Writing alt text asserts what an image is
for in this course, and the tool was not in the lecture. So the tool proposes each of those, labels
every draft as a draft, and applies one only when the person who owns the file names that specific
fix. A yes to the whole batch counts as a yes to nothing.

The language is the case that taught me the most. An earlier version wrote `en-US` into every file
by default, which seemed harmless until a review pass caught that it is a fact the tool made up,
and a wrong language setting makes a screen reader mispronounce every word in a Spanish course
reader. Now the language repair waits until someone names the language, and the report says it is
waiting. The original file is never written to either: every repair goes into a copy saved beside
it, with a record of what was found before, what was changed, and what is still open after.

PDFs get the shortest answer, and the tool gives it in the same words every time. *A PDF is the end
of the line, not the place to fix things. The fastest honest path is back to the Word or PowerPoint
file, fix it there, and export again. If that file is gone, the PDF needs a person with Acrobat,
and the tool will not pretend otherwise.* It will set a PDF's title and language, and it will tell
you whether the file is tagged at all, but it will not build a tag tree, because open-source tools
cannot build one well and a weak one implies a repaired file that is not there.

## One set of rules, three ways to run them

Faculty meet AI through whatever their campus provides, and that differs from one campus to the
next and sometimes from one department to the next. A toolkit that runs in only one of those places
works for almost nobody, and the professor with forty-one files will not switch platforms to use
it. So the same rules are rendered three ways, and each one can do a little more than the last,
depending on what the platform allows.

| | BoodleBox bot | Skill | MCP server |
| :--- | :--- | :--- | :--- |
| Install | Nothing; open the link | Upload one zip | About fifteen minutes, once |
| Reads your file | As text | As text, or the file itself where the assistant can run code | The file itself |
| Changes your file | Never | Never | The title automatically, the language once you name it, the rest only by named fix, always in a copy |
| Best for | Trying the triage on one file today | Faculty and staff in Claude, ChatGPT or Gemini | A whole folder, with a record of every change |

The difference that matters most is the second row. Read as plain text, a Word file hides most of
what a screen reader depends on: whether an image has alt text, whether a table's header row is
marked, what language the document declares, whether a line is a real heading or just bold. The
[bot](https://box.boodle.ai/a/@wcag-tool) cannot see any of that, which makes it the gentlest place
to start and the least complete: anyone with a BoodleBox account can open it and try a file in a
minute, and what it cannot check goes on a short list for the author to look at in the
file, never into the pile of things that passed. The skill is one
zip file that Claude, ChatGPT and Gemini all accept, and it can read the file itself wherever the
assistant is allowed to run code. The server reads the file directly and can repair a copy. The rules that must
never break (never certify, never invent meaning, route before you fix) sit in the instruction text
of every version, never only in an attached file, because an assistant searching its attachments
may not retrieve the one paragraph that tells it to refuse.

## Why the rules live in data files

Three versions of one triage only help if they say the same thing, and the first version of this
repository kept the rules the way most projects do, typed by hand into each place that needed them.
The scanner had its list, the reference page had its table, the template proposals had their own
map, and the bot would have had a fourth copy. Nothing checked that they agreed, and when I finally
compared them, one already disagreed with itself: the check for skipped heading levels reported its
findings under one WCAG criterion while the list of what the tool evaluates filed the same check
under another. It was a small error, and the kind that never announces itself. A report would have
looked complete and been quietly wrong about which criterion it had checked.

So the rules now live in three data files. One holds all 50 Level A and AA success criteria in
W3C's own words, extracted from the published standard by a script anyone can re-run. One holds
every check the scanner runs, with its criterion, its route, its closure state, its fix and its
wording. One holds, for every criterion in every file format, whether a check covers part of it,
what a person still has to judge, and who that person is. The tool refuses to start if the three
disagree, the reference pages and the bot's knowledge files are generated from them, and the build
fails if any page falls behind. One consequence I like a great deal: every report now names all 50
criteria, either as checked in part or as not checked, so nothing can read as passed simply because
it was left off the list.

I did consider a vector database here, a searchable index of the WCAG documents that an assistant
could query for context. It turned out to be the wrong tool for this particular job. Every finding
already knows its criterion number, so the explanation is a lookup by number rather than a search,
and a lookup returns the same text every time. A similarity search would occasionally hand back the
criterion next door (1.3.2 for a 1.3.1 finding), and nothing in the report would flag it. For a
triage whose whole value is that it says the same thing on Tuesday that it said on Monday, exact
beats clever.

Repeatability is the other half of trust, so the toolkit ships with its own tests, and they are
meant for the people receiving it as much as for whoever maintains the code. The scanner half is
exact: a self-test runs the checks against seven fictional course files and compares every finding
with a saved expected result. The conversation half cannot be exact, because a language model never
answers word for word the same way twice, so it is measured instead, with ten short scripted
conversations whose replies are scored for banned words, for any score or percentage, and for the
scripted first sentence when someone asks whether a file is compliant. That question has to pass
every single run, because a bot that says *compliant* once in three tries will eventually say it to
a dean.

## How the pieces fit together

Everything in the repository serves one of the three versions, and all three are built from the
same two sources: the rules as data, and the instructions as prose. Change either one and every
version changes with it.

```text
src/wcag_tool/rules/          THE RULES, as data
  wcag21.json                   the 50 A and AA criteria, in W3C's words
  checks.json                   every check: criterion, route, closure, fix, wording
  coverage.json                 what each format can and cannot be checked for, and who judges the rest

skill/                        THE INSTRUCTIONS, as prose
  SKILL.md                      how a triage session runs, and the rules that never break
  references/                   routes, checks, alt text, the bounded claim, all 50 criteria
  scripts/                      a read-only scanner, the self-test, the conversation grader
  tests/                        the expected results and the ten scripted conversations

bot/                          THE BOT
  instructions.md               its session flow (the never-break rules are copied in from SKILL.md)
  greeting.md                   the opening message people see before they type anything
  BOODLEBOX_BOT.md              how to assemble it in BoodleBox

src/wcag_tool/                THE MCP SERVER and command-line tool (reads the rules above)
tools/build_skill.py          builds the downloads below from all of the above

GitHub Releases page          WHAT PEOPLE DOWNLOAD, built automatically for each version
  wcag-triage-skill.zip         the skill folder, with scripts and tests
  wcag-triage-bot.zip           the bot's instructions, greeting, knowledge files and practice course files
```

Nobody downloads anything from the repository's folders. Each time a new version is tagged, a
GitHub workflow runs the tests, builds the two zips from the sources and attaches them to that
version's release, so the files people download always match the code and the rules of the
version they chose.

Putting it in front of a campus follows the same order the versions climb. Start with the bot, so
people can try the triage on one file with nothing to install and see what a routed work list
looks like. Offer the skill to the faculty and staff who already work in Claude, ChatGPT or Gemini,
so the triage lives in the assistant they open every day and, where that assistant can run code,
reads their files properly. Set up the MCP server for the people who own a whole course folder or a
template, because that is where the record of every change, and Route 5, earn their keep. Before
sharing any of the three, run its tests: the scripted conversations for the bot and the skill, and
the self-test for anything that reads files. Step-by-step instructions for each are in the
[README](README.md).

## Where this came from

I built this as part of my work with the Council of Independent Colleges' AI Ready program, after
a member campus asked for a tool faculty could point at their course files. The request came with
a date attached. The Department of Justice's rule under Title II of the Americans with Disabilities
Act names WCAG 2.1 AA as the standard for the websites, apps and online course content of public
colleges and universities, and an interim final rule this April moved its compliance dates to April
26, 2027 for public entities serving 50,000 people or more and April 26, 2028 for smaller ones and
special districts
([Federal Register, April 20, 2026](https://www.federalregister.gov/documents/2026/04/20/2026-07663/extension-of-compliance-dates-for-nondiscrimination-on-the-basis-of-disability-accessibility-of-web)).
Most CIC members are private colleges, which that rule does not bind directly, and the request came
from one of them anyway, because a federal rule with a named standard and a named date gets heard
well beyond the institutions it covers. None of this is legal advice; what applies to your campus
is a question for your accessibility coordinator or your counsel.

The toolkit is MIT licensed, so take it, adapt it to your campus, and make it better. The reasoning
behind each design choice is recorded in [docs/DECISIONS.md](docs/DECISIONS.md). Criterion text in
the reference pages and rules files is quoted from [WCAG 2.1](https://www.w3.org/TR/WCAG21/),
Copyright © W3C, under the
[W3C Document License](https://www.w3.org/copyright/document-license-2023/).
