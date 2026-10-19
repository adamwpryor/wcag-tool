"""Alt text that is present but says nothing.

Office and the libraries that write its files often fill the alt text slot with
the image's filename or a machine-generated phrase. A screen reader then reads
"IMG_4521.jpg" or "A picture containing text" aloud. Both count as missing.
"""

from __future__ import annotations

import re

_FILENAME = re.compile(r"^[\w\- ()]+\.(png|jpe?g|gif|bmp|tiff?|svg|emf|wmf|webp)$", re.IGNORECASE)
_AUTO_PHRASES = (
    "a picture containing",
    "a close up of",
    "a close-up of",
    "a screenshot of",
    "diagram description automatically generated",
    "description automatically generated",
    "image",
    "picture",
    "photo",
    "graphic",
)


def is_missing_or_placeholder(descr: str | None) -> bool:
    """Return True when alt text is absent, a filename, or an auto-generated phrase.

    Args:
        descr: The alt text found on the image, or None.

    Returns:
        True if a person still needs to write the alt text.
    """
    text = (descr or "").strip()
    if not text:
        return True
    lowered = text.lower()
    if _FILENAME.match(text):
        return True
    return any(
        lowered == phrase or lowered.startswith(phrase + " ") for phrase in _AUTO_PHRASES
    ) or ("automatically generated" in lowered)
