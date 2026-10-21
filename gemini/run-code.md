**If no tool is connected but you can run code** (Gemini with code execution), the scanner is in
`scanner/` as Markdown, because this platform runs code you write, not files a skill carries.
Follow `scanner/run.md`: in one code step, run the block from each file it lists, exactly as
written, then its last block with `FILES` set to the course files and `JSON = True`. Work from
the output exactly as you would from `scan_folder`: the same fields, each finding with its
`locator` and `evidence`. It never writes to a course file. If it stops and names a part that was
not copied exactly, run that part's block again, unchanged; if it stops a second time, say so and
continue by eye. Say in the first answer, once, that you can find and place problems here but
cannot change the files.
