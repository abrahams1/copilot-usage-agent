"""Copilot Studio MCP Server — Studio message usage and agent listing."""

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

server = Server("copilot_studio")


def _load_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "copilot_studio.json").read_text())


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_studio_message_usage",
            description="Get Copilot Studio message usage: total consumed, billed, overage, and agent count.",
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Month in YYYY-MM format, or 'current_month'. Default current_month.",
                    }
                },
            },
        ),
        Tool(
            name="get_studio_agents",
            description="List published Copilot Studio agents with last-active date and message count.",
            inputSchema={
                "type": "object",
                "properties": {
                    "environment": {
                        "type": "string",
                        "description": "Filter by environment name. Omit for all.",
                    },
                    "top": {"type": "integer", "description": "Max agents to return. Default 50."},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if USE_MOCK:
        fixture = _load_fixture()

        if name == "get_studio_message_usage":
            data = fixture["message_usage"]
        elif name == "get_studio_agents":
            agents = fixture["agents"]
            env = arguments.get("environment")
            if env:
                agents = [a for a in agents if a["environment"] == env]
            top = arguments.get("top", 50)
            data = agents[:top]
        else:
            data = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    # Live mode — Power Platform admin APIs
    # The Power Platform admin connector requires either:
    #   - Power Platform admin role + service principal
    #   - Or the PPAC REST API (https://api.powerplatform.com)
    # This is a stub; wire to your tenant's admin endpoints.
    from backend.clients.graph_client import graph_get

    if name == "get_studio_message_usage":
        # Placeholder: Graph does not yet expose Studio billing natively.
        # Replace with Power Platform admin API call.
        data = {
            "error": "Live Copilot Studio billing API not yet configured. Set USE_MOCK_DATA=true or implement Power Platform admin connector."
        }
    elif name == "get_studio_agents":
        data = {
            "error": "Live Copilot Studio agent listing not yet configured. Set USE_MOCK_DATA=true or implement Power Platform admin connector."
        }
    else:
        data = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(data, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
