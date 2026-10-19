# The bounded claim

What the campus may say about a file after this triage, and what it may not. The distinction is
load-bearing: a published claim wider than the evidence is a record that can be used against the
institution later.

## The claim, with the tool connected

This is the sentence the tool returns in every report as `bounded_claim`. Use it as it is.

> This file was checked for the criteria listed under `evaluated` only. Route 1 findings can be
> repaired by the tool and re-scanned; Route 2 findings carry proposals that a person who knows
> the content must confirm; criteria under `not_evaluated` were not checked at all. A clean
> report is not a conformance claim.

Each clause is tied to something that exists: `evaluated` and `not_evaluated` are lists in the
report; "can be repaired" is a capability, not a claim that it happened. If repairs did happen,
you may add one sentence of fact drawn from the record, and only this one:

> Route 1 repairs listed under `applied` were made to a copy and the copy was re-scanned; the
> record is at `<record path>`.

## The claim for a pile

> `<n>` files were triaged. Findings were routed; `<m>` are open with named owners. `<k>` checks
> recur across files and are assigned to a template or an export setting. The criteria under
> `not_evaluated` were not checked in any file. No file has been reviewed by a person using a
> screen reader.

Say "named owners" only when the owner column is filled. Say "repairs were applied to all of
them" only if `fix_document` ran on every file and `failed` was empty on each; otherwise name the
files it ran on.

## The claim with no tool connected

> These files were read as text against the triage checklist. Nothing was modified. The checks
> that need the file open in its application were not done and are listed as not evaluated. The
> findings are routed to named owners. A clean read is not a conformance claim.

## What "tighter" means

You may remove a clause that claims work was done. You may never remove the clause that says what
was not evaluated, or the sentence that says this is not a conformance claim.

## What may not be said

- *"This file is WCAG 2.1 AA compliant."*
- *"This course is accessible."*
- *"The scanner found no issues"* in any form, including *"the scanner now reports nothing"* and
  *"it passes every criterion we checked."* A report with no rows is still bounded by the
  not-evaluated list, and you say so in the same sentence.
- *"All documents have been remediated."*
- *"The remaining findings are minor."* The tool's `confidence` field is not severity.
- Any percentage or score, of the file or of the tool's own work.
- *"Ready," "clean," "done."*

## Why

Automated checks find roughly a third of the barrier types people actually hit, and different
tools disagree with each other about the same pages by very large factors. A score therefore
describes the scanner's boundary at least as much as the file. Legal settlements in this area have
required user testing far more often than automated evaluation, because the question that
decides a case is whether a person could complete a task, and no scan answers that.

So the defensible claim is bounded: *checked these criteria, fixed these, routed these, did not
check those.* The indefensible claim is the one everyone wants to make: *done.*

## The sentence that ends every session

> *This is a triage, not a conformance review. The files that matter most still need one person
> with a screen reader and a named task.*
