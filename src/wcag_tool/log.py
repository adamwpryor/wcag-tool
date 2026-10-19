"""JSON structured logging to stderr.

Stdout is the MCP wire when the server runs over stdio, so every log record goes
to stderr. Each record carries the package version so a report can be matched to
the code that produced it.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from wcag_tool import __version__


class JsonFormatter(logging.Formatter):
    """Render each log record as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a record as a JSON line.

        Args:
            record: The log record to format.

        Returns:
            A single-line JSON string.
        """
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "version": __version__,
        }
        extra = getattr(record, "data", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger, writing to stderr.

    Args:
        level: Root logging level.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
