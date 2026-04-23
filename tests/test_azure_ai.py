"""Tests for the Azure AI usage module."""

from __future__ import annotations

import pytest

from copilot_monitor.azure_ai import AzureAIClient, summarize_cost, summarize_metrics

COST_RESPONSE = {
    "properties": {
        "columns": [
            {"name": "Cost"},
            {"name": "Currency"},
            {"name": "ServiceName"},
        ],
        "rows": [
            [12.5, "USD", "Azure OpenAI"],
            [3.75, "USD", "Cognitive Services"],
            [2.0, "USD", "Azure OpenAI"],
        ],
    }
}

METRICS_RESPONSE = {
    "value": [
        {
            "name": {"value": "TokenTransaction"},
            "timeseries": [
                {
                    "data": [
                        {"total": 1000.0},
                        {"total": 2000.0},
                    ]
                }
            ],
        },
        {
            "name": {"value": "GeneratedTokens"},
            "timeseries": [
                {
                    "data": [
                        {"total": 500.0},
                    ]
                }
            ],
        },
    ]
}


# ---------------------------------------------------------------------------
# summarize_cost
# ---------------------------------------------------------------------------

class TestSummarizeCost:
    def test_totals_are_aggregated(self):
        result = summarize_cost(COST_RESPONSE)
        assert result["total_cost"] == pytest.approx(18.25)
        assert result["currency"] == "USD"

    def test_by_service_sums_per_service(self):
        result = summarize_cost(COST_RESPONSE)
        assert result["by_service"]["Azure OpenAI"] == pytest.approx(14.5)
        assert result["by_service"]["Cognitive Services"] == pytest.approx(3.75)

    def test_empty_rows_returns_zero(self):
        response = {"properties": {"columns": [], "rows": []}}
        result = summarize_cost(response)
        assert result["total_cost"] == 0.0
        assert result["by_service"] == {}

    def test_missing_properties_returns_zero(self):
        result = summarize_cost({})
        assert result["total_cost"] == 0.0


# ---------------------------------------------------------------------------
# summarize_metrics
# ---------------------------------------------------------------------------

class TestSummarizeMetrics:
    def test_totals_summed_across_timeseries(self):
        result = summarize_metrics(METRICS_RESPONSE)
        assert result["TokenTransaction"] == 3000.0
        assert result["GeneratedTokens"] == 500.0

    def test_empty_response_returns_empty_dict(self):
        result = summarize_metrics({})
        assert result == {}

    def test_no_timeseries_data_gives_zero(self):
        response = {
            "value": [
                {
                    "name": {"value": "TokenTransaction"},
                    "timeseries": [],
                }
            ]
        }
        result = summarize_metrics(response)
        assert result["TokenTransaction"] == 0.0


# ---------------------------------------------------------------------------
# AzureAIClient
# ---------------------------------------------------------------------------


class TestAzureAIClient:
    def _make_client(self) -> AzureAIClient:
        return AzureAIClient(
            subscription_id="sub-123",
            bearer_token="token-abc",
        )

    def test_session_auth_header_set(self):
        client = self._make_client()
        assert "Bearer token-abc" in client._session.headers["Authorization"]

    def test_get_cost_by_resource_posts_to_correct_url(self, requests_mock):
        client = self._make_client()
        url = (
            "https://management.azure.com/subscriptions/sub-123"
            "/providers/Microsoft.CostManagement/query"
        )
        requests_mock.post(url, json=COST_RESPONSE, status_code=200)

        result = client.get_cost_by_resource()

        assert result == COST_RESPONSE
        assert requests_mock.called

    def test_get_openai_resource_metrics_calls_correct_url(self, requests_mock):
        client = self._make_client()
        # Use a partial match for the URL prefix
        url_prefix = (
            "https://management.azure.com/subscriptions/sub-123"
            "/resourceGroups/my-rg"
            "/providers/Microsoft.CognitiveServices/accounts/my-openai"
            "/providers/Microsoft.Insights/metrics"
        )
        requests_mock.get(
            url_prefix,
            json=METRICS_RESPONSE,
            status_code=200,
        )

        result = client.get_openai_resource_metrics(
            resource_group="my-rg",
            resource_name="my-openai",
        )
        assert result == METRICS_RESPONSE

    def test_http_error_raises(self, requests_mock):
        client = self._make_client()
        url = (
            "https://management.azure.com/subscriptions/sub-123"
            "/providers/Microsoft.CostManagement/query"
        )
        requests_mock.post(url, status_code=403)

        with pytest.raises(Exception):
            client.get_cost_by_resource()
