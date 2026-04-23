import { useEffect, useState } from "react";
import { DashboardData, fetchDashboard } from "./api/client";
import Dashboard from "./components/Dashboard";
import ChatPanel from "./components/ChatPanel";

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Copilot Usage Dashboard</h1>
        <span className="subtitle">M365 Copilot &middot; Copilot Studio &middot; Azure AI Foundry</span>
      </header>

      <main className="app-main">
        {loading && <div className="loading">Loading dashboard data...</div>}
        {error && <div className="error">Error: {error}</div>}
        {data && <Dashboard data={data} />}
      </main>

      <aside className="chat-aside">
        <ChatPanel />
      </aside>
    </div>
  );
}
