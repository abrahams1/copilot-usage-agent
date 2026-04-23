"""Tests for the GitHub Copilot usage module."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from copilot_monitor.github_copilot import GitHubCopilotClient, summarize_usage

DAILY_RECORD = {
    "day": "2024-01-15",
    "total_suggestions_count": 500,
    "total_acceptances_count": 400,
    "total_lines_suggested": 900,
    "total_lines_accepted": 600,
    "total_active_users": 10,
    "total_chat_turns": 50,
    "total_chat_acceptances": 20,
    "total_active_chat_users": 5,
}


# ---------------------------------------------------------------------------
# summarize_usage
# ---------------------------------------------------------------------------

class TestSummarizeUsage:
    def test_empty_list_returns_zeroes(self):
        result = summarize_usage([])
        assert result["days"] == 0
        assert result["total_suggestions"] == 0
        assert result["acceptance_rate"] == 0.0
        assert result["daily"] == []

    def test_single_record(self):
        result = summarize_usage([DAILY_RECORD])
        assert result["days"] == 1
        assert result["total_suggestions"] == 500
        assert result["total_acceptances"] == 400
        assert result["acceptance_rate"] == 80.0
        assert result["total_lines_suggested"] == 900
        assert result["total_lines_accepted"] == 600
        assert result["total_active_users"] == 10
        assert result["total_chat_turns"] == 50
        assert result["total_chat_acceptances"] == 20
        assert result["total_active_chat_users"] == 5

    def test_multiple_records_are_summed(self):
        records = [DAILY_RECORD, DAILY_RECORD]
        result = summarize_usage(records)
        assert result["days"] == 2
        assert result["total_suggestions"] == 1000
        assert result["total_acceptances"] == 800
        assert result["acceptance_rate"] == 80.0

    def test_zero_suggestions_gives_zero_acceptance_rate(self):
        record = {**DAILY_RECORD, "total_suggestions_count": 0, "total_acceptances_count": 0}
        result = summarize_usage([record])
        assert result["acceptance_rate"] == 0.0

    def test_daily_records_preserved(self):
        records = [DAILY_RECORD]
        result = summarize_usage(records)
        assert result["daily"] == records


# ---------------------------------------------------------------------------
# GitHubCopilotClient
# ---------------------------------------------------------------------------

class TestGitHubCopilotClient:
    def _make_client(self) -> GitHubCopilotClient:
        return GitHubCopilotClient(token="test-token")

    def test_session_auth_header_set(self):
        client = self._make_client()
        assert "Bearer test-token" in client._session.headers["Authorization"]

    def test_get_org_usage_calls_correct_url(self, requests_mock):
        client = self._make_client()
        url = "https://api.github.com/orgs/my-org/copilot/usage"
        requests_mock.get(url, json=[DAILY_RECORD])

        result = client.get_org_usage("my-org")

        assert result == [DAILY_RECORD]
        assert requests_mock.called

    def test_get_org_usage_passes_date_params(self, requests_mock):
        client = self._make_client()
        url = "https://api.github.com/orgs/my-org/copilot/usage"
        requests_mock.get(url, json=[DAILY_RECORD])

        client.get_org_usage(
            "my-org",
            since=date(2024, 1, 1),
            until=date(2024, 1, 28),
        )

        qs = requests_mock.last_request.qs
        assert qs["since"] == ["2024-01-01"]
        assert qs["until"] == ["2024-01-28"]

    def test_get_enterprise_usage_calls_correct_url(self, requests_mock):
        client = self._make_client()
        url = "https://api.github.com/enterprises/my-enterprise/copilot/usage"
        requests_mock.get(url, json=[DAILY_RECORD])

        result = client.get_enterprise_usage("my-enterprise")
        assert result == [DAILY_RECORD]

    def test_get_org_seat_info_calls_billing_url(self, requests_mock):
        client = self._make_client()
        url = "https://api.github.com/orgs/my-org/copilot/billing"
        requests_mock.get(url, json={"seat_breakdown": {}})

        result = client.get_org_seat_info("my-org")
        assert "seat_breakdown" in result

    def test_http_error_raises(self, requests_mock):
        client = self._make_client()
        url = "https://api.github.com/orgs/my-org/copilot/usage"
        requests_mock.get(url, status_code=403)

        with pytest.raises(Exception):
            client.get_org_usage("my-org")
