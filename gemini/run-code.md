**If you can run code** (Gemini's Thinking models can), run this once on each PDF before you
write the list, with `PATH` set to the file. It reads the file and writes nothing. What it prints
is fact: whether the file is tagged, its title and language, the pages that draw pictures, the
fill-in fields with no name, and every link. State those as facts in the list and use its page
numbers for pictures and fields. Then still look at each page: the code counts pictures, it
cannot see them, so the descriptions and drafts come from looking. It does not count drawings
made of shapes, such as a logo or a cover graphic; look for those. For Word and PowerPoint files,
and if the code will not run, read every page as below, and say nothing about the code.

```python
# Reads one PDF's structure and prints it. Writes nothing.
from pypdf import PdfReader
from pypdf.generic import ContentStream

PATH = "the-file.pdf"
reader = PdfReader(PATH)
root = reader.trailer["/Root"]
mark = root.get("/MarkInfo")
print("tagged:", bool(mark and mark.get_object().get("/Marked")))
print("title:", (reader.metadata or {}).get("/Title"))
print("language:", root.get("/Lang"))


def pictures(owner, resources, seen):
    """Images a content stream draws, following form XObjects. A shared resource list
    names every picture on every page, so only what is drawn counts."""
    resources = resources.get_object() if resources is not None else None
    if owner is None or resources is None:
        return 0
    xobjects = resources.get("/XObject")
    xobjects = xobjects.get_object() if xobjects is not None else {}
    count = 0
    for operands, operator in ContentStream(owner, reader).operations:
        if operator != b"Do" or operands[0] not in xobjects:
            continue
        xobject = xobjects[operands[0]].get_object()
        if xobject.get("/Subtype") == "/Image":
            count += 1
        elif xobject.get("/Subtype") == "/Form" and id(xobject) not in seen:
            seen.add(id(xobject))
            count += pictures(xobject, xobject.get("/Resources") or resources, seen)
    return count


for number, page in enumerate(reader.pages, start=1):
    drawn = pictures(page.get_contents(), page.get("/Resources"), set())
    fields, unnamed, links = 0, [], []
    for ref in page.get("/Annots") or []:
        annotation = ref.get_object()
        if annotation.get("/Subtype") == "/Widget":
            fields += 1
            field, name, tooltip = annotation, None, None
            while field is not None:
                field = field.get_object()
                name, tooltip = name or field.get("/T"), tooltip or field.get("/TU")
                field = field.get("/Parent")
            if not tooltip:
                unnamed.append(str(name))
        elif annotation.get("/Subtype") == "/Link" and "/A" in annotation:
            uri = annotation["/A"].get_object().get("/URI")
            if uri:
                links.append(str(uri))
    print(f"page {number}: pictures {drawn}; fields {fields}, no name {unnamed}; links {links}")
```
