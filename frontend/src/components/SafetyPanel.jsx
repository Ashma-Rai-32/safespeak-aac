import { useState, useMemo } from "react";
import { CORE_VOCABULARY } from "../data/coreVocabulary";
import { generateAndScoreLive, hasLiveGenerationKey } from "../lib/liveGenerate";

// The LLM AAC panel + safety layer, together. Patient selects words, an LLM
// expands them into a full phrase, and the safety layer scores it. If
// UNSUPPORTED, the phrase is blocked from display and a human-confirmation
// state is shown instead -- this is the core differentiator of the project.
//
// benchmarkResults: an array of real, pre-computed rows from BigQuery
// (scenario_id, patient_input, generated_phrase, predicted_label, reason,
// model_name), passed in as a prop, used for the scenario picker (fast,
// reproducible, no API key/rate-limit risk).
//
// Manual word-tap sequences that don't match a recorded scenario fall back
// to a LIVE Gemini call (see lib/liveGenerate.js) when a frontend API key is
// configured, so the demo isn't limited to only the 41 pre-recorded cases.
// See liveGenerate.js for the security tradeoff this involves.
export default function SafetyPanel({ benchmarkResults }) {
  const scenarioOptions = useMemo(() => {
    const seen = new Map();
    for (const r of benchmarkResults) {
      if (!seen.has(r.scenario_id)) {
        seen.set(r.scenario_id, { scenario_id: r.scenario_id, patient_input: r.patient_input });
      }
    }
    return Array.from(seen.values()).sort((a, b) => a.scenario_id.localeCompare(b.scenario_id));
  }, [benchmarkResults]);

  const defaultScenarioId = scenarioOptions.some((s) => s.scenario_id === "SC-015")
    ? "SC-015"
    : scenarioOptions[0]?.scenario_id ?? "";

  const [scenarioId, setScenarioId] = useState(defaultScenarioId);
  const [selected, setSelected] = useState([]);
  const [mode, setMode] = useState("picker"); // "picker" | "manual"
  const [result, setResult] = useState(null);
  const [liveState, setLiveState] = useState("idle"); // "idle" | "loading" | "error"
  const [liveError, setLiveError] = useState(null);

  const matchesFor = (id) => benchmarkResults.filter((r) => r.scenario_id === id);

  const handlePickerChange = (id) => {
    setScenarioId(id);
    setLiveState("idle");
    const matches = matchesFor(id);
    setResult(matches.length > 0 ? { multi: matches } : { notFound: true });
  };

  const addWord = (word) => {
    setMode("manual");
    setSelected((prev) => [...prev, word]);
    setResult(null);
    setLiveState("idle");
  };
  const clear = () => {
    setSelected([]);
    setResult(null);
    setLiveState("idle");
  };
  const removeLast = () => {
    setSelected((prev) => prev.slice(0, -1));
    setResult(null);
    setLiveState("idle");
  };

  const findMatch = async () => {
    const inputKey = selected.join(",").toUpperCase();
    const matches = benchmarkResults.filter(
      (r) => r.patient_input.join(",").toUpperCase() === inputKey
    );

    if (matches.length > 0) {
      setResult({ multi: matches });
      setLiveState("idle");
      return;
    }

    if (!hasLiveGenerationKey()) {
      setResult({ notFound: true });
      setLiveState("idle");
      return;
    }

    setResult(null);
    setLiveState("loading");
    setLiveError(null);
    try {
      const liveResult = await generateAndScoreLive(selected);
      setResult({ multi: [liveResult] });
      setLiveState("idle");
    } catch (err) {
      setLiveState("error");
      setLiveError(err.message || String(err));
    }
  };

  const currentPatientInput = mode === "picker"
    ? scenarioOptions.find((s) => s.scenario_id === scenarioId)?.patient_input ?? []
    : selected;

  return (
    <div className="panel safety-panel">
      <h2>LLM Panel + Safety Layer</h2>
      <p className="panel-subtitle">
        Pick a recorded scenario, or tap your own words for a live result.
      </p>

      <div className="scenario-picker-row">
        <label htmlFor="scenario-picker">Scenario:</label>
        <select
          id="scenario-picker"
          value={mode === "picker" ? scenarioId : ""}
          onChange={(e) => {
            setMode("picker");
            handlePickerChange(e.target.value);
          }}
        >
          {scenarioOptions.map((s) => (
            <option key={s.scenario_id} value={s.scenario_id}>
              {s.scenario_id}: {s.patient_input.join(" + ")}
            </option>
          ))}
        </select>
      </div>

      <div className="output-bar">
        <span className="output-text">
          {currentPatientInput.length > 0 ? currentPatientInput.join(" ") : " "}
        </span>
        {mode === "manual" && (
          <div className="output-actions">
            <button onClick={removeLast} disabled={selected.length === 0}>Undo</button>
            <button onClick={clear} disabled={selected.length === 0}>Clear</button>
            <button
              onClick={findMatch}
              disabled={selected.length === 0 || liveState === "loading"}
              className="primary-action"
            >
              {liveState === "loading" ? "Generating…" : "Generate"}
            </button>
          </div>
        )}
      </div>

      <p className="panel-hint">
        Tap words below to build your own sequence.{" "}
        {hasLiveGenerationKey()
          ? "If it doesn't match a recorded scenario, it calls Gemini live."
          : "Live generation isn't configured in this deployment, only recorded scenarios will match."}
      </p>
      <div className="word-grid">
        {CORE_VOCABULARY.map((word) => (
          <button key={word} className="word-tile" onClick={() => addWord(word)}>
            {word}
          </button>
        ))}
      </div>

      {liveState === "loading" && (
        <div className="result-card result-loading">
          <p>Calling Gemini live…</p>
        </div>
      )}

      {liveState === "error" && (
        <div className="result-card result-unknown">
          <p>Live generation failed: {liveError}</p>
        </div>
      )}

      {liveState !== "loading" && liveState !== "error" && (
        result ? (
          <ResultGroup result={result} />
        ) : (
          <ResultGroup result={{ multi: matchesFor(scenarioId) }} />
        )
      )}
    </div>
  );
}

