# Data Model

## Dashboard API response

The `/api/dashboard` endpoint returns a single JSON payload consumed by the React frontend.

```mermaid
classDiagram
    class DashboardResponse {
        +CopilotSummary copilot
        +FoundrySummary foundry
        +StudioSummary studio
        +list~SubscriptionRow~ subscriptions
    }

    class CopilotSummary {
        +int total_enabled_users
        +int total_active_users
        +int total_prompts_30d
        +list~AppUsage~ app_breakdown
        +str snapshot_date
    }

    class AppUsage {
        +str app_name
        +int prompts
        +int active_users
    }

    class FoundrySummary {
        +int total_tokens
        +int prompt_tokens
        +int completion_tokens
        +float total_cost_usd
        +str period
    }

    class StudioSummary {
        +int total_messages
        +int billed_messages
        +int overage_messages
        +int agent_count
        +str period
    }

    class SubscriptionRow {
        +str subscription_id
        +str subscription_name
        +int tokens
        +float cost_usd
        +int ai_resource_count
    }

    DashboardResponse --> CopilotSummary
    DashboardResponse --> FoundrySummary
    DashboardResponse --> StudioSummary
    DashboardResponse --> SubscriptionRow
    CopilotSummary --> AppUsage
```

## Chat API

### Request

```json
POST /api/chat
{
  "message": "Which app has the most Copilot prompts?",
  "conversation_id": "uuid-optional"
}
```

### Response (SSE stream)

```
event: token
data: {"content": "Teams"}

event: token
data: {"content": " leads with"}

event: done
data: {"conversation_id": "uuid"}
```
