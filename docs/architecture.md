# Architecture

## High-level overview

```mermaid
graph TD
    subgraph "Frontend (React + Vite)"
        UI[Dashboard & Chat Panel]
    end

    subgraph "Backend (FastAPI)"
        API[REST API]
        AG[LangGraph Agent]
    end

    subgraph "MCP Servers (Python stdio)"
        WIQ[WorkIQ MCP<br/>M365 Copilot Usage]
        FIQ[FoundryIQ MCP<br/>Azure AI Foundry Metrics]
        CST[Copilot Studio MCP<br/>Studio Messages]
    end

    subgraph "Microsoft APIs"
        GRAPH[Microsoft Graph<br/>/reports, /admin]
        ARM[Azure Resource Manager<br/>/subscriptions, /monitor]
        MON[Azure Monitor<br/>/metrics]
    end

    UI -->|REST / SSE| API
    API --> AG
    AG -->|MCP stdio| WIQ
    AG -->|MCP stdio| FIQ
    AG -->|MCP stdio| CST
    WIQ -->|HTTPS| GRAPH
    FIQ -->|HTTPS| ARM
    FIQ -->|HTTPS| MON
    CST -->|HTTPS| GRAPH
```

## Component responsibilities

| Component | Responsibility |
|---|---|
| **React UI** | Renders KPI cards, charts, subscription table. Hosts a chat panel for ad-hoc questions. Calls `/api/dashboard` for initial load and `/api/chat` for agent interactions. |
| **FastAPI backend** | Serves REST endpoints. Owns the LangGraph agent lifecycle. Manages MCP server subprocesses. |
| **LangGraph agent** | Orchestrates multi-step reasoning. Routes user questions to the appropriate MCP tool(s), synthesizes answers, and streams tokens back via SSE. |
| **WorkIQ MCP** | Wraps Microsoft Graph report APIs for M365 Copilot: `getM365AppUserDetail`, `getMicrosoft365CopilotUsageReport`. Exposes MCP tools: `get_copilot_usage_summary`, `get_copilot_user_detail`, `get_copilot_app_usage`. |
| **FoundryIQ MCP** | Wraps Azure Monitor metrics and ARM resource queries scoped to Azure AI Foundry (Azure OpenAI, AI Studio). Exposes: `get_foundry_token_usage`, `get_foundry_transactions`, `list_ai_resources`, `get_subscription_cost`. |
| **Copilot Studio MCP** | Wraps Power Platform / Graph APIs for Copilot Studio analytics. Exposes: `get_studio_message_usage`, `get_studio_agents`. |

## Authentication flow

```mermaid
sequenceDiagram
    participant Admin as Admin (browser)
    participant FE as React frontend
    participant BE as FastAPI backend
    participant Entra as Entra ID
    participant Graph as MS Graph / Azure

    Note over BE: On startup, acquires token<br/>via client credentials
    BE->>Entra: POST /token (client_id, client_secret, scope)
    Entra-->>BE: access_token (app-only)

    Admin->>FE: Opens dashboard
    FE->>BE: GET /api/dashboard
    BE->>Graph: GET /reports/... (Bearer token)
    Graph-->>BE: usage data
    BE-->>FE: JSON
    FE-->>Admin: Rendered dashboard
```

## Data flow for a chat question

```mermaid
sequenceDiagram
    participant User
    participant FE as React
    participant BE as FastAPI
    participant AG as LangGraph Agent
    participant MCP as MCP Server(s)
    participant MS as Microsoft APIs

    User->>FE: "Which subscription used the most tokens?"
    FE->>BE: POST /api/chat {message}
    BE->>AG: invoke(state)
    AG->>AG: Plan: call foundryiq.get_foundry_token_usage
    AG->>MCP: MCP tool call
    MCP->>MS: Azure Monitor metrics query
    MS-->>MCP: metrics JSON
    MCP-->>AG: tool result
    AG->>AG: Synthesize answer
    AG-->>BE: streamed tokens
    BE-->>FE: SSE stream
    FE-->>User: "Subscription 'Prod-AI' used 42M tokens..."
```

## Technology stack

| Layer | Tech | Why |
|---|---|---|
| Frontend | React 18, Vite, TypeScript, Recharts | Fast HMR, modern charting, strong typing |
| Backend | FastAPI, Python 3.12 | Async-native, auto OpenAPI spec |
| Agent | LangGraph, LangChain, Azure OpenAI | State-machine agent with tool use |
| MCP protocol | `mcp` Python SDK (stdio transport) | Standardized tool exposure |
| Auth | `azure-identity` ClientSecretCredential | Service principal, auto token refresh |
| Azure queries | `azure-mgmt-monitor`, ARM REST | Metrics + resource discovery |
| Graph queries | `msgraph-sdk` | Official Python SDK for Graph |
