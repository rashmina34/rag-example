"use client";

import { useEffect, useState } from "react";
import {
  deleteEvaluationRun,
  listEvaluationRuns,
  runEvaluation,
  uploadDocument,
} from "../api";
import Nav from "../components/Nav";

const STORAGE_KEY = "ai-workbench-eval-cases";

const EMPTY_CASE = { question: "", reference_answer: "", evidence: "" };

// Matches docs/test.txt in the repo. The last case is a trap: the answer
// is not in the document, so a good system should say so.
const SAMPLE_CASES = [
  {
    question: "What are large language models trained on?",
    reference_answer: "They are trained on large amounts of text.",
    evidence: "trained on large amounts of text",
  },
  {
    question: "What do embeddings let applications do?",
    reference_answer:
      "They let applications compare the semantic meaning of different pieces of text.",
    evidence: "compare the semantic meaning",
  },
  {
    question: "What do vector databases do?",
    reference_answer:
      "They store embeddings and allow applications to search for similar information efficiently.",
    evidence: "store embeddings",
  },
  {
    question: "How does retrieval augmented generation work?",
    reference_answer:
      "A system first retrieves relevant information and then gives it to a language model as context.",
    evidence: "retrieves relevant information",
  },
  {
    question: "Who invented the transformer architecture?",
    reference_answer:
      "The documents do not say. The answer should say the information is not available.",
    evidence: "",
  },
];

const METRICS = [
  {
    key: "hit_rate",
    title: "Hit rate",
    hint: "How often the right chunk was retrieved at all. If this is low, fix retrieval first: no prompt can answer from a chunk the model never saw.",
  },
  {
    key: "mrr",
    title: "MRR",
    hint: "Mean reciprocal rank. 1.0 means the right chunk was always ranked first, 0.5 means second on average.",
  },
  {
    key: "correctness",
    title: "Correctness",
    hint: "How often an AI judge says the answer matches your expected answer.",
  },
  {
    key: "faithfulness",
    title: "Faithfulness",
    hint: "How often every claim in the answer is backed by the retrieved chunks. A low score means the model is making things up.",
  },
];

function percent(value) {
  return value === null || value === undefined
    ? "–"
    : `${Math.round(value * 100)}%`;
}

function mrrText(value) {
  return value === null || value === undefined ? "–" : value.toFixed(2);
}

function metricText(key, value) {
  return key === "mrr" ? mrrText(value) : percent(value);
}

function loadCases() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (Array.isArray(saved) && saved.length) return saved;
  } catch {
    // ignore; fall back to the sample
  }
  return SAMPLE_CASES;
}

