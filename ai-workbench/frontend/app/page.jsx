"use client";

import { useState } from "react";
import { uploadDocument, askQuestion } from "./api";

export default function App() {
  const [file, setFile] = useState(null);
  const [document, setDocument] = useState(null);

  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);

  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);

  const [error, setError] = useState("");

  async function handleUpload() {
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setError("");
    setUploading(true);

    try {
      const result = await uploadDocument(file);

      setDocument(result);
      setAnswer("");
      setSources([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk() {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    setError("");
    setAsking(true);

    try {
      const result = await askQuestion(
        question,
        topK,
        document?.document_id || null
      );

      setAnswer(result.answer);
      setSources(result.sources || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="app">

      <header className="header">
        <h1>AI Workbench</h1>
        <p>Document RAG Assistant</p>
      </header>


      <main className="container">

        {/* Upload Section */}

        <section className="card">
          <h2>1. Upload Document</h2>

          <input
            type="file"
            accept=".txt"
            onChange={(event) =>
              setFile(event.target.files[0])
            }
          />

          <button
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? "Processing..." : "Upload Document"}
          </button>

          {document && (
            <div className="success">
              <strong>{document.filename}</strong>

              <p>
                Characters: {document.characters}
              </p>

              <p>
                Chunks: {document.chunk_count}
              </p>

              <p>
                Document ID: {document.document_id}
              </p>
            </div>
          )}
        </section>


        {/* Question Section */}

        <section className="card">
          <h2>2. Ask a Question</h2>

          <textarea
            value={question}
            onChange={(event) =>
              setQuestion(event.target.value)
            }
            placeholder="Ask something about your document..."
            rows={5}
          />

          <div className="controls">

            <label>
              Top K:

              <select
                value={topK}
                onChange={(event) =>
                  setTopK(Number(event.target.value))
                }
              >
                <option value={1}>1</option>
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
              </select>
            </label>

            <button
              onClick={handleAsk}
              disabled={asking}
            >
              {asking ? "Thinking..." : "Ask"}
            </button>

          </div>
        </section>


        {/* Error */}

        {error && (
          <div className="error">
            {error}
          </div>
        )}


        {/* Answer */}

        {answer && (
          <section className="card">
            <h2>3. Answer</h2>

            <div className="answer">
              {answer}
            </div>
          </section>
        )}


        {/* Sources */}

        {sources.length > 0 && (
          <section className="card">
            <h2>4. Retrieved Sources</h2>

            {sources.map((source, index) => (
              <div
                className="source"
                key={`${source.filename}-${source.chunk_index}-${index}`}
              >
                <div className="source-header">
                  <strong>
                    Source {index + 1}
                  </strong>

                  <span>
                    Distance:{" "}
                    {source.distance.toFixed(4)}
                  </span>
                </div>

                <p>
                  File: {source.filename}
                </p>

                <p>
                  Chunk: {source.chunk_index}
                </p>

                <div className="source-text">
                  {source.text}
                </div>
              </div>
            ))}
          </section>
        )}

      </main>
    </div>
  );
}
