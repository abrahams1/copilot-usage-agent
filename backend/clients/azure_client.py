"""Azure Monitor + ARM client for AI Foundry resource metrics."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from azure.identity import ClientSecretCredential

from backend.config import settings

ARM_BASE = "https://management.azure.com"
ARM_SCOPE = "https://management.azure.com/.default"
API_VERSION_MONITOR = "2024-02-01"
API_VERSION_RESOURCES = "2021-04-01"
API_VERSION_SUBSCRIPTIONS = "2022-12-01"
API_VERSION_COSTMGMT = "2023-11-01"


def _get_token() -> str:
    cred = ClientSecretCredential(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )
    return cred.get_token(ARM_SCOPE).token


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_get_token()}"}


async def list_subscriptions() -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ARM_BASE}/subscriptions",
            headers=_headers(),
            params={"api-version": API_VERSION_SUBSCRIPTIONS},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


async def list_ai_resources(subscription_id: str) -> list[dict]:
    resource_filter = "resourceType eq 'Microsoft.CognitiveServices/accounts'"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ARM_BASE}/subscriptions/{subscription_id}/resources",
            headers=_headers(),
            params={"api-version": API_VERSION_RESOURCES, "$filter": resource_filter},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("value", [])


async def get_metrics(
    resource_id: str,
    metric_names: str,
    timespan_days: int = 7,
) -> dict:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=timespan_days)
    timespan = f"{start.isoformat()}/{now.isoformat()}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ARM_BASE}{resource_id}/providers/microsoft.insights/metrics",
            headers=_headers(),
            params={
                "api-version": API_VERSION_MONITOR,
                "metricnames": metric_names,
                "timespan": timespan,
                "interval": "P1D",
                "aggregation": "Total",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


async def get_subscription_cost(subscription_id: str, period_days: int = 30) -> dict:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=period_days)
    body = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {
            "from": start.strftime("%Y-%m-%dT00:00:00Z"),
            "to": now.strftime("%Y-%m-%dT23:59:59Z"),
        },
        "dataset": {
            "granularity": "None",
            "aggregation": {
                "totalCost": {"name": "Cost", "function": "Sum"},
            },
            "filter": {
                "dimensions": {
                    "name": "ServiceName",
                    "operator": "In",
                    "values": [
                        "Azure OpenAI Service",
                        "Azure AI Services",
                        "Azure Machine Learning",
                    ],
                }
            },
        },
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ARM_BASE}/subscriptions/{subscription_id}"
            f"/providers/Microsoft.CostManagement/query"
            f"?api-version={API_VERSION_COSTMGMT}",
            headers=_headers(),
            json=body,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
