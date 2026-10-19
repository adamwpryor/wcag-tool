"""The server over the real protocol: in memory, and as a stdio subprocess."""

import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from wcag_tool.server import mcp

EXPECTED_TOOLS = {"scan_document", "fix_document", "scan_folder", "describe_routes"}


def _structured(result) -> dict:  # type: ignore[no-untyped-def]
    if getattr(result, "structured_content", None):
        return result.structured_content
    return json.loads(result.content[0].text)


def test_tools_in_memory(bad_docx: Path) -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == EXPECTED_TOOLS
            result = await client.call_tool("scan_document", {"path": str(bad_docx)})
            assert not result.is_error
            data = _structured(result)
            assert data["asset"] == bad_docx.name
            assert "bounded_claim" in data
            routes = await client.call_tool("describe_routes", {})
            assert "Five routes" in routes.content[0].text

    asyncio.run(run())


def test_server_over_stdio_subprocess(bad_pdf: Path) -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "wcag_tool.server"])

    async def run() -> None:
        async with Client(params) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == EXPECTED_TOOLS
            result = await client.call_tool("fix_document", {"path": str(bad_pdf)})
            assert not result.is_error
            data = _structured(result)
            assert set(data["applied"]) == {"set-title", "set-language"}
            assert Path(data["output"]).exists()

    asyncio.run(run())
