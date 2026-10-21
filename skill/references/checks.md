# What is checked, what is fixed, what is not

**One file or a pile.** `scan_document` reads one file. `scan_folder` reads every supported file
under a folder and adds the thing one file cannot show: a check that recurs across three or more
files, and at least half of them, is a **Route 5** candidate with a proposal to fix it once at the
template or the export setting. Faculty rarely have one file. Start with the folder.

Three file types. For each: what a machine can see, which of those the tool repairs on its own,
which it drafts for a person, and what it does not evaluate at all. The `not evaluated` list is
read out every time; it is the part people skip and the part that keeps the claim honest.

The tables and the *Not evaluated* paragraphs are generated from `rules/checks.json` and
`rules/coverage.json` by `tools/build_skill.py`. Edit those files, not the blocks below.
`criteria.md` has every WCAG 2.1 A and AA criterion with W3C's own words and what each format
still needs.

## Word (.docx)

<!-- generated:docx -->
| Check | Criterion | Route | Fix |
| :--- | :--- | :-: | :--- |
| Document title property empty | 2.4.2 | 1 | `set-title` — uses the first Heading 1, else the file name made readable |
| No default document language | 3.1.1 | 1 | `set-language` — only with the language the owner names (`en-US`, `es-ES`); the tool never guesses one |
| Image with no alt text, or alt text that is a filename or an auto-generated phrase | 1.1.1 | 2 | Draft one sentence, or offer "decorative". Author confirms |
| Bold short line used as a heading | 1.3.1 | 2 | `apply-heading:<paragraph>:<level>` — the tool proposes level 2; the author confirms both that it is a heading and the level, and the id is passed with the level they named |
| No heading styles in a long document | 2.4.6 | 2 | Author marks the section titles; no tool fix |
| Heading level skipped (1 → 3) | 1.3.1 | 2 | Author chooses: fix the level or restructure; no tool fix |
| Empty heading (a Heading style with no text) | 2.4.6 | 2 | Author deletes it or gives it the section's title |
| Table with no header row marked | 1.3.1 | 2 | `mark-header-row:<table>` — only if the first row really holds column names |
| Link text that says nothing ("click here", a bare URL) | 2.4.4 | 2 | Author replaces it with the destination's name |

**Not evaluated in Word.** Checked only in part, a person judges the rest: 1.1.1, 1.3.1, 2.4.2, 2.4.4, 2.4.6, 3.1.1. Not checked at all: 1.3.2 Meaningful Sequence · 1.3.3 Sensory Characteristics · 1.4.1 Use of Color · 1.4.3 Contrast (Minimum) · 1.4.4 Resize Text · 1.4.5 Images of Text · 1.4.10 Reflow · 1.4.11 Non-text Contrast · 1.4.12 Text Spacing · 3.1.2 Language of Parts · 4.1.1 Parsing. Not checked, and applies only when the file has that kind of content (media, forms, animation, a set of files): 1.2.1, 1.2.2, 1.2.3, 1.2.4, 1.2.5, 1.3.4, 1.3.5, 1.4.2, 1.4.13, 2.1.1, 2.1.2, 2.1.4, 2.2.1, 2.2.2, 2.3.1, 2.4.1, 2.4.3, 2.4.5, 2.4.7, 2.5.1, 2.5.2, 2.5.3, 2.5.4, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 4.1.2, 4.1.3. What each one needs, and who judges it, is in `criteria.md`.
<!-- /generated:docx -->

## PowerPoint (.pptx)

<!-- generated:pptx -->
| Check | Criterion | Route | Fix |
| :--- | :--- | :-: | :--- |
| Presentation title property empty | 2.4.2 | 1 | `set-title` — uses the first slide title, else the file name |
| Slide without a title placeholder with text | 1.3.1 | 2 | Author gives each slide a unique title; it may be visually hidden but must exist |
| Picture with no alt text, or alt text that is a filename or an auto-generated phrase | 1.1.1 | 2 | Draft one sentence, or offer "decorative". Author confirms |
| Table with no header row marked | 1.3.1 | 2 | `mark-header-row:<slide>:<shape>` — only if the first row really holds column names |

