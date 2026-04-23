"""WorkIQ MCP Server — M365 Copilot usage data via Microsoft Graph."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

FIXTURES_DIR = Path(__file__).parent / "fixtures"
USE_MOCK = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

server = Server("workiq")


def _load_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "workiq.json").read_text())


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_copilot_usage_summary",
            description="Get M365 Copilot usage summary: total enabled users, active users, prompts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["D7", "D30", "D90", "D180"],
                        "description": "Report period. Default D30.",
                    }
                },
            },
        ),
        Tool(
            name="get_copilot_user_detail",
            description="Get per-user Copilot activity: last activity date, per-app prompts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "enum": ["D7", "D30", "D90", "D180"]},
                    "top": {"type": "integer", "description": "Max users to return. Default 50."},
                },
            },
        ),
        Tool(
            name="get_copilot_app_usage",
            description="Get Copilot prompt counts broken down by M365 app (Teams, Outlook, Word, Excel, PowerPoint).",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {"type": "string", "enum": ["D7", "D30", "D90", "D180"]},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if USE_MOCK:
        fixture = _load_fixture()
        if name == "get_copilot_usage_summary":
            data = fixture["copilot_usage_summary"]
        elif name == "get_copilot_user_detail":
            top = arguments.get("top", 50)
            data = fixture["copilot_user_detail"][:top]
        elif name == "get_copilot_app_usage":
            data = fixture["copilot_app_usage"]
        else:
            data = {"error": f"Unknown tool: {name}"}
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    # Live mode — call Microsoft Graph
    from backend.clients.graph_client import (
        get_copilot_usage_report,
        get_copilot_user_detail,
    )

    period = arguments.get("period", "D30")

    if name == "get_copilot_usage_summary":
        data = await get_copilot_usage_report(period)
    elif name == "get_copilot_user_detail":
        data = await get_copilot_user_detail(period)
    elif name == "get_copilot_app_usage":
        data = await get_copilot_usage_report(period)
    else:
        data = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(data, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
