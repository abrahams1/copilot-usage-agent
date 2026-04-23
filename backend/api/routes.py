from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.agent.graph import get_agent
from backend.api.models import ChatRequest, DashboardResponse
from backend.api.mock_data import get_mock_dashboard
from backend.config import settings

router = APIRouter(prefix="/api")


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard():
    if settings.use_mock_data:
        return get_mock_dashboard()

    agent = await get_agent()
    result = await agent.ainvoke(
        {"messages": [("user", "Give me the full dashboard summary.")]},
    )
    last = result["messages"][-1]
    return DashboardResponse.model_validate_json(last.content)


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    conversation_id = body.conversation_id or str(uuid.uuid4())
    agent = await get_agent()

    async def event_stream():
        async for event in agent.astream_events(
            {"messages": [("user", body.message)]},
            version="v2",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    payload = json.dumps({"content": chunk.content})
                    yield f"event: token\ndata: {payload}\n\n"
        done_payload = json.dumps({"conversation_id": conversation_id})
        yield f"event: done\ndata: {done_payload}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def health():
    return {"status": "ok"}
