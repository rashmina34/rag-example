"use client";

import { useState } from "react";
import { compareTexts } from "../../api";
import Nav from "../../components/Nav";

const PRESETS = {
  "Animals vs vehicles": [
    "cat",
    "kitten",
    "dog",
    "puppy",
    "car",
    "truck",
    "bicycle",
  ],
  "Same meaning, different words": [
    "How do I reset my password?",
    "I forgot my login credentials",
    "What is the capital of France?",
    "Paris is the main city of France",
    "I love pizza",
  ],
  "Words with two meanings": [
    "I deposited money at the bank",
    "We had a picnic on the river bank",
    "The bank approved my loan",
    "Fish swim near the muddy bank",
  ],
};

const WIDTH = 560;
const HEIGHT = 380;
const PAD = 50;

function scale(values, size) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return values.map(
    (value) => PAD + ((value - min) / range) * (size - PAD * 2)
  );
}

function shorten(text) {
  return text.length > 26 ? `${text.slice(0, 25)}…` : text;
}

// white (unrelated) -> blue (identical)
function heat(value) {
  const t = Math.max(0, Math.min(1, value));
  const lightness = 97 - t * 45;
  return `hsl(215 80% ${lightness}%)`;
}

export default function EmbeddingsVisualizer() {
  const [input, setInput] = useState(
    PRESETS["Animals vs vehicles"].join("\n")
  );
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleCompare() {
    setError("");
    setLoading(true);

    try {
      const texts = input
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);

      setResult(await compareTexts(texts));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  let xs = [];
  let ys = [];

  if (result) {
    xs = scale(result.points.map((p) => p.x), WIDTH);
    ys = scale(result.points.map((p) => -p.y), HEIGHT);
  }

  // closest pair, to give a one-line takeaway
  let closest = null;

  if (result) {
    const n = result.texts.length;

    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const score = result.similarity[i][j];

        if (!closest || score > closest.score) {
          closest = { i, j, score };
        }
      }
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>AI Workbench</h1>
        <p>Embeddings Visualizer</p>
      </header>

      <Nav />

      <main className="container">
        <section className="card">
          <h2>What is an embedding?</h2>
          <p className="lab-hint">
            An embedding turns text into a list of numbers (a vector) so
            that texts with similar <em>meaning</em> end up close together,
            even when they share no words. This is how RAG finds the right
            chunks. Type a few texts below, one per line. We embed each
            one with Gemini, then show how similar they are and plot them
            on a 2D map.
          </p>
        </section>

        <section className="card">
          <h2>1. Your texts (2 to 12, one per line)</h2>

          <div className="lab-presets">
            {Object.entries(PRESETS).map(([name, texts]) => (
              <button
                key={name}
                className="lab-chip"
                onClick={() => setInput(texts.join("\n"))}
              >
                {name}
              </button>
            ))}
          </div>

          <textarea
            rows={8}
            value={input}
            onChange={(event) => setInput(event.target.value)}
          />

          <button onClick={handleCompare} disabled={loading}>
            {loading ? "Embedding..." : "Compare"}
          </button>
        </section>

        {error && <div className="error">{error}</div>}

        {result && (
          <>
            <section className="card">
              <h2>2. The map</h2>

              <p className="lab-stats">
                Each text became a vector of{" "}
                <strong>{result.dimensions}</strong> numbers. The map
                squashes those down to 2 dimensions (PCA), so only the
                rough grouping is meaningful.
              </p>

              <svg
                viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
                className="lab-plot"
              >
                {result.texts.map((text, i) => (
                  <g key={i}>
                    <circle
                      cx={xs[i]}
                      cy={ys[i]}
                      r={6}
                      fill="#2563eb"
                    />
                    <text x={xs[i] + 10} y={ys[i] + 4} fontSize="12">
                      {shorten(text)}
                    </text>
                  </g>
                ))}
              </svg>

              {closest && (
                <p className="lab-hint">
                  Closest pair: &ldquo;{result.texts[closest.i]}&rdquo; and
                  &ldquo;{result.texts[closest.j]}&rdquo; (similarity{" "}
                  {closest.score.toFixed(2)}).
                </p>
              )}
            </section>

            <section className="card">
              <h2>3. Similarity scores</h2>

              <p className="lab-hint">
                Cosine similarity: 1.0 means the same direction (same
                meaning), lower means less related. Gemini embeddings
                rarely go near 0, so compare scores with each other rather
                than reading them as percentages.
              </p>

              <div className="lab-matrix-wrap">
                <table className="lab-matrix">
                  <thead>
                    <tr>
                      <th />
                      {result.texts.map((text, i) => (
                        <th key={i} title={text}>
                          {i + 1}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {result.texts.map((text, i) => (
                      <tr key={i}>
                        <th title={text}>
                          {i + 1}. {shorten(text)}
                        </th>

                        {result.similarity[i].map((score, j) => (
                          <td
                            key={j}
                            style={{ background: heat(score) }}
                          >
                            {score.toFixed(2)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
