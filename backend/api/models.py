from __future__ import annotations

from pydantic import BaseModel


class AppUsage(BaseModel):
    app_name: str
    prompts: int
    active_users: int


class CopilotSummary(BaseModel):
    total_enabled_users: int
    total_active_users: int
    total_prompts_30d: int
    app_breakdown: list[AppUsage]
    snapshot_date: str


class FoundrySummary(BaseModel):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost_usd: float
    period: str


class StudioSummary(BaseModel):
    total_messages: int
    billed_messages: int
    overage_messages: int
    agent_count: int
    period: str


class SubscriptionRow(BaseModel):
    subscription_id: str
    subscription_name: str
    tokens: int
    cost_usd: float
    ai_resource_count: int


class DashboardResponse(BaseModel):
    copilot: CopilotSummary
    foundry: FoundrySummary
    studio: StudioSummary
    subscriptions: list[SubscriptionRow]


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ChatChunk(BaseModel):
    content: str


class ChatDone(BaseModel):
    conversation_id: str
