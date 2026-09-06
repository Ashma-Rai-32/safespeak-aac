// Results/metrics view: real numbers pulled from BigQuery's
// fabrication_conditional_metrics view (see docs/sql/ddl.sql), exported as a
// static JSON snapshot for the deployed demo. This is the screenshot-able
// results table for the submission.
export default function MetricsView({ metrics }) {
  if (!metrics || metrics.length === 0) {
    return (
      <div className="panel metrics-panel">
        <h2>Benchmark Results</h2>
        <p>No results loaded yet.</p>
      </div>
    );
  }

  return (
    <div className="panel metrics-panel">
      <h2>Benchmark Results</h2>
      <p className="panel-subtitle">
        Fabrication-conditional catch rate: of the phrases that actually fabricated intent,
        what fraction did the safety layer catch. Computed from {metrics[0]?.total_outputs ?? "?"} scenarios
        across all models.
      </p>

      <div className="metrics-table-wrap">
        <table className="metrics-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Total Outputs</th>
              <th>Actual Fabrications</th>
              <th>Fabrication Rate</th>
              <th>Caught</th>
              <th>Catch Rate</th>
              <th>Real Misses</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => (
              <tr key={`${m.model_name}-${m.benchmark_run_id}`}>
                <td>{m.model_name}</td>
                <td>{m.total_outputs}</td>
                <td>{m.actual_fabrication_count}</td>
                <td>{(m.fabrication_rate * 100).toFixed(1)}%</td>
                <td>{m.caught_count}</td>
                <td className={m.fabrication_catch_rate >= 0.7 ? "rate-good" : "rate-warn"}>
                  {(m.fabrication_catch_rate * 100).toFixed(1)}%
                </td>
                <td>{m.real_misses_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
