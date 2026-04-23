"""LangGraph agent wired to MCP tool servers."""

from __future__ import annotations

import asyncio
import shlex
from functools import lru_cache

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

from backend.agent.prompts import SYSTEM_PROMPT
from backend.config import settings

_agent = None
_lock = asyncio.Lock()


def _build_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
        temperature=0,
        streaming=True,
    )


def _mcp_server_configs() -> dict:
    return {
        "workiq": {
            "command": shlex.split(settings.workiq_mcp_cmd)[0],
            "args": shlex.split(settings.workiq_mcp_cmd)[1:],
            "transport": "stdio",
        },
        "foundryiq": {
            "command": shlex.split(settings.foundryiq_mcp_cmd)[0],
            "args": shlex.split(settings.foundryiq_mcp_cmd)[1:],
            "transport": "stdio",
        },
        "copilot_studio": {
            "command": shlex.split(settings.copilot_studio_mcp_cmd)[0],
            "args": shlex.split(settings.copilot_studio_mcp_cmd)[1:],
            "transport": "stdio",
        },
    }


async def get_agent():
    global _agent
    if _agent is not None:
        return _agent

    async with _lock:
        if _agent is not None:
            return _agent

        mcp_client = MultiServerMCPClient(_mcp_server_configs())
        tools = await mcp_client.get_tools()
        llm = _build_llm()

        _agent = create_react_agent(
            model=llm,
            tools=tools,
            state_modifier=SYSTEM_PROMPT,
        )
        return _agent
