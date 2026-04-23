"""Azure AI / Azure OpenAI usage metrics fetcher."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

AZURE_MANAGEMENT_API = "https://management.azure.com"
AZURE_OPENAI_API_VERSION = "2024-10-01"
COST_MGMT_API_VERSION = "2023-11-01"


class AzureAIClient:
    """Client for Azure AI and Azure OpenAI usage APIs.

    Supports two authentication modes:
    1. Bearer token (e.g. from ``azure.identity.DefaultAzureCredential``).
    2. Azure OpenAI API key for the OpenAI-level usage endpoint.
    """

    def __init__(
        self,
        subscription_id: str,
        bearer_token: str,
        openai_api_key: str | None = None,
    ) -> None:
        self._subscription_id = subscription_id
        self._openai_api_key = openai_api_key

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Azure Cost Management
    # ------------------------------------------------------------------

    def get_cost_by_resource(
        self,
        resource_group: str | None = None,
        since: date | None = None,
        until: date | None = None,
        granularity: str = "Daily",
    ) -> dict[str, Any]:
        """Return Azure cost data filtered to AI/Cognitive Services.

        Args:
            resource_group: Optionally scope to a specific resource group.
            since: Start date.  Defaults to the start of the current month.
            until: End date.  Defaults to today.
            granularity: ``'Daily'`` or ``'Monthly'``.
        """
        if since is None:
            today = date.today()
            since = today.replace(day=1)
        if until is None:
            until = date.today()

        if resource_group:
            scope = (
                f"/subscriptions/{self._subscription_id}"
                f"/resourceGroups/{resource_group}"
            )
        else:
            scope = f"/subscriptions/{self._subscription_id}"

        url = (
            f"{AZURE_MANAGEMENT_API}{scope}"
            f"/providers/Microsoft.CostManagement/query"
            f"?api-version={COST_MGMT_API_VERSION}"
        )

        body = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": since.isoformat(),
                "to": until.isoformat(),
            },
            "dataset": {
                "granularity": granularity,
                "aggregation": {
                    "totalCost": {"name": "Cost", "function": "Sum"},
                    "totalUsage": {"name": "UsageQuantity", "function": "Sum"},
                },
                "filter": {
                    "or": [
                        {
                            "dimensions": {
                                "name": "ServiceName",
                                "operator": "In",
                                "values": [
                                    "Cognitive Services",
                                    "Azure OpenAI",
                                    "Azure AI Services",
                                ],
                            }
                        }
                    ]
                },
                "grouping": [
                    {"type": "Dimension", "name": "ServiceName"},
                    {"type": "Dimension", "name": "ResourceId"},
                ],
            },
        }

        logger.debug("Fetching Azure cost data: %s", url)
        response = self._session.post(url, json=body, timeout=60)
        response.raise_for_status()
        return response.json()  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Azure OpenAI resource-level metrics (Azure Monitor)
    # ------------------------------------------------------------------

    def get_openai_resource_metrics(
        self,
        resource_group: str,
        resource_name: str,
        since: date | None = None,
        until: date | None = None,
        interval: str = "PT1H",
    ) -> dict[str, Any]:
        """Return Azure Monitor metrics for an Azure OpenAI resource.

        Fetches ``TokenTransaction``, ``ActiveTokens``, and ``GeneratedTokens``
        metrics.

        Args:
            resource_group: Azure resource group.
            resource_name: Azure OpenAI account name.
            since: Start datetime.  Defaults to 24 hours ago.
            until: End datetime.  Defaults to now.
            interval: ISO 8601 duration for aggregation window.
        """
        if since is None:
            since = date.today() - timedelta(days=1)
        if until is None:
            until = date.today()

        resource_id = (
            f"/subscriptions/{self._subscription_id}"
            f"/resourceGroups/{resource_group}"
            f"/providers/Microsoft.CognitiveServices/accounts/{resource_name}"
        )

        metric_names = "TokenTransaction,ActiveTokens,GeneratedTokens"
        url = (
            f"{AZURE_MANAGEMENT_API}{resource_id}"
            f"/providers/Microsoft.Insights/metrics"
            f"?api-version=2023-10-01"
            f"&metricnames={metric_names}"
            f"&timespan={since.isoformat()}/{until.isoformat()}"
            f"&interval={interval}"
            f"&aggregation=Total"
        )

        logger.debug("Fetching Azure Monitor metrics: %s", url)
        response = self._session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Azure OpenAI deployment-level usage (OpenAI API)
    # ------------------------------------------------------------------

    def get_openai_deployments(
        self, resource_group: str, resource_name: str
    ) -> list[dict[str, Any]]:
        """List Azure OpenAI deployments in a given resource."""
        resource_id = (
            f"/subscriptions/{self._subscription_id}"
            f"/resourceGroups/{resource_group}"
            f"/providers/Microsoft.CognitiveServices/accounts/{resource_name}"
        )
        url = (
            f"{AZURE_MANAGEMENT_API}{resource_id}"
            f"/deployments?api-version={AZURE_OPENAI_API_VERSION}"
        )
        logger.debug("Fetching OpenAI deployments: %s", url)
        response = self._session.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("value", [])  # type: ignore[return-value]


def summarize_cost(cost_response: dict[str, Any]) -> dict[str, Any]:
    """Extract and aggregate cost rows from an Azure Cost Management response.

    Args:
        cost_response: Raw response from ``get_cost_by_resource``.

    Returns:
        Dictionary with total cost, currency, and per-service breakdown.
    """
    properties = cost_response.get("properties", {})
    rows = properties.get("rows", [])
    columns = [c["name"] for c in properties.get("columns", [])]

    if not rows:
        return {"total_cost": 0.0, "currency": "USD", "by_service": {}}

    cost_idx = columns.index("Cost") if "Cost" in columns else None
    currency_idx = columns.index("Currency") if "Currency" in columns else None
    service_idx = columns.index("ServiceName") if "ServiceName" in columns else None

    by_service: dict[str, float] = {}
    currency = "USD"
    total_cost = 0.0

    for row in rows:
        cost_val = float(row[cost_idx]) if cost_idx is not None else 0.0
        if currency_idx is not None:
            currency = str(row[currency_idx])
        service = str(row[service_idx]) if service_idx is not None else "Unknown"
        by_service[service] = by_service.get(service, 0.0) + cost_val
        total_cost += cost_val

    return {
        "total_cost": round(total_cost, 4),
        "currency": currency,
        "by_service": {k: round(v, 4) for k, v in by_service.items()},
    }


def summarize_metrics(metrics_response: dict[str, Any]) -> dict[str, Any]:
    """Summarize Azure Monitor metric timeseries data.

    Args:
        metrics_response: Raw response from ``get_openai_resource_metrics``.

    Returns:
        Dictionary mapping metric name to its total value over the period.
    """
    result: dict[str, float] = {}
    for metric in metrics_response.get("value", []):
        name = metric.get("name", {}).get("value", "unknown")
        total = 0.0
        for ts in metric.get("timeseries", []):
            for point in ts.get("data", []):
                total += point.get("total", 0.0)
        result[name] = total
    return result
