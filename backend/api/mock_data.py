"""Mock data for dashboard when USE_MOCK_DATA=true."""

from __future__ import annotations

from backend.api.models import (
    AppUsage,
    CopilotSummary,
    DashboardResponse,
    FoundrySummary,
    StudioSummary,
    SubscriptionRow,
)


def get_mock_dashboard() -> DashboardResponse:
    return DashboardResponse(
        copilot=CopilotSummary(
            total_enabled_users=1240,
            total_active_users=876,
            total_prompts_30d=34521,
            app_breakdown=[
                AppUsage(app_name="Teams", prompts=12430, active_users=654),
                AppUsage(app_name="Outlook", prompts=8910, active_users=502),
                AppUsage(app_name="Word", prompts=6340, active_users=389),
                AppUsage(app_name="Excel", prompts=4120, active_users=245),
                AppUsage(app_name="PowerPoint", prompts=2721, active_users=198),
            ],
            snapshot_date="2026-04-22",
        ),
        foundry=FoundrySummary(
            total_tokens=42_600_000,
            prompt_tokens=28_400_000,
            completion_tokens=14_200_000,
            total_cost_usd=8320.50,
            period="last_30d",
        ),
        studio=StudioSummary(
            total_messages=15230,
            billed_messages=12800,
            overage_messages=2800,
            agent_count=14,
            period="2026-04",
        ),
        subscriptions=[
            SubscriptionRow(
                subscription_id="aaaa-1111",
                subscription_name="Prod-AI",
                tokens=28_100_000,
                cost_usd=5480.00,
                ai_resource_count=4,
            ),
            SubscriptionRow(
                subscription_id="bbbb-2222",
                subscription_name="Dev-AI",
                tokens=10_500_000,
                cost_usd=2040.50,
                ai_resource_count=3,
            ),
            SubscriptionRow(
                subscription_id="cccc-3333",
                subscription_name="Sandbox",
                tokens=4_000_000,
                cost_usd=800.00,
                ai_resource_count=2,
            ),
        ],
    )
