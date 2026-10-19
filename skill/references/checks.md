# What is checked, what is fixed, what is not

**One file or a pile.** `scan_document` reads one file. `scan_folder` reads every supported file
under a folder and adds the thing one file cannot show: a check that recurs across three or more
files, and at least half of them, is a **Route 5** candidate with a proposal to fix it once at the
template or the export setting. Faculty rarely have one file. Start with the folder.

Three file types. For each: what a machine can see, which of those the tool repairs on its own,
which it drafts for a person, and what it does not evaluate at all. The `not evaluated` list is
read out every time; it is the part people skip and the part that keeps the claim honest.

## Word (.docx)

| Check | Criterion | Route | Fix |
| :--- | :--- | :-: | :--- |
| Document title property empty | 2.4.2 | 1 | `set-title` — uses the first Heading 1, else the file name made readable |
| No default document language | 3.1.1 | 1 | `set-language` — defaults to en-US; pass another code for other languages |
| Image with no alt text, or alt text that is a filename or an auto-generated phrase | 1.1.1 | 2 | Draft one sentence, or offer "decorative". Author confirms |
| Bold short line used as a heading | 1.3.1 | 2 | `apply-heading:<paragraph>:<level>` — only after the author says it is a heading |
| No heading styles in a long document | 2.4.6 | 2 | Author marks the section titles |
| Heading level skipped (1 → 3) | 1.3.1 | 2 | Author chooses: fix the level or restructure |
| Empty heading (a Heading style with no text) | 2.4.6 | 2 | Author deletes it or gives it the section's title |
| Table with no header row marked | 1.3.1 | 2 | `mark-header-row:<table>` — only if the first row really holds column names |
| Link text that says nothing ("click here", a bare URL) | 2.4.4 | 2 | Author replaces it with the destination's name |

**Not evaluated in Word:** the quality of alt text that exists · reading order of text boxes and
floating objects · colour and contrast · language changes inside the text · footnote and
comment accessibility.

## PowerPoint (.pptx)

| Check | Criterion | Route | Fix |
| :--- | :--- | :-: | :--- |
| Presentation title property empty | 2.4.2 | 1 | `set-title` — uses the first slide title, else the file name |
| Slide without a title placeholder with text | 1.3.1 | 2 | Author gives each slide a unique title; it may be visually hidden but must exist |
| Picture with no alt text, or alt text that is a filename or an auto-generated phrase | 1.1.1 | 2 | Draft one sentence, or offer "decorative". Author confirms |
| Table with no header row marked | 1.3.1 | 2 | `mark-header-row:<slide>:<shape>` — only if the first row really holds column names |

**Not evaluated in PowerPoint:** reading order (it follows the selection pane and only a person
can judge it) · contrast · captions on embedded audio and video · text inside images.

Reading order is the defect that matters most in slides. Tell the author how to check it: open
the selection pane, read the list from the bottom up, and ask whether that is the order a listener
should hear.

## PDF

| Check | Criterion | Route | Fix |
| :--- | :--- | :-: | :--- |
| Title metadata empty | 2.4.2 | 1 | `set-title` |
| No document language | 3.1.1 | 1 | `set-language` |
| File is not tagged at all | 1.3.1 | 2 | **None in this tool.** Re-export from the source file after fixing it there. If there is no source, the file needs Acrobat's auto-tag followed by a human check |
| Pages are images with no text | 1.1.1 | 2 | Find the original, or OCR and then check the recognised text against the page |

**Not evaluated in PDF:** alt text on figures · the order of the tag tree · headings, lists and
tables inside the tag tree · bookmarks · contrast · form fields.

**Say this about PDFs, in these words or tighter:** *A PDF is the end of the line, not the place
to fix things. The fastest honest path is back to the Word or PowerPoint file, fix it there, and
export again. If that file is gone, the PDF needs a person with Acrobat, and the tool will not
pretend otherwise.*

## The canonical honesty rule

When a criterion is not evaluated, the report says **not evaluated**. It never says pass. A check
that could not run is a gap in the evidence, and the gap is reported in the same breath as the
findings.
