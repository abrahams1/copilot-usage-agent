"""Report generation for Copilot and Azure AI usage data."""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_SEPARATOR = "-" * 60


def _section(title: str) -> str:
    return f"\n{_SEPARATOR}\n  {title}\n{_SEPARATOR}"


def format_copilot_summary(summary: dict[str, Any]) -> str:
    """Return a human-readable Copilot usage summary string."""
    lines = [_section("GitHub Copilot Usage Summary")]
    lines.append(f"  Period:              {summary.get('days', 0)} day(s)")
    lines.append(f"  Total Suggestions:   {summary.get('total_suggestions', 0):,}")
    lines.append(f"  Total Acceptances:   {summary.get('total_acceptances', 0):,}")
    lines.append(f"  Acceptance Rate:     {summary.get('acceptance_rate', 0.0):.1f}%")
    lines.append(f"  Lines Suggested:     {summary.get('total_lines_suggested', 0):,}")
    lines.append(f"  Lines Accepted:      {summary.get('total_lines_accepted', 0):,}")
    lines.append(f"  Active Users (sum):  {summary.get('total_active_users', 0):,}")
    lines.append(f"  Chat Turns:          {summary.get('total_chat_turns', 0):,}")
    lines.append(f"  Chat Acceptances:    {summary.get('total_chat_acceptances', 0):,}")
    lines.append(
        f"  Active Chat Users:   {summary.get('total_active_chat_users', 0):,}"
    )
    return "\n".join(lines)


def format_azure_cost_summary(cost_summary: dict[str, Any]) -> str:
    """Return a human-readable Azure AI cost summary string."""
    lines = [_section("Azure AI Cost Summary")]
    currency = cost_summary.get("currency", "USD")
    total = cost_summary.get("total_cost", 0.0)
    lines.append(f"  Total Cost:  {total:,.4f} {currency}")
    by_service = cost_summary.get("by_service", {})
    if by_service:
        lines.append("  By Service:")
        for service, cost in sorted(by_service.items(), key=lambda x: -x[1]):
            lines.append(f"    {service:<30} {cost:>12,.4f} {currency}")
    return "\n".join(lines)


def format_azure_metrics_summary(
    metrics: dict[str, float], resource_name: str = ""
) -> str:
    """Return a human-readable Azure Monitor metrics summary string."""
    title = f"Azure OpenAI Metrics{' — ' + resource_name if resource_name else ''}"
    lines = [_section(title)]
    if not metrics:
        lines.append("  No metrics data available.")
        return "\n".join(lines)
    for metric_name, value in sorted(metrics.items()):
        lines.append(f"  {metric_name:<30} {value:>15,.0f}")
    return "\n".join(lines)


def generate_text_report(
    copilot_summary: dict[str, Any] | None = None,
    azure_cost_summary: dict[str, Any] | None = None,
    azure_metrics: dict[str, float] | None = None,
    resource_name: str = "",
) -> str:
    """Assemble a full text report from available data sections."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    header = [
        "=" * 60,
        "  COPILOT & AZURE AI USAGE MONITOR",
        f"  Generated: {timestamp}",
        "=" * 60,
    ]
    sections = ["\n".join(header)]

    if copilot_summary is not None:
        sections.append(format_copilot_summary(copilot_summary))

    if azure_cost_summary is not None:
        sections.append(format_azure_cost_summary(azure_cost_summary))

    if azure_metrics is not None:
        sections.append(
            format_azure_metrics_summary(azure_metrics, resource_name=resource_name)
        )

    sections.append(_SEPARATOR)
    return "\n".join(sections) + "\n"


def generate_json_report(
    copilot_summary: dict[str, Any] | None = None,
    azure_cost_summary: dict[str, Any] | None = None,
    azure_metrics: dict[str, float] | None = None,
) -> str:
    """Return a JSON-formatted report combining all available data."""
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if copilot_summary is not None:
        payload["copilot"] = copilot_summary
    if azure_cost_summary is not None:
        payload["azure_cost"] = azure_cost_summary
    if azure_metrics is not None:
        payload["azure_metrics"] = azure_metrics
    return json.dumps(payload, indent=2)


def generate_csv_report(daily_records: list[dict[str, Any]]) -> str:
    """Return a CSV string of daily Copilot usage records."""
    if not daily_records:
        return ""

    fieldnames = [
        "day",
        "total_suggestions_count",
        "total_acceptances_count",
        "total_lines_suggested",
        "total_lines_accepted",
        "total_active_users",
        "total_chat_turns",
        "total_chat_acceptances",
        "total_active_chat_users",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    for record in daily_records:
        writer.writerow(record)

    return output.getvalue()
