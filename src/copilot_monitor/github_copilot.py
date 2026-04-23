"""GitHub Copilot usage metrics fetcher."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubCopilotClient:
    """Client for the GitHub Copilot usage API."""

    def __init__(self, token: str) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = self._session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Organization-level endpoints
    # ------------------------------------------------------------------

    def get_org_usage(
        self,
        org: str,
        since: date | None = None,
        until: date | None = None,
        page: int = 1,
        per_page: int = 28,
    ) -> list[dict[str, Any]]:
        """Return daily Copilot usage metrics for an organization.

        Args:
            org: GitHub organization login.
            since: Start date (inclusive).  Defaults to 28 days ago.
            until: End date (inclusive).  Defaults to today.
            page: Page number for pagination.
            per_page: Results per page (max 28).
        """
        if since is None:
            since = date.today() - timedelta(days=27)
        if until is None:
            until = date.today()

        params: dict[str, Any] = {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "page": page,
            "per_page": per_page,
        }
        url = f"{GITHUB_API_BASE}/orgs/{org}/copilot/usage"
        logger.debug("Fetching org usage: %s", url)
        return self._get(url, params=params)  # type: ignore[return-value]

    def get_org_seat_info(self, org: str) -> dict[str, Any]:
        """Return Copilot seat assignment summary for an organization."""
        url = f"{GITHUB_API_BASE}/orgs/{org}/copilot/billing"
        logger.debug("Fetching org seat info: %s", url)
        return self._get(url)  # type: ignore[return-value]

    def get_org_assigned_seats(
        self,
        org: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """Return a paginated list of Copilot seat assignments."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        url = f"{GITHUB_API_BASE}/orgs/{org}/copilot/billing/seats"
        logger.debug("Fetching assigned seats: %s", url)
        return self._get(url, params=params)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Enterprise-level endpoints
    # ------------------------------------------------------------------

    def get_enterprise_usage(
        self,
        enterprise: str,
        since: date | None = None,
        until: date | None = None,
        page: int = 1,
        per_page: int = 28,
    ) -> list[dict[str, Any]]:
        """Return daily Copilot usage metrics for an enterprise."""
        if since is None:
            since = date.today() - timedelta(days=27)
        if until is None:
            until = date.today()

        params: dict[str, Any] = {
            "since": since.isoformat(),
            "until": until.isoformat(),
            "page": page,
            "per_page": per_page,
        }
        url = f"{GITHUB_API_BASE}/enterprises/{enterprise}/copilot/usage"
        logger.debug("Fetching enterprise usage: %s", url)
        return self._get(url, params=params)  # type: ignore[return-value]


def summarize_usage(daily_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate a list of daily usage records into summary statistics.

    Args:
        daily_records: List returned by ``get_org_usage`` /
            ``get_enterprise_usage``.

    Returns:
        Dictionary with aggregated totals and per-day data.
    """
    if not daily_records:
        return {
            "days": 0,
            "total_suggestions": 0,
            "total_acceptances": 0,
            "acceptance_rate": 0.0,
            "total_lines_suggested": 0,
            "total_lines_accepted": 0,
            "total_active_users": 0,
            "total_chat_turns": 0,
            "total_chat_acceptances": 0,
            "total_active_chat_users": 0,
            "daily": [],
        }

    totals: dict[str, int] = {
        "total_suggestions_count": 0,
        "total_acceptances_count": 0,
        "total_lines_suggested": 0,
        "total_lines_accepted": 0,
        "total_active_users": 0,
        "total_chat_turns": 0,
        "total_chat_acceptances": 0,
        "total_active_chat_users": 0,
    }

    for record in daily_records:
        for key in totals:
            totals[key] += record.get(key, 0)

    suggestions = totals["total_suggestions_count"]
    acceptances = totals["total_acceptances_count"]
    acceptance_rate = (acceptances / suggestions * 100) if suggestions else 0.0

    return {
        "days": len(daily_records),
        "total_suggestions": suggestions,
        "total_acceptances": acceptances,
        "acceptance_rate": round(acceptance_rate, 2),
        "total_lines_suggested": totals["total_lines_suggested"],
        "total_lines_accepted": totals["total_lines_accepted"],
        "total_active_users": totals["total_active_users"],
        "total_chat_turns": totals["total_chat_turns"],
        "total_chat_acceptances": totals["total_chat_acceptances"],
        "total_active_chat_users": totals["total_active_chat_users"],
        "daily": daily_records,
    }
