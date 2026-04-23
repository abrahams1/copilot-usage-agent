import { DashboardData } from "../api/client";
import KpiCards from "./KpiCards";
import UsageChart from "./UsageChart";
import AzureSubscriptionTable from "./AzureSubscriptionTable";

interface Props {
  data: DashboardData;
}

export default function Dashboard({ data }: Props) {
  return (
    <div className="dashboard">
      <KpiCards copilot={data.copilot} foundry={data.foundry} studio={data.studio} />

      <div className="charts-row">
        <div className="chart-card">
          <h3>M365 Copilot Prompts by App</h3>
          <UsageChart
            data={data.copilot.app_breakdown.map((a) => ({
              name: a.app_name,
              value: a.prompts,
            }))}
            color="#0078d4"
          />
        </div>
        <div className="chart-card">
          <h3>Azure AI Token Split</h3>
          <UsageChart
            data={[
              { name: "Prompt Tokens", value: data.foundry.prompt_tokens },
              { name: "Completion Tokens", value: data.foundry.completion_tokens },
            ]}
            color="#107c10"
          />
        </div>
      </div>

      <div className="table-card">
        <h3>Azure Subscriptions — AI Usage</h3>
        <AzureSubscriptionTable subscriptions={data.subscriptions} />
      </div>
    </div>
  );
}