export default function Evaluation() {
  const [cases, setCases] = useState(SAMPLE_CASES);
  const [loaded, setLoaded] = useState(false);

  const [file, setFile] = useState(null);
  const [chunkSize, setChunkSize] = useState(500);
  const [chunkOverlap, setChunkOverlap] = useState(50);
  const [document, setDocument] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [label, setLabel] = useState("");
  const [topK, setTopK] = useState(3);
  const [mode, setMode] = useState("retrieval");

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [runs, setRuns] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect */
    setCases(loadCases());
    setLoaded(true);
    /* eslint-enable react-hooks/set-state-in-effect */

    listEvaluationRuns().then(setRuns).catch(() => {});
  }, []);

  useEffect(() => {
    if (!loaded) return;

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cases));
    } catch {
      // storage can be blocked; the page still works
    }
  }, [cases, loaded]);

  function updateCase(index, field, value) {
    setCases((current) =>
      current.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      )
    );
  }

  async function handleUpload() {
    if (!file) {
      setError("Choose a .txt file first.");
      return;
    }

    setError("");
    setUploading(true);

    try {
      const uploaded = await uploadDocument(file, chunkSize, chunkOverlap);

      setDocument({ ...uploaded, chunkSize, chunkOverlap });
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleRun() {
    const filled = cases.filter((item) => item.question.trim());

    if (!filled.length) {
      setError("Add at least one question.");
      return;
    }

    setError("");
    setRunning(true);
    setResult(null);

    try {
      const data = await runEvaluation({
        label,
        mode,
        top_k: topK,
        document_id: document?.document_id || null,
        chunk_size: document?.chunkSize ?? null,
        chunk_overlap: document?.chunkOverlap ?? null,
        cases: filled,
      });

      setResult(data);
      setRuns(await listEvaluationRuns());
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  async function handleDeleteRun(id) {
    try {
      await deleteEvaluationRun(id);
      setRuns((current) => current.filter((run) => run.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  // best value per metric column, to highlight in the history table
  const best = {};

  METRICS.forEach(({ key }) => {
    const values = runs
      .map((run) => run[key])
      .filter((value) => value !== null && value !== undefined);

    best[key] = values.length ? Math.max(...values) : null;
  });

  return (
    <div className="app">
      <header className="header">
        <h1>AI Workbench</h1>
        <p>RAG Evaluation</p>
      </header>

      <Nav />

      <main className="container">
        <section className="card">
          <h2>Why evaluate?</h2>

          <p className="lab-hint">
            A RAG demo that works on one question proves nothing. To know
            whether a change helps (a different chunk size, a bigger top
            K), you need a fixed set of questions with known answers and a
            score you can compare between runs. That is what this page
            does.
          </p>

          <ol className="lab-hint">
            <li>Upload a document (you choose how it is chunked).</li>
            <li>
              Write test questions. For each one give the{" "}
              <strong>evidence</strong>, a phrase that must appear in the
              chunk holding the answer, and the{" "}
              <strong>expected answer</strong>.
            </li>
            <li>
              Run it. Start with <em>retrieval only</em>: it is fast,
              free of generation calls, and tells you whether the right
              chunk is found. Then try <em>full</em> to also grade the
              generated answers.
            </li>
            <li>
              Change one thing, run again, and compare the runs in the
              history table.
            </li>
          </ol>
        </section>

        <section className="card">
          <h2>1. Document</h2>

          <p className="lab-hint">
            Upload the document the questions are about, with the chunk
            settings you want to test. Skip this to test against every
            document already uploaded.
          </p>

          <input
            type="file"
            accept=".txt"
            onChange={(event) => setFile(event.target.files[0])}
          />

          <div className="eval-row">
            <label>
              Chunk size
              <input
                type="number"
                min={20}
                max={5000}
                value={chunkSize}
                onChange={(event) => setChunkSize(Number(event.target.value))}
              />
            </label>

            <label>
              Overlap
              <input
                type="number"
                min={0}
                max={chunkSize - 1}
                value={chunkOverlap}
                onChange={(event) =>
                  setChunkOverlap(Number(event.target.value))
                }
              />
            </label>

            <button onClick={handleUpload} disabled={uploading}>
              {uploading ? "Processing..." : "Upload"}
            </button>
          </div>

          {document ? (
            <div className="success">
              <strong>{document.filename}</strong> uploaded as{" "}
              {document.chunk_count} chunks (size {document.chunkSize},
              overlap {document.chunkOverlap}). Runs use this document
              only.
            </div>
          ) : (
            <p className="lab-hint">
              No document selected: runs search every uploaded document.
            </p>
          )}
        </section>

        <section className="card">
          <h2>2. Test questions</h2>

          <div className="chat-toolbar">
            <button
              className="lab-chip"
              onClick={() => setCases(SAMPLE_CASES)}
            >
              Load sample (for docs/test.txt)
            </button>

            <button
              className="lab-chip"
              onClick={() => setCases([...cases, { ...EMPTY_CASE }])}
            >
              Add question
            </button>
          </div>

          {cases.map((item, index) => (
            <div className="source eval-case" key={index}>
              <div className="source-header">
                <strong>Question {index + 1}</strong>

                <button
                  className="lab-chip"
                  onClick={() =>
                    setCases(cases.filter((_, i) => i !== index))
                  }
                >
                  Remove
                </button>
              </div>

              <label>
                Question
                <textarea
                  rows={2}
                  value={item.question}
                  onChange={(event) =>
                    updateCase(index, "question", event.target.value)
                  }
                />
              </label>

              <label>
                Expected answer (used by the AI judge in full mode)
                <textarea
                  rows={2}
                  value={item.reference_answer}
                  onChange={(event) =>
                    updateCase(index, "reference_answer", event.target.value)
                  }
                />
              </label>

              <label>
                Evidence: a phrase copied from the chunk that holds the
                answer (leave empty if the answer is not in the document)
                <input
                  type="text"
                  className="eval-input"
                  value={item.evidence}
                  onChange={(event) =>
                    updateCase(index, "evidence", event.target.value)
                  }
                />
              </label>
            </div>
          ))}
        </section>

        <section className="card">
          <h2>3. Run</h2>

          <div className="eval-row">
            <label>
              Label (to recognise this run later)
              <input
                type="text"
                className="eval-input"
                value={label}
                placeholder="e.g. chunk 200, top 3"
                onChange={(event) => setLabel(event.target.value)}
              />
            </label>

            <label>
              Top K
              <input
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
              />
            </label>
          </div>

          <div className="eval-modes">
            <label>
              <input
                type="radio"
                checked={mode === "retrieval"}
                onChange={() => setMode("retrieval")}
              />{" "}
              <strong>Retrieval only</strong>: is the right chunk found?
              Fast, one embedding per question.
            </label>

            <label>
              <input
                type="radio"
                checked={mode === "full"}
                onChange={() => setMode("full")}
              />{" "}
              <strong>Full</strong>: also generate each answer and grade
              it with an AI judge.
            </label>
          </div>

          {mode === "full" && (
            <p className="chat-notice">
              Full mode makes 2 model calls per question. Free Gemini keys
              allow about 5 calls a minute, so a run of 5 questions can
              take a few minutes. The page waits and retries when the
              limit is hit.
            </p>
          )}

          <button onClick={handleRun} disabled={running}>
            {running ? "Running..." : "Run evaluation"}
          </button>
        </section>

        {error && <div className="error">{error}</div>}

        {result && (
          <section className="card">
            <h2>Results</h2>

            <div className="eval-tiles">
              {METRICS.map(({ key, title, hint }) => (
                <div className="eval-tile" key={key} title={hint}>
                  <span>{title}</span>
                  <strong>{metricText(key, result[key])}</strong>
                </div>
              ))}
            </div>

            <ul className="lab-hint">
              {METRICS.filter(
                ({ key }) =>
                  result[key] !== null && result[key] !== undefined
              ).map(({ key, title, hint }) => (
                <li key={key}>
                  <strong>{title}:</strong> {hint}
                </li>
              ))}
            </ul>

            {result.results.map((item, index) => {
              const hasEvidence = item.evidence.trim() !== "";

              return (
                <div className="source" key={index}>
                  <div className="source-header">
                    <strong>
                      {index + 1}. {item.question}
                    </strong>
                  </div>

                  {item.error ? (
                    <p className="eval-bad">Error: {item.error}</p>
                  ) : (
                    <div className="eval-badges">
                      {hasEvidence && (
                        <span
                          className={
                            item.retrieved_rank ? "eval-ok" : "eval-bad"
                          }
                        >
                          {item.retrieved_rank
                            ? `Right chunk found at rank ${item.retrieved_rank}`
                            : "Right chunk NOT retrieved"}
                        </span>
                      )}

                      {item.correct !== null && (
                        <span className={item.correct ? "eval-ok" : "eval-bad"}>
                          {item.correct ? "Correct" : "Incorrect"}
                        </span>
                      )}

                      {item.faithful !== null && (
                        <span className={item.faithful ? "eval-ok" : "eval-bad"}>
                          {item.faithful ? "Faithful" : "Not faithful"}
                        </span>
                      )}
                    </div>
                  )}

                  {item.answer && (
                    <div className="source-text">
                      <strong>Answer:</strong> {item.answer}
                    </div>
                  )}

                  {item.judge_reason && (
                    <p className="lab-hint">Judge: {item.judge_reason}</p>
                  )}
                </div>
              );
            })}
          </section>
        )}

        <section className="card">
          <h2>Past runs</h2>

          {runs.length === 0 ? (
            <p className="lab-hint">
              No runs yet. Run an evaluation, change one setting, run again,
              and compare here. The best score in each column is
              highlighted.
            </p>
          ) : (
            <div className="lab-matrix-wrap">
              <table className="lab-matrix eval-history">
                <thead>
                  <tr>
                    <th>Run</th>
                    <th>Mode</th>
                    <th>Chunk</th>
                    <th>Top K</th>
                    {METRICS.map(({ key, title }) => (
                      <th key={key}>{title}</th>
                    ))}
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id}>
                      <td>
                        {run.label || "(no label)"}
                        <br />
                        <small>
                          {new Date(run.created_at + "Z").toLocaleString()}
                        </small>
                      </td>
                      <td>{run.mode}</td>
                      <td>
                        {run.chunk_size
                          ? `${run.chunk_size} / ${run.chunk_overlap}`
                          : "–"}
                      </td>
                      <td>{run.top_k}</td>
                      {METRICS.map(({ key }) => (
                        <td
                          key={key}
                          className={
                            run[key] !== null &&
                            run[key] === best[key] &&
                            runs.length > 1
                              ? "eval-best"
                              : ""
                          }
                        >
                          {metricText(key, run[key])}
                        </td>
                      ))}
                      <td>
                        <button
                          className="lab-chip"
                          onClick={() => handleDeleteRun(run.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
