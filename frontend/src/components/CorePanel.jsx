import { useState } from "react";
import { CORE_VOCABULARY } from "../data/coreVocabulary";

// Static 36-word Core Vocabulary panel: the baseline AAC experience with no
// AI involved. Tapping words builds a sequence; there is no expansion or
// interpretation step, what the patient selects is exactly what's shown.
export default function CorePanel() {
  const [selected, setSelected] = useState([]);

  const addWord = (word) => setSelected((prev) => [...prev, word]);
  const clear = () => setSelected([]);
  const removeLast = () => setSelected((prev) => prev.slice(0, -1));

  return (
    <div className="panel core-panel">
      <h2>Static Core Panel</h2>
      <p className="panel-subtitle">36-word baseline. No AI. What you select is what you get.</p>

      <div className="output-bar">
        <span className="output-text">
          {selected.length > 0 ? selected.join(" ") : " "}
        </span>
        <div className="output-actions">
          <button onClick={removeLast} disabled={selected.length === 0}>Undo</button>
          <button onClick={clear} disabled={selected.length === 0}>Clear</button>
        </div>
      </div>

      <div className="word-grid">
        {CORE_VOCABULARY.map((word) => (
          <button key={word} className="word-tile" onClick={() => addWord(word)}>
            {word}
          </button>
        ))}
      </div>
    </div>
  );
}
