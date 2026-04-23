"""Tests for the main CLI entry point."""

from __future__ import annotations

import json
import sys
from unittest.mock import patch, MagicMock

import pytest

from main import parse_args, run


class TestParseArgs:
    def test_defaults(self):
        with patch.dict("os.environ", {}, clear=False):
            args = parse_args([])
        assert args.format == "text"
        assert args.output is None

    def test_format_json(self):
        args = parse_args(["--format", "json"])
        assert args.format == "json"

    def test_format_csv(self):
        args = parse_args(["--format", "csv"])
        assert args.format == "csv"

    def test_github_token_from_env(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "tok-env"}):
            args = parse_args([])
        assert args.github_token == "tok-env"

    def test_org_from_env(self):
        with patch.dict("os.environ", {"GITHUB_ORG": "my-org"}):
            args = parse_args([])
        assert args.org == "my-org"

    def test_azure_token_from_env(self):
        with patch.dict("os.environ", {"AZURE_BEARER_TOKEN": "az-tok"}):
            args = parse_args([])
        assert args.azure_token == "az-tok"


class TestRun:
    def _mock_copilot_summary(self):
        return {
            "days": 1,
            "total_suggestions": 100,
            "total_acceptances": 80,
            "acceptance_rate": 80.0,
            "total_lines_suggested": 200,
            "total_lines_accepted": 150,
            "total_active_users": 5,
            "total_chat_turns": 10,
            "total_chat_acceptances": 4,
            "total_active_chat_users": 2,
            "daily": [],
        }

    def test_returns_1_when_no_credentials(self, capsys):
        result = run([])
        assert result == 1

    def test_copilot_text_report_to_stdout(self, capsys):
        with (
            patch("main.GitHubCopilotClient") as mock_client_cls,
            patch("main.summarize_usage", return_value=self._mock_copilot_summary()),
        ):
            mock_client = MagicMock()
            mock_client.get_org_usage.return_value = []
            mock_client_cls.return_value = mock_client

            result = run(["--github-token", "tok", "--org", "my-org"])

        captured = capsys.readouterr()
        assert result == 0
        assert "COPILOT & AZURE AI USAGE MONITOR" in captured.out

    def test_copilot_json_report(self, capsys):
        with (
            patch("main.GitHubCopilotClient") as mock_client_cls,
            patch("main.summarize_usage", return_value=self._mock_copilot_summary()),
        ):
            mock_client = MagicMock()
            mock_client.get_org_usage.return_value = []
            mock_client_cls.return_value = mock_client

            result = run(
                ["--github-token", "tok", "--org", "my-org", "--format", "json"]
            )

        captured = capsys.readouterr()
        assert result == 0
        data = json.loads(captured.out)
        assert "copilot" in data

    def test_copilot_csv_report(self, capsys):
        summary = {**self._mock_copilot_summary(), "daily": [
            {
                "day": "2024-01-15",
                "total_suggestions_count": 100,
                "total_acceptances_count": 80,
                "total_lines_suggested": 200,
                "total_lines_accepted": 150,
                "total_active_users": 5,
                "total_chat_turns": 10,
                "total_chat_acceptances": 4,
                "total_active_chat_users": 2,
            }
        ]}
        with (
            patch("main.GitHubCopilotClient") as mock_client_cls,
            patch("main.summarize_usage", return_value=summary),
        ):
            mock_client = MagicMock()
            mock_client.get_org_usage.return_value = []
            mock_client_cls.return_value = mock_client

            result = run(
                ["--github-token", "tok", "--org", "my-org", "--format", "csv"]
            )

        captured = capsys.readouterr()
        assert result == 0
        assert "day," in captured.out

    def test_output_to_file(self, tmp_path):
        out_file = tmp_path / "report.txt"
        with (
            patch("main.GitHubCopilotClient") as mock_client_cls,
            patch("main.summarize_usage", return_value=self._mock_copilot_summary()),
        ):
            mock_client = MagicMock()
            mock_client.get_org_usage.return_value = []
            mock_client_cls.return_value = mock_client

            result = run(
                [
                    "--github-token", "tok",
                    "--org", "my-org",
                    "--output", str(out_file),
                ]
            )

        assert result == 0
        assert out_file.exists()
        assert "COPILOT & AZURE AI USAGE MONITOR" in out_file.read_text()

    def test_enterprise_flag_used(self, capsys):
        with (
            patch("main.GitHubCopilotClient") as mock_client_cls,
            patch("main.summarize_usage", return_value=self._mock_copilot_summary()),
        ):
            mock_client = MagicMock()
            mock_client.get_enterprise_usage.return_value = []
            mock_client_cls.return_value = mock_client

            run(["--github-token", "tok", "--enterprise", "my-enterprise"])

            mock_client.get_enterprise_usage.assert_called_once()
