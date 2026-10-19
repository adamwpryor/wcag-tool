"""wcag-tool: find, fix, and route accessibility defects in course documents."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("wcag-tool")
except PackageNotFoundError:  # running from a checkout without an install
    __version__ = "0.0.0+local"

__all__ = ["__version__"]