function ResultGroup({ result }) {
  if (result.notFound) {
    return (
      <div className="result-card result-unknown">
        <p>No recorded benchmark scenario matches this exact word sequence.</p>
        <p className="result-hint">Try a sequence from the picker above, e.g. STOP + PAIN, or NO + COLD.</p>
      </div>
    );
  }

  if (!result.multi || result.multi.length === 0) return null;

  return (
    <>
      {result.multi.map((r) => (
        <ResultCard key={`${r.scenario_id}-${r.model_name}`} result={r} />
      ))}
    </>
  );
}

function ResultCard({ result }) {
  const isBlocked = result.predicted_label === "UNSUPPORTED";
  // Human-in-the-loop resolution for a blocked phrase. Not derived from any
  // stored data -- this is a live, local decision a caregiver makes right
  // now, simulating the actual safety-layer workflow: a blocked phrase never
  // reaches the patient's speaker until a human either overrides the safety
  // layer (approves it anyway, e.g. they know the patient really did mean
  // this) or agrees with the block (rejects it, the patient must try again).
  const [resolution, setResolution] = useState(null); // null | "approved" | "rejected"

  return (
    <div className={`result-card ${isBlocked ? "result-blocked" : "result-passed"}`}>
      <div className="result-header">
        <span className="model-badge">
          {result.model_name}
          {result.live && <span className="live-badge"> · LIVE</span>}
        </span>
        <span className={`verdict-badge ${isBlocked ? "verdict-blocked" : "verdict-passed"}`}>
          {isBlocked ? "BLOCKED" : "SUPPORTED"}
        </span>
      </div>

      {isBlocked ? (
        <>
          {resolution === null && (
            <>
              <div className="blocked-banner">
                ⚠ Awaiting human confirmation
              </div>
              <p className="generated-phrase struck-through">"{result.generated_phrase}"</p>
              <p className="result-reason">{result.reason}</p>
              <div className="confirmation-actions">
                <button
                  className="confirm-button confirm-reject"
                  onClick={() => setResolution("rejected")}
                >
                  ✕ Reject (block stands)
                </button>
                <button
                  className="confirm-button confirm-approve"
                  onClick={() => setResolution("approved")}
                >
                  ✓ Approve anyway (I confirm this is what the patient meant)
                </button>
              </div>
            </>
          )}

          {resolution === "rejected" && (
            <div className="resolution-banner resolution-rejected">
              <p><strong>Rejected by caregiver.</strong> This phrase will not be spoken. The patient should try again.</p>
              <p className="generated-phrase struck-through">"{result.generated_phrase}"</p>
            </div>
          )}

          {resolution === "approved" && (
            <div className="resolution-banner resolution-approved">
              <p><strong>Approved by caregiver override.</strong> Spoken despite the safety layer's block, on human authority.</p>
              <p className="generated-phrase">"{result.generated_phrase}"</p>
            </div>
          )}
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
