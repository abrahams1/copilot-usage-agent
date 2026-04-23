export interface AppUsage {
  app_name: string;
  prompts: number;
  active_users: number;
}

export interface CopilotSummary {
  total_enabled_users: number;
  total_active_users: number;
  total_prompts_30d: number;
  app_breakdown: AppUsage[];
  snapshot_date: string;
}

export interface FoundrySummary {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost_usd: number;
  period: string;
}

export interface StudioSummary {
  total_messages: number;
  billed_messages: number;
  overage_messages: number;
  agent_count: number;
  period: string;
}

export interface SubscriptionRow {
  subscription_id: string;
  subscription_name: string;
  tokens: number;
  cost_usd: number;
  ai_resource_count: number;
}

export interface DashboardData {
  copilot: CopilotSummary;
  foundry: FoundrySummary;
  studio: StudioSummary;
  subscriptions: SubscriptionRow[];
}

const API_BASE = "/api";

export async function fetchDashboard(): Promise<DashboardData> {
  const resp = await fetch(`${API_BASE}/dashboard`);
  if (!resp.ok) throw new Error(`Dashboard fetch failed: ${resp.status}`);
  return resp.json();
}

export async function* streamChat(
  message: string,
  conversationId?: string
): AsyncGenerator<string, void> {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });

  if (!resp.ok) throw new Error(`Chat failed: ${resp.status}`);
  if (!resp.body) throw new Error("No response body");

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const raw = line.slice(6);
        try {
          const parsed = JSON.parse(raw);
          if (parsed.content) yield parsed.content;
        } catch {
          // skip malformed
        }
      }
    }
  }
}