**Not evaluated in PowerPoint.** Checked only in part, a person judges the rest: 1.1.1, 1.3.1, 2.4.2. Not checked at all: 1.3.2 Meaningful Sequence · 1.3.3 Sensory Characteristics · 1.4.1 Use of Color · 1.4.3 Contrast (Minimum) · 1.4.4 Resize Text · 1.4.5 Images of Text · 1.4.10 Reflow · 1.4.11 Non-text Contrast · 1.4.12 Text Spacing · 2.4.4 Link Purpose (In Context) · 2.4.6 Headings and Labels · 3.1.1 Language of Page · 3.1.2 Language of Parts · 4.1.1 Parsing. Not checked, and applies only when the file has that kind of content (media, forms, animation, a set of files): 1.2.1, 1.2.2, 1.2.3, 1.2.4, 1.2.5, 1.3.4, 1.3.5, 1.4.2, 1.4.13, 2.1.1, 2.1.2, 2.1.4, 2.2.1, 2.2.2, 2.3.1, 2.4.1, 2.4.3, 2.4.5, 2.4.7, 2.5.1, 2.5.2, 2.5.3, 2.5.4, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 4.1.2, 4.1.3. What each one needs, and who judges it, is in `criteria.md`.
<!-- /generated:pptx -->

Reading order is the defect that matters most in slides. Tell the author how to check it: open
the selection pane, read the list from the bottom up, and ask whether that is the order a listener
should hear.

## PDF

<!-- generated:pdf -->
| Check | Criterion | Route | Fix |
| :--- | :--- | :-: | :--- |
| Title metadata empty | 2.4.2 | 1 | `set-title` — from the file name, since the tool does not read a PDF's structure; glance at the result |
| No document language | 3.1.1 | 1 | `set-language` — only with the language the owner names |
| File is not tagged at all | 1.3.1 | 2 | **None in this tool.** Re-export from the source file after fixing it there. If there is no source, the file needs Acrobat's auto-tag followed by a human check |
| Pages are images with no text | 1.1.1 | 2 | Find the original, or OCR and then check the recognised text against the page |
| Pictures on a page of an untagged file | 1.1.1 | 2 | Tag the file first; then give each picture alt text, or mark it decorative |
| Fill-in fields with no name | 4.1.2 | 2 | Give each field a tooltip in the words printed beside it |

**Not evaluated in PDF.** Checked only in part, a person judges the rest: 1.1.1, 1.3.1, 2.4.2, 3.1.1, 4.1.2. Not checked at all: 1.3.2 Meaningful Sequence · 1.3.3 Sensory Characteristics · 1.4.1 Use of Color · 1.4.3 Contrast (Minimum) · 1.4.4 Resize Text · 1.4.5 Images of Text · 1.4.10 Reflow · 1.4.11 Non-text Contrast · 1.4.12 Text Spacing · 2.4.4 Link Purpose (In Context) · 2.4.6 Headings and Labels · 3.1.2 Language of Parts · 4.1.1 Parsing. Not checked, and applies only when the file has that kind of content (media, forms, animation, a set of files): 1.2.1, 1.2.2, 1.2.3, 1.2.4, 1.2.5, 1.3.4, 1.3.5, 1.4.2, 1.4.13, 2.1.1, 2.1.2, 2.1.4, 2.2.1, 2.2.2, 2.3.1, 2.4.1, 2.4.3, 2.4.5, 2.4.7, 2.5.1, 2.5.2, 2.5.3, 2.5.4, 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 4.1.3. What each one needs, and who judges it, is in `criteria.md`.
<!-- /generated:pdf -->

**The PDF passage. Say this, word for word or shorter, whenever an untagged PDF comes up:**
*A PDF is the end of the line, not the place to fix things. The fastest honest path is back to the
Word or PowerPoint file, fix it there, and export again. If that file is gone, the PDF needs a
person with Acrobat, and the tool will not pretend otherwise.* The tool's own `proposal` on the
finding says the same in fewer words; the passage above is the one you read aloud.

## The canonical honesty rule

When a criterion is not evaluated, the report says **not evaluated**. It never says pass. A check
that could not run is a gap in the evidence, and the gap is reported in the same breath as the
findings.
