"""Tests for report generation."""

from __future__ import annotations

import json

from copilot_monitor.report import (
    format_azure_cost_summary,
    format_azure_metrics_summary,
    format_copilot_summary,
    generate_csv_report,
    generate_json_report,
    generate_text_report,
)

COPILOT_SUMMARY = {
    "days": 7,
    "total_suggestions": 1000,
    "total_acceptances": 800,
    "acceptance_rate": 80.0,
    "total_lines_suggested": 2000,
    "total_lines_accepted": 1500,
    "total_active_users": 25,
    "total_chat_turns": 100,
    "total_chat_acceptances": 40,
    "total_active_chat_users": 8,
    "daily": [
        {
            "day": "2024-01-15",
            "total_suggestions_count": 1000,
            "total_acceptances_count": 800,
            "total_lines_suggested": 2000,
            "total_lines_accepted": 1500,
            "total_active_users": 25,
            "total_chat_turns": 100,
            "total_chat_acceptances": 40,
            "total_active_chat_users": 8,
        }
    ],
}

AZURE_COST_SUMMARY = {
    "total_cost": 18.25,
    "currency": "USD",
    "by_service": {
        "Azure OpenAI": 14.5,
        "Cognitive Services": 3.75,
    },
}

AZURE_METRICS = {
    "TokenTransaction": 3000.0,
    "GeneratedTokens": 500.0,
}


class TestFormatCopilotSummary:
    def test_contains_key_fields(self):
        result = format_copilot_summary(COPILOT_SUMMARY)
        assert "1,000" in result  # total suggestions
        assert "80.0%" in result
        assert "7 day" in result

    def test_empty_summary(self):
        result = format_copilot_summary({})
        assert "0" in result


class TestFormatAzureCostSummary:
    def test_contains_total_cost(self):
        result = format_azure_cost_summary(AZURE_COST_SUMMARY)
        assert "18.2500" in result
        assert "USD" in result

    def test_contains_service_breakdown(self):
        result = format_azure_cost_summary(AZURE_COST_SUMMARY)
        assert "Azure OpenAI" in result
        assert "Cognitive Services" in result


class TestFormatAzureMetricsSummary:
    def test_contains_metric_names(self):
        result = format_azure_metrics_summary(AZURE_METRICS)
        assert "TokenTransaction" in result
        assert "GeneratedTokens" in result

    def test_empty_metrics(self):
        result = format_azure_metrics_summary({})
        assert "No metrics data" in result

    def test_resource_name_in_title(self):
        result = format_azure_metrics_summary({}, resource_name="my-openai")
        assert "my-openai" in result


class TestGenerateTextReport:
    def test_full_report_contains_all_sections(self):
        result = generate_text_report(
            copilot_summary=COPILOT_SUMMARY,
            azure_cost_summary=AZURE_COST_SUMMARY,
            azure_metrics=AZURE_METRICS,
        )
        assert "COPILOT & AZURE AI USAGE MONITOR" in result
        assert "GitHub Copilot" in result
        assert "Azure AI Cost" in result
        assert "Azure OpenAI Metrics" in result

    def test_report_with_only_copilot(self):
        result = generate_text_report(copilot_summary=COPILOT_SUMMARY)
        assert "GitHub Copilot" in result
        assert "Azure AI Cost" not in result

    def test_report_with_no_data(self):
        result = generate_text_report()
        assert "COPILOT & AZURE AI USAGE MONITOR" in result


class TestGenerateJsonReport:
    def test_valid_json_output(self):
        result = generate_json_report(
            copilot_summary=COPILOT_SUMMARY,
            azure_cost_summary=AZURE_COST_SUMMARY,
        )
        data = json.loads(result)
        assert "generated_at" in data
        assert "copilot" in data
        assert "azure_cost" in data

    def test_only_included_sections_present(self):
        result = generate_json_report(copilot_summary=COPILOT_SUMMARY)
        data = json.loads(result)
        assert "copilot" in data
        assert "azure_cost" not in data


class TestGenerateCsvReport:
    def test_csv_has_header_and_row(self):
        result = generate_csv_report(COPILOT_SUMMARY["daily"])
        lines = result.strip().split("\n")
        assert lines[0].startswith("day,")
        assert "2024-01-15" in lines[1]

    def test_empty_list_returns_empty_string(self):
        result = generate_csv_report([])
        assert result == ""
