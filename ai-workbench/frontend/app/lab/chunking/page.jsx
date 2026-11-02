"use client";

import { useEffect, useState } from "react";
import { chunkText } from "../../api";
import Nav from "../../components/Nav";

const SAMPLE = `Artificial intelligence is a field of computer science that focuses on creating systems capable of performing tasks that normally require human intelligence.

Large language models are AI models trained on large amounts of text. They predict the next word, which lets them answer questions and write text.

Vector databases store embeddings and allow applications to search for similar meaning instead of exact words.`;

const COLORS = ["#fde68a", "#bfdbfe", "#bbf7d0", "#fbcfe8", "#ddd6fe"];

// Split the cleaned text into pieces so each character range is tagged
// with the chunks that cover it. Overlapping ranges get a darker mark.
function buildSegments(text, chunks) {
  const points = new Set([0, text.length]);

  chunks.forEach((chunk) => {
    points.add(chunk.start);
    points.add(chunk.end);
  });

  const sorted = [...points].sort((a, b) => a - b);

  return sorted.slice(0, -1).map((start, i) => {
    const end = sorted[i + 1];

    const covering = chunks.filter(
      (chunk) => chunk.start <= start && chunk.end >= end
    );

    return {
      text: text.slice(start, end),
      covering,
    };
  });
}

export default function ChunkingLab() {
  const [text, setText] = useState(SAMPLE);
  const [chunkSize, setChunkSize] = useState(200);
  const [chunkOverlap, setChunkOverlap] = useState(40);

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const data = await chunkText(text, chunkSize, chunkOverlap);
        setResult(data);
        setError("");
      } catch (err) {
        setError(err.message);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [text, chunkSize, chunkOverlap]);

  const segments = result
    ? buildSegments(result.cleaned_text, result.chunks)
    : [];

  return (
    <div className="app">
      <header className="header">
        <h1>AI Workbench</h1>
        <p>Chunking Lab</p>
      </header>

      <Nav />

      <main className="container">
        <section className="card">
          <h2>Why chunk?</h2>
          <p className="lab-hint">
            Models and vector search work best on small pieces of text.
            RAG splits a document into chunks, embeds each one, and later
            retrieves only the chunks that match the question. Chunks that
            are too big are vague, and chunks that are too small lose
            context. Overlap repeats a little text at each boundary so a
            sentence cut in half is still found. Change the sliders and
            watch what happens. No AI calls are made on this page.
          </p>
        </section>

        <section className="card">
          <h2>1. Your text</h2>

          <textarea
            rows={8}
            value={text}
            onChange={(event) => setText(event.target.value)}
          />

          <div className="lab-sliders">
            <label>
              Chunk size: <strong>{chunkSize}</strong> characters
              <input
                type="range"
                min={20}
                max={1000}
                step={10}
                value={chunkSize}
                onChange={(event) => {
                  const size = Number(event.target.value);
                  setChunkSize(size);
                  if (chunkOverlap >= size) setChunkOverlap(size - 10);
                }}
              />
            </label>

            <label>
              Overlap: <strong>{chunkOverlap}</strong> characters
              <input
                type="range"
                min={0}
                max={Math.max(chunkSize - 10, 0)}
                step={5}
                value={chunkOverlap}
                onChange={(event) =>
                  setChunkOverlap(Number(event.target.value))
                }
              />
            </label>
          </div>
        </section>

        {error && <div className="error">{error}</div>}

        {result && (
          <>
            <section className="card">
              <h2>2. Where the cuts happen</h2>

              <p className="lab-stats">
                {result.characters} characters &rarr;{" "}
                <strong>{result.chunk_count}</strong> chunks
              </p>

              <div className="chunk-text">
                {segments.map((segment, i) => {
                  const overlapping = segment.covering.length > 1;
                  const first = segment.covering[0];

                  return (
                    <span
                      key={i}
                      className={overlapping ? "chunk-mark overlap" : "chunk-mark"}
                      style={{
                        background: first
                          ? COLORS[first.index % COLORS.length]
                          : "transparent",
                      }}
                      title={segment.covering
                        .map((c) => `chunk ${c.index}`)
                        .join(" + ")}
                    >
                      {segment.text}
                    </span>
                  );
                })}
              </div>

              <p className="lab-hint">
                Colors show which chunk a piece of text belongs to. Text
                with a dashed underline is in the overlap, so it appears
                in two chunks.
              </p>
            </section>

            <section className="card">
              <h2>3. The chunks</h2>

              {result.chunks.map((chunk) => (
                <div
                  className="source"
                  key={chunk.index}
                  style={{
                    borderLeft: `6px solid ${
                      COLORS[chunk.index % COLORS.length]
                    }`,
                  }}
                >
                  <div className="source-header">
                    <strong>Chunk {chunk.index}</strong>
                    <span>
                      chars {chunk.start}&ndash;{chunk.end} &middot;{" "}
                      {chunk.length} long
                    </span>
                  </div>

                  <div className="source-text">{chunk.text}</div>
                </div>
              ))}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
