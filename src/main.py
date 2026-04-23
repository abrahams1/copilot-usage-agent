"""Main entry point for the Copilot and Azure AI Usage Monitor."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date

from copilot_monitor.azure_ai import AzureAIClient, summarize_cost, summarize_metrics
from copilot_monitor.github_copilot import GitHubCopilotClient, summarize_usage
from copilot_monitor.report import (
    generate_csv_report,
    generate_json_report,
    generate_text_report,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor GitHub Copilot and Azure AI usage.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Output format
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write report to FILE instead of stdout.",
    )

    # Date range
    parser.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help="Start date for usage data.",
    )
    parser.add_argument(
        "--until",
        metavar="YYYY-MM-DD",
        help="End date for usage data.",
    )

    # GitHub Copilot options
    copilot_group = parser.add_argument_group("GitHub Copilot")
    copilot_group.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN env var).",
    )
    copilot_group.add_argument(
        "--org",
        default=os.environ.get("GITHUB_ORG"),
        help="GitHub organization login (or set GITHUB_ORG env var).",
    )
    copilot_group.add_argument(
        "--enterprise",
        default=os.environ.get("GITHUB_ENTERPRISE"),
        help="GitHub enterprise slug (or set GITHUB_ENTERPRISE env var).",
    )

    # Azure AI options
    azure_group = parser.add_argument_group("Azure AI")
    azure_group.add_argument(
        "--azure-token",
        default=os.environ.get("AZURE_BEARER_TOKEN"),
        help="Azure management bearer token (or set AZURE_BEARER_TOKEN env var).",
    )
    azure_group.add_argument(
        "--subscription-id",
        default=os.environ.get("AZURE_SUBSCRIPTION_ID"),
        help="Azure subscription ID (or set AZURE_SUBSCRIPTION_ID env var).",
    )
    azure_group.add_argument(
        "--resource-group",
        default=os.environ.get("AZURE_RESOURCE_GROUP"),
        help=(
            "Azure resource group for cost/metrics scope "
            "(or set AZURE_RESOURCE_GROUP env var)."
        ),
    )
    azure_group.add_argument(
        "--openai-resource",
        default=os.environ.get("AZURE_OPENAI_RESOURCE"),
        help=(
            "Azure OpenAI account name for per-resource metrics "
            "(or set AZURE_OPENAI_RESOURCE env var)."
        ),
    )

    return parser.parse_args(argv)


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    since = _parse_date(args.since)
    until = _parse_date(args.until)

    copilot_summary = None
    azure_cost_summary = None
    azure_metrics = None

    # ------------------------------------------------------------------
    # GitHub Copilot
    # ------------------------------------------------------------------
    if args.github_token and (args.org or args.enterprise):
        try:
            client = GitHubCopilotClient(token=args.github_token)
            if args.org:
                logger.info("Fetching Copilot usage for org: %s", args.org)
                daily = client.get_org_usage(args.org, since=since, until=until)
            else:
                logger.info(
                    "Fetching Copilot usage for enterprise: %s", args.enterprise
                )
                daily = client.get_enterprise_usage(
                    args.enterprise, since=since, until=until
                )
            copilot_summary = summarize_usage(daily)
            logger.info(
                "Copilot: %d day(s), %.1f%% acceptance rate",
                copilot_summary["days"],
                copilot_summary["acceptance_rate"],
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch Copilot usage: %s", exc)
    else:
        if not args.github_token:
            logger.warning(
                "No GitHub token provided; skipping Copilot metrics. "
                "Set --github-token or GITHUB_TOKEN."
            )
        if not (args.org or args.enterprise):
            logger.warning(
                "No org or enterprise provided; skipping Copilot metrics. "
                "Set --org/GITHUB_ORG or --enterprise/GITHUB_ENTERPRISE."
            )

    # ------------------------------------------------------------------
    # Azure AI
    # ------------------------------------------------------------------
    if args.azure_token and args.subscription_id:
        try:
            azure_client = AzureAIClient(
                subscription_id=args.subscription_id,
                bearer_token=args.azure_token,
            )

            logger.info(
                "Fetching Azure AI costs for subscription: %s", args.subscription_id
            )
            cost_data = azure_client.get_cost_by_resource(
                resource_group=args.resource_group,
                since=since,
                until=until,
            )
            azure_cost_summary = summarize_cost(cost_data)
            logger.info(
                "Azure AI cost: %.4f %s",
                azure_cost_summary["total_cost"],
                azure_cost_summary["currency"],
            )

            if args.resource_group and args.openai_resource:
                logger.info(
                    "Fetching Azure OpenAI metrics for resource: %s",
                    args.openai_resource,
                )
                metrics_data = azure_client.get_openai_resource_metrics(
                    resource_group=args.resource_group,
                    resource_name=args.openai_resource,
                    since=since,
                    until=until,
                )
                azure_metrics = summarize_metrics(metrics_data)
                logger.info("Azure OpenAI metrics: %s", azure_metrics)

        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch Azure AI usage: %s", exc)
    else:
        if not args.azure_token:
            logger.warning(
                "No Azure bearer token provided; skipping Azure AI metrics. "
                "Set --azure-token or AZURE_BEARER_TOKEN."
            )
        if not args.subscription_id:
            logger.warning(
                "No Azure subscription ID provided; skipping Azure AI metrics. "
                "Set --subscription-id or AZURE_SUBSCRIPTION_ID."
            )

    # ------------------------------------------------------------------
    # Nothing to report
    # ------------------------------------------------------------------
    if copilot_summary is None and azure_cost_summary is None and azure_metrics is None:
        logger.error(
            "No data collected. Provide credentials for at least one source."
        )
        return 1

    # ------------------------------------------------------------------
    # Format output
    # ------------------------------------------------------------------
    if args.format == "json":
        output = generate_json_report(
            copilot_summary=copilot_summary,
            azure_cost_summary=azure_cost_summary,
            azure_metrics=azure_metrics,
        )
    elif args.format == "csv":
        daily_records = (copilot_summary or {}).get("daily", [])
        output = generate_csv_report(daily_records)
    else:
        output = generate_text_report(
            copilot_summary=copilot_summary,
            azure_cost_summary=azure_cost_summary,
            azure_metrics=azure_metrics,
            resource_name=args.openai_resource or "",
        )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        logger.info("Report written to %s", args.output)
    else:
        sys.stdout.write(output)

    return 0


if __name__ == "__main__":
    sys.exit(run())
