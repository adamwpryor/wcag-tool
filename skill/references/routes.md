# The five routes and the four closure states

A finding is never a score. It is a defect with a route, an owner and a closure state. The route
is decided by what the fix needs, not by how easy the fix is.

## Routes

| Route | Name | Send a finding here when | Who acts |
| :-: | :--- | :--- | :--- |
| **1** | Deterministic defect → automatic repair | The rule is deterministic, the repair invents no meaning, it is reversible, it can be re-scanned, and it cannot silently change an assessment or a student's task | The tool, with a before-and-after record |
| **2** | Machine finding → content-owner review | The tool can see that something is missing or wrong but cannot know what it should be: alt text, heading levels, table headers, link text | The person who made the file. The tool may draft; it may not close |
| **3** | Interaction defect → manual task testing | Keyboard, focus, reading order, screen-reader announcements, whether a student can complete a task | One person with assistive technology and a named task |
| **4** | High-impact or time-sensitive → expedited review | A currently enrolled student needs it, it is a graded task, it is accommodation or safety information, or a deadline is inside two weeks | Whoever can act today. Overrides every other route |
| **5** | Recurring systemic defect → template or source | The same finding appears across many files | Whoever owns the template, the export settings, or the vendor |

**Route 4 is an override, not a severity label.** A missing title on a quiz a student needs this
week is Route 4, however trivial the fix.

**Route 5 is where the time goes back.** One corrected syllabus template retires the same finding
in every section that used it. Count the repeats and name the template before anyone fixes an
instance.

## Closure states

A finding may be closed only with one of these four, and the state is written down next to it.

| State | Means | Enough for |
| :--- | :--- | :--- |
| `automatically_verified` | The tool applied a Route 1 repair, the re-scan no longer reports it, the record exists, and a person has opened the record and written the closure down | Route 1 only |
| `content_owner_verified` | The person who made the file confirmed or edited the proposal | Route 2 |
| `expert_verified` | Someone who does accessibility work checked it, with the file open in its application or a screen reader | Untagged PDFs, scanned files, anything structural |
| `user_task_verified` | A person using assistive technology completed a named task with the file | Route 3, and the files that matter most |

**"No longer reported by the scanner" is not a closure state.** Two tools disagree with each other
by a factor of fifty on the same pages. A finding disappearing from one report proves what the
report measures, not what a student experiences.

**An untagged PDF** is routed 2 because the person who made the file acts (re-export from the
source), but it closes as `expert_verified`, because only someone with Acrobat and a screen
reader can say the tags are right. The route says who moves; the closure says who may call it
done. They are allowed to differ.

## What the tool does with routes

- `scan_document` and `scan_folder` assign Route 1, 2 or 5 to every finding. They never emit
  Route 3 or Route 4: a person overwrites the route for the file a student needs, and adds the
  Route 3 rows for the files that matter most.
- `fix_document` applies Route 1 repairs by default (the language only once a person names it)
  and a Route 2 repair only when its `fix_id` is named, which a person does after confirming the
  proposal. An id that matches no finding is returned in `unknown_fix_ids` and not applied.
- Nothing in the tool closes anything. Closure is a human act, recorded by a human.
