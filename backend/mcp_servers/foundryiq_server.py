"""FoundryIQ MCP Server — Azure AI Foundry metrics via Azure Monitor + ARM."""

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

server = Server("foundryiq")


def _load_fixture() -> dict:
    return json.loads((FIXTURES_DIR / "foundryiq.json").read_text())


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_ai_resources",
            description="List Azure OpenAI and AI Services resources across subscriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "description": "Filter to one subscription. Omit for all.",
                    }
                },
            },
        ),
        Tool(
            name="get_foundry_token_usage",
            description="Get token usage (prompt + completion) for Azure AI resources in a subscription.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {"type": "string"},
                    "period": {
                        "type": "string",
                        "enum": ["last_7d", "last_30d", "last_90d"],
                        "description": "Time range. Default last_7d.",
                    },
                },
            },
        ),
        Tool(
            name="get_foundry_transactions",
            description="Get transaction units (standard calls, PTU processed) per subscription.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {"type": "string"},
                    "period": {"type": "string", "enum": ["last_7d", "last_30d", "last_90d"]},
                },
            },
        ),
        Tool(
            name="get_subscription_cost",
            description="Get Azure AI cost roll-up for a subscription (or all subscriptions).",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "description": "Omit for all subscriptions.",
                    },
                    "period_days": {
                        "type": "integer",
                        "description": "Lookback in days. Default 30.",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if USE_MOCK:
        fixture = _load_fixture()
        sub_id = arguments.get("subscription_id")

        if name == "list_ai_resources":
            resources = fixture["ai_resources"]
            if sub_id:
                resources = [r for r in resources if r["subscription_id"] == sub_id]
            data = resources

        elif name == "get_foundry_token_usage":
            usage = fixture["token_usage"]
            if sub_id:
                data = {sub_id: usage.get(sub_id, {})}
            else:
                data = usage

        elif name == "get_foundry_transactions":
            txns = fixture["transactions"]
            if sub_id:
                data = {sub_id: txns.get(sub_id, {})}
            else:
                data = txns

        elif name == "get_subscription_cost":
            costs = fixture["subscription_costs"]
            if sub_id:
                data = {sub_id: costs.get(sub_id, {})}
            else:
                data = costs

        else:
            data = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    # Live mode
    from backend.clients.azure_client import (
        get_metrics,
        get_subscription_cost,
        list_ai_resources,
        list_subscriptions,
    )

    period_map = {"last_7d": 7, "last_30d": 30, "last_90d": 90}
    sub_id = arguments.get("subscription_id")

    if name == "list_ai_resources":
        subs = [sub_id] if sub_id else [s["subscriptionId"] for s in await list_subscriptions()]
        all_resources = []
        for sid in subs:
            all_resources.extend(await list_ai_resources(sid))
        data = all_resources

    elif name == "get_foundry_token_usage":
        days = period_map.get(arguments.get("period", "last_7d"), 7)
        subs = [sub_id] if sub_id else [s["subscriptionId"] for s in await list_subscriptions()]
        data = {}
        for sid in subs:
            resources = await list_ai_resources(sid)
            total_prompt = total_completion = 0
            for r in resources:
                metrics = await get_metrics(
                    r["id"],
                    "ProcessedPromptTokens,GeneratedCompletionTokens",
                    days,
                )
                for m in metrics.get("value", []):
                    for ts in m.get("timeseries", []):
                        for d in ts.get("data", []):
                            val = d.get("total", 0) or 0
                            if "Prompt" in m["name"]["value"]:
                                total_prompt += val
                            else:
                                total_completion += val
            data[sid] = {
                "prompt_tokens": total_prompt,
                "completion_tokens": total_completion,
                "total_tokens": total_prompt + total_completion,
            }

    elif name == "get_foundry_transactions":
        days = period_map.get(arguments.get("period", "last_7d"), 7)
        subs = [sub_id] if sub_id else [s["subscriptionId"] for s in await list_subscriptions()]
        data = {}
        for sid in subs:
            resources = await list_ai_resources(sid)
            total_calls = 0
            for r in resources:
                metrics = await get_metrics(r["id"], "TokenTransaction", days)
                for m in metrics.get("value", []):
                    for ts in m.get("timeseries", []):
                        for d in ts.get("data", []):
                            total_calls += d.get("total", 0) or 0
            data[sid] = {"standard_calls": total_calls}

    elif name == "get_subscription_cost":
        days = arguments.get("period_days", 30)
        subs = [sub_id] if sub_id else [s["subscriptionId"] for s in await list_subscriptions()]
        data = {}
        for sid in subs:
            cost_resp = await get_subscription_cost(sid, days)
            rows = cost_resp.get("properties", {}).get("rows", [])
            total = sum(row[0] for row in rows) if rows else 0.0
            data[sid] = {"cost_usd": round(total, 2)}

    else:
        data = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(data, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
