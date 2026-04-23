import { CopilotSummary, FoundrySummary, StudioSummary } from "../api/client";

interface Props {
  copilot: CopilotSummary;
  foundry: FoundrySummary;
  studio: StudioSummary;
}

function fmt(n: number): string {
  return n.toLocaleString();
}

function fmtUsd(n: number): string {
  return `$${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function KpiCards({ copilot, foundry, studio }: Props) {
  const cards = [
    { label: "Copilot Enabled Users", value: fmt(copilot.total_enabled_users), accent: "#0078d4" },
    { label: "Copilot Active Users", value: fmt(copilot.total_active_users), accent: "#005a9e" },
    { label: "Total Prompts (30d)", value: fmt(copilot.total_prompts_30d), accent: "#2b88d8" },
    { label: "Azure AI Tokens", value: fmt(foundry.total_tokens), accent: "#107c10" },
    { label: "Azure AI Cost", value: fmtUsd(foundry.total_cost_usd), accent: "#d83b01" },
    { label: "Studio Messages", value: fmt(studio.total_messages), accent: "#8661c5" },
    { label: "Studio Billed", value: fmt(studio.billed_messages), accent: "#5c2d91" },
    { label: "Studio Agents", value: fmt(studio.agent_count), accent: "#b4009e" },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((c) => (
        <div key={c.label} className="kpi-card" style={{ borderTopColor: c.accent }}>
          <div className="kpi-value">{c.value}</div>
          <div className="kpi-label">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
