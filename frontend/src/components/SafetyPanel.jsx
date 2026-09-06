import { useState } from "react";
import { CORE_VOCABULARY } from "../data/coreVocabulary";

// The LLM AAC panel + safety layer, together. Patient selects words, an LLM
// expands them into a full phrase, and the safety layer scores it. If
// UNSUPPORTED, the phrase is blocked from display and a human-confirmation
// state is shown instead -- this is the core differentiator of the project.
//
// benchmarkResults: an array of real, pre-computed rows from BigQuery
// (scenario_id, patient_input, generated_phrase, predicted_label, reason,
// model_name), passed in as a prop. This demo replays REAL benchmark data
// rather than making live Gemini calls from the browser, so results are
// reproducible and don't depend on a live API key or rate limits during
// grading/demo.
export default function SafetyPanel({ benchmarkResults }) {
  const [selected, setSelected] = useState([]);
  const [result, setResult] = useState(null); // the matched benchmark row, if any

  const addWord = (word) => {
    setSelected((prev) => [...prev, word]);
    setResult(null);
  };
  const clear = () => {
    setSelected([]);
    setResult(null);
  };
  const removeLast = () => {
    setSelected((prev) => prev.slice(0, -1));
    setResult(null);
  };

  const findMatch = () => {
    const inputKey = selected.join(",").toUpperCase();
    const match = benchmarkResults.find(
      (r) => r.patient_input.join(",").toUpperCase() === inputKey
    );
    setResult(match || { notFound: true });
  };

  return (
    <div className="panel safety-panel">
      <h2>LLM Panel + Safety Layer</h2>
      <p className="panel-subtitle">
        Select the same words as a benchmark scenario to replay a real, recorded result.
      </p>

      <div className="output-bar">
        <span className="output-text">
          {selected.length > 0 ? selected.join(" ") : " "}
        </span>
        <div className="output-actions">
          <button onClick={removeLast} disabled={selected.length === 0}>Undo</button>
          <button onClick={clear} disabled={selected.length === 0}>Clear</button>
          <button onClick={findMatch} disabled={selected.length === 0} className="primary-action">
            Generate
          </button>
        </div>
      </div>

      <div className="word-grid">
        {CORE_VOCABULARY.map((word) => (
          <button key={word} className="word-tile" onClick={() => addWord(word)}>
            {word}
          </button>
        ))}
      </div>

      {result && <ResultCard result={result} />}
    </div>
  );
}

function ResultCard({ result }) {
  if (result.notFound) {
    return (
      <div className="result-card result-unknown">
        <p>No recorded benchmark scenario matches this exact word sequence.</p>
        <p className="result-hint">Try a sequence from the scenarios list, e.g. STOP + PAIN.</p>
      </div>
    );
  }

  const isBlocked = result.predicted_label === "UNSUPPORTED";

  return (
    <div className={`result-card ${isBlocked ? "result-blocked" : "result-passed"}`}>
      <div className="result-header">
        <span className="model-badge">{result.model_name}</span>
        <span className={`verdict-badge ${isBlocked ? "verdict-blocked" : "verdict-passed"}`}>
          {isBlocked ? "BLOCKED" : "SUPPORTED"}
        </span>
      </div>

      {isBlocked ? (
        <>
          <div className="blocked-banner">
            ⚠ Awaiting human confirmation
          </div>
          <p className="generated-phrase struck-through">"{result.generated_phrase}"</p>
          <p className="result-reason">{result.reason}</p>
        </>
      ) : (
        <>
          <p className="generated-phrase">"{result.generated_phrase}"</p>
          <p className="result-reason">{result.reason}</p>
        </>
      )}
    </div>
  );
}
