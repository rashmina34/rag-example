"use client";

const SECTIONS = [
  {
    key: "system",
    title: "Instructions",
    hint: "Fixed rules that tell the model how to behave.",
    className: "prompt-system",
  },
  {
    key: "context",
    title: "Retrieved context",
    hint: "The chunks found by vector search. This is the 'R' in RAG.",
    className: "prompt-context",
  },
  {
    key: "question",
    title: "Your question",
    hint: "What you typed.",
    className: "prompt-question",
  },
];

export default function PromptViewer({ prompt }) {
  return (
    <div>
      <p className="lab-hint">
        A RAG answer is just a normal LLM call. The model never searches
        your documents itself. It only sees this one text, built from
        three parts.
      </p>

      {SECTIONS.map((section) => (
        <div key={section.key} className={`prompt-block ${section.className}`}>
          <div className="prompt-block-title">
            <strong>{section.title}</strong>
            <span>{section.hint}</span>
          </div>

          <pre>{prompt[section.key]}</pre>
        </div>
      ))}

      <details className="prompt-raw">
        <summary>Show the exact raw text sent</summary>
        <pre>{prompt.full}</pre>
      </details>
    </div>
  );
}
