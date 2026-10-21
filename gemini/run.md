# Running the scanner

The scanner is the same code the wcag-tool's MCP server runs. It is carried here as Markdown
because this platform runs code you write, not files a skill carries. Each other file in this
folder holds one block that saves one part of the scanner into your code sandbox; the block at the
end of this page checks those parts and scans.

1. In one code step, run the block from every file listed under *The parts*, exactly as written,
   then the block under *Scan*. Do not shorten, reformat or correct anything in them. The scan
   block compares each saved part with its fingerprint and refuses to run if any part differs.
2. Set `FILES` to the course files as your sandbox sees them. Left empty, it scans every Word,
   PowerPoint and PDF file under the working folder.
3. If your sandbox keeps files between steps, a later scan needs only the *Scan* block. If it
   names a part as missing, run that part again.

The scanner reads files and never writes to them. It fixes nothing.
