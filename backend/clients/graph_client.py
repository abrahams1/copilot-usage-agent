"""Microsoft Graph client for M365 Copilot usage reports."""

from __future__ import annotations

import httpx
from azure.identity import ClientSecretCredential

from backend.config import settings

GRAPH_BASE = "https://graph.microsoft.com/beta"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def _get_credential() -> ClientSecretCredential:
    return ClientSecretCredential(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )


def _get_token() -> str:
    cred = _get_credential()
    token = cred.get_token(GRAPH_SCOPE)
    return token.token


async def graph_get(path: str, params: dict | None = None) -> dict:
    token = _get_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


async def get_copilot_usage_report(period: str = "D30") -> dict:
    return await graph_get(
        "/reports/getMicrosoft365CopilotUsageReport",
        {"period": period},
    )


async def get_copilot_user_detail(period: str = "D30") -> dict:
    return await graph_get(
        "/reports/getMicrosoft365CopilotUserDetail",
        {"period": period},
    )
