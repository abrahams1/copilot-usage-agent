# copilot-usage-agent

Monitor GitHub Copilot and Azure AI usage from a single command-line tool and GitHub Actions workflow.

## Features

- **GitHub Copilot metrics** — daily suggestions, acceptances, acceptance rate, chat turns, and active users (organization or enterprise scope)
- **Azure AI cost data** — cost breakdown by service (Azure OpenAI, Cognitive Services, etc.) via Azure Cost Management
- **Azure OpenAI resource metrics** — token transactions, generated tokens, and active tokens via Azure Monitor
- **Multiple output formats** — human-readable text, JSON, and CSV
- **GitHub Actions workflow** — scheduled daily runs that upload the report as a workflow artifact

---

## Project Layout

```
.
├── src/
│   ├── copilot_monitor/
│   │   ├── __init__.py
│   │   ├── github_copilot.py   # GitHub Copilot API client + summarizer
│   │   ├── azure_ai.py         # Azure Cost Management + Monitor client
│   │   └── report.py           # Text / JSON / CSV report generation
│   └── main.py                 # CLI entry point
├── tests/                      # pytest test suite
├── .github/workflows/
│   ├── monitor.yml             # Scheduled usage monitor workflow
│   └── tests.yml               # CI test workflow
├── requirements.txt
└── requirements-dev.txt
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set credentials

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | Fine-grained PAT with **read:org** and **manage_billing:copilot** scopes |
| `GITHUB_ORG` | GitHub organization login (e.g. `my-company`) |
| `GITHUB_ENTERPRISE` | GitHub enterprise slug (alternative to org) |
| `AZURE_BEARER_TOKEN` | Azure management bearer token (`az account get-access-token --query accessToken -o tsv`) |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | Azure resource group (optional — scopes cost data) |
| `AZURE_OPENAI_RESOURCE` | Azure OpenAI account name (optional — enables per-resource metrics) |

### 3. Run the monitor

```bash
# Text report (default)
PYTHONPATH=src python src/main.py --org my-company

# JSON output
PYTHONPATH=src python src/main.py --org my-company --format json

# CSV of daily Copilot data
PYTHONPATH=src python src/main.py --org my-company --format csv --output copilot.csv

# Custom date range
PYTHONPATH=src python src/main.py --org my-company --since 2024-01-01 --until 2024-01-31

# Azure AI only
PYTHONPATH=src python src/main.py \
  --subscription-id <sub-id> \
  --resource-group my-rg \
  --openai-resource my-openai-account

# Both together
PYTHONPATH=src python src/main.py \
  --org my-company \
  --subscription-id <sub-id> \
  --resource-group my-rg \
  --openai-resource my-openai-account
```

**Example text output:**

```
============================================================
  COPILOT & AZURE AI USAGE MONITOR
  Generated: 2024-01-28 08:00:00 UTC
============================================================

------------------------------------------------------------
  GitHub Copilot Usage Summary
------------------------------------------------------------
  Period:              28 day(s)
  Total Suggestions:   45,230
  Total Acceptances:   34,102
  Acceptance Rate:     75.4%
  Lines Suggested:     89,400
  Lines Accepted:      61,200
  Active Users (sum):  320
  Chat Turns:          1,840
  Chat Acceptances:    740
  Active Chat Users:   48

------------------------------------------------------------
  Azure AI Cost Summary
------------------------------------------------------------
  Total Cost:  142.3800 USD
  By Service:
    Azure OpenAI                     128.5000 USD
    Cognitive Services                13.8800 USD

------------------------------------------------------------
  Azure OpenAI Metrics — my-openai-account
------------------------------------------------------------
  GeneratedTokens                        2,450,000
  TokenTransaction                       4,900,000
------------------------------------------------------------
```

---

## GitHub Actions Setup

### Secrets and Variables

Configure the following in your repository's **Settings → Secrets and variables**:

| Type | Name | Description |
|---|---|---|
| Secret | `COPILOT_USAGE_TOKEN` | GitHub PAT (Copilot metrics scope) |
| Secret | `AZURE_BEARER_TOKEN` | Azure management bearer token |
| Variable | `GITHUB_ORG` | GitHub organization login |
| Variable | `GITHUB_ENTERPRISE` | GitHub enterprise slug (alternative) |
| Variable | `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| Variable | `AZURE_RESOURCE_GROUP` | Azure resource group |
| Variable | `AZURE_OPENAI_RESOURCE` | Azure OpenAI account name |

The workflow (`.github/workflows/monitor.yml`) runs every day at 08:00 UTC and uploads the report as a workflow artifact retained for 90 days.  It can also be triggered manually via **Actions → Copilot & Azure AI Usage Monitor → Run workflow**, where you can override the format and date range.

---

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
PYTHONPATH=src pytest tests/ -v
```

---

## Required API Permissions

### GitHub Token

- `read:org` — read organization membership
- `manage_billing:copilot` — read Copilot seat and usage data

For enterprise-level data, the token owner must be an **enterprise owner** or **billing manager**.

### Azure Service Principal / Managed Identity

- `Cost Management Reader` on the subscription or resource group
- `Monitoring Reader` on the Azure OpenAI resource (for per-resource metrics)

