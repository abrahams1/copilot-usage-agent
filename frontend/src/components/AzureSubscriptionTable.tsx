import { SubscriptionRow } from "../api/client";

interface Props {
  subscriptions: SubscriptionRow[];
}

export default function AzureSubscriptionTable({ subscriptions }: Props) {
  return (
    <table className="sub-table">
      <thead>
        <tr>
          <th>Subscription</th>
          <th>Tokens</th>
          <th>Cost (USD)</th>
          <th>AI Resources</th>
        </tr>
      </thead>
      <tbody>
        {subscriptions.map((s) => (
          <tr key={s.subscription_id}>
            <td>{s.subscription_name}</td>
            <td>{s.tokens.toLocaleString()}</td>
            <td>${s.cost_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            <td>{s.ai_resource_count}</td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <td><strong>Total</strong></td>
          <td><strong>{subscriptions.reduce((a, s) => a + s.tokens, 0).toLocaleString()}</strong></td>
          <td>
            <strong>
              ${subscriptions
                .reduce((a, s) => a + s.cost_usd, 0)
                .toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </strong>
          </td>
          <td><strong>{subscriptions.reduce((a, s) => a + s.ai_resource_count, 0)}</strong></td>
        </tr>
      </tfoot>
    </table>
  );
}
