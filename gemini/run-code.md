**If no tool is connected but you can run code** (Gemini with code execution), the scanner is in
`scanner/` as Markdown, because this platform runs code you write, not files a skill carries.
Follow `scanner/run.md`: in one code step, run the block from each file it lists, exactly as
written, then its last block with `FILES` set to the course files. Work from the output exactly
as you would from `scan_folder`: it prints the same routed table, Route 5 lines and not-evaluated
paragraphs (`JSON = True` gives the data, with the same fields). It reads the file itself, so alt
text, header marks, the title, the language and heading styles are all visible to it. It never
writes to a course file. If it stops and names a part that was not copied exactly, run that part's
block again, unchanged; if it stops a second time, say so and continue by eye. Say in the first
answer, once, that this path finds and routes but fixes nothing: the Route 1 repairs need the
wcag-tool or the author.
