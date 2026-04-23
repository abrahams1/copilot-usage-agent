# Copilot Usage Agent

An AI agent that gives M365 / Azure administrators a unified view of AI usage across their tenant:

- **M365 Copilot** – enabled users, active users, prompts submitted, per-app usage (Teams, Outlook, Word, Excel, PowerPoint).
- **Copilot Studio** – messages consumed, billed messages, top agents.
- **Azure AI Foundry** – tokens in/out, transaction units, cost, per-subscription rollups.

Ask the agent follow-up questions in natural language (e.g. *"Which subscription burned the most tokens last week?"*).

---

## Architecture at a glance

```
   ┌────────────────────────┐
   │  React UI (Vite + TS)  │
   │  Dashboard + Chat      │
   └──────────┬─────────────┘
              │ REST / SSE
   ┌──────────▼─────────────┐
   │   FastAPI backend       │
   │   + LangGraph agent     │
   └───┬───────┬─────────┬──┘
       │       │         │
   ┌───▼──┐ ┌──▼────┐ ┌──▼──────────┐
   │WorkIQ│ │Foundry│ │CopilotStudio│   ← MCP servers (Python)
   │ MCP  │ │  IQ   │ │    MCP      │
   └───┬──┘ └──┬────┘ └──┬──────────┘
       │       │         │
   ┌───▼────────▼─────────▼──┐
   │  Microsoft Graph + Azure │
   │   Monitor / ARM APIs     │
   └──────────────────────────┘
```

Full diagrams in [`docs/architecture.md`](docs/architecture.md), [`docs/agent-flow.md`](docs/agent-flow.md), and [`docs/mcp-servers.md`](docs/mcp-servers.md).

---

## Prerequisites

- Python 3.11+
- Node 20+
- An Entra ID app registration with admin consent for:
  - `Reports.Read.All` (M365 usage reports)
  - `ReportSettings.ReadWrite.All` (disable display-name anonymization; optional)
  - Azure RBAC `Monitoring Reader` at the subscription / management group scope
- An Azure OpenAI deployment (GPT-4o / GPT-4.1 class model)

---

## Quick start (local)

```bash
# 1. Clone & configure
git clone <your-repo-url> copilot-usage-agent
cd copilot-usage-agent
cp .env.example .env
# Fill in the values in .env

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Open `http://localhost:5173`. The dashboard will call the backend at `http://localhost:8000`, which fans out to the three MCP servers.

### Docker

```bash
docker compose up --build
```

---

## Repo layout

```
copilot-usage-agent/
├── backend/
│   ├── main.py                 FastAPI app entrypoint
│   ├── config.py               Pydantic settings loaded from .env
│   ├── agent/                  LangGraph agent (state, nodes, graph, prompts)
│   ├── api/                    REST routes + Pydantic response models
│   ├── clients/                Graph / Azure / Azure OpenAI clients
│   └── mcp_servers/            WorkIQ, FoundryIQ, Copilot Studio MCP servers
├── frontend/                   Vite + React + TypeScript dashboard
├── docs/                       Architecture & flow diagrams (Mermaid)
├── scripts/                    Dev helpers
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Configuration

See [`.env.example`](.env.example). All secrets are read via `pydantic-settings`; nothing is committed.

Key variables:

| Variable | Purpose |
|---|---|
| `AZURE_TENANT_ID` | Entra ID tenant |
| `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` | App registration credentials |
| `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_DEPLOYMENT` | LLM used by the agent |
| `USE_MOCK_DATA` | `true` → use bundled fixtures (no tenant required; great for first run) |

---

## Mock mode

On first run, set `USE_MOCK_DATA=true`. The MCP servers will return deterministic fixtures so you can exercise the UI and agent loop before wiring real credentials. Flip to `false` once the app registration has admin consent.

---

## Contributing / next steps

- `docs/architecture.md` explains module responsibilities.
- `docs/agent-flow.md` shows the LangGraph state machine.
- `docs/mcp-servers.md` documents each MCP tool's inputs/outputs.

Open an issue or PR on the GitHub repo once you've pushed.
