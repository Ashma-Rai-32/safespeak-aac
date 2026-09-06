import { useState } from "react";
import CorePanel from "./components/CorePanel";
import SafetyPanel from "./components/SafetyPanel";
import MetricsView from "./components/MetricsView";
import benchmarkResults from "./data/benchmarkResults.json";
import metrics from "./data/metrics.json";
import "./App.css";

const TABS = ["Static Core Panel", "LLM + Safety Layer", "Results"];

function App() {
  const [tab, setTab] = useState(TABS[1]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>SafeSpeak</h1>
        <p className="app-tagline">
          An AAC safety layer that catches AI-fabricated intent before it reaches a patient's caregiver.
        </p>
      </header>

      <nav className="tab-bar">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab-button ${tab === t ? "tab-active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {tab === "Static Core Panel" && <CorePanel />}
        {tab === "LLM + Safety Layer" && <SafetyPanel benchmarkResults={benchmarkResults} />}
        {tab === "Results" && <MetricsView metrics={metrics} />}
      </main>
    </div>
  );
}

export default App;
