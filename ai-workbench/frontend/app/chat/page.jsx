"use client";

import { useEffect, useRef, useState } from "react";
import { streamChat } from "../api";
import Nav from "../components/Nav";

const STORAGE_KEY = "ai-workbench-chat";
const DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant.";

function loadSaved() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM_PROMPT);
  const [temperature, setTemperature] = useState(0.7);
  const [showSettings, setShowSettings] = useState(false);

  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState("");
  const [dropped, setDropped] = useState(0);

  const [loaded, setLoaded] = useState(false);

  const abortRef = useRef(null);
  const bottomRef = useRef(null);

  // restore the saved chat once, on the client
  useEffect(() => {
    const saved = loadSaved();

    /* eslint-disable react-hooks/set-state-in-effect */
    if (saved.messages) setMessages(saved.messages);
    if (saved.systemPrompt) setSystemPrompt(saved.systemPrompt);
    if (typeof saved.temperature === "number") setTemperature(saved.temperature);
    setLoaded(true);
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  useEffect(() => {
    if (!loaded) return;

    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ messages, systemPrompt, temperature })
      );
    } catch {
      // storage can be blocked; the chat still works without it
    }
  }, [messages, systemPrompt, temperature, loaded]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send `history` (ending with a user message) and stream the reply
  // into a new, empty assistant message.
  async function run(history) {
    setError("");
    setDropped(0);
    setStreaming(true);

    setMessages([...history, { role: "assistant", content: "" }]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await streamChat({
        messages: history,
        systemPrompt,
        temperature,
        signal: controller.signal,
        onText: (text) =>
          setMessages((current) => {
            const next = [...current];
            const last = next[next.length - 1];

            next[next.length - 1] = {
              ...last,
              content: last.content + text,
            };

            return next;
          }),
      });

      setDropped(result.dropped);
    } catch (err) {
      if (err.name !== "AbortError") setError(err.message);
    } finally {
      setStreaming(false);
      abortRef.current = null;

      // drop an assistant bubble that never received any text
      setMessages((current) =>
        current.length && current[current.length - 1].content === ""
          ? current.slice(0, -1)
          : current
      );
    }
  }

  function handleSend() {
    const text = input.trim();

    if (!text || streaming) return;

    setInput("");
    run([...messages, { role: "user", content: text }]);
  }

  function handleRegenerate() {
    if (streaming) return;

    const last = messages.length - 1;

    // remove the last answer, then ask again
    if (last >= 0 && messages[last].role === "assistant") {
      run(messages.slice(0, last));
    } else if (last >= 0) {
      // the last turn failed before any answer; retry it
      run(messages);
    }
  }

  function handleNewChat() {
    abortRef.current?.abort();
    setMessages([]);
    setError("");
    setDropped(0);
  }

  const canRegenerate = !streaming && messages.length > 0;

  return (
    <div className="app">
      <header className="header">
        <h1>AI Workbench</h1>
        <p>Chat</p>
      </header>

      <Nav />

      <main className="container chat-container">
        <section className="card chat-card">
          <div className="chat-toolbar">
            <button className="lab-chip" onClick={handleNewChat}>
              New chat
            </button>

            <button
              className="lab-chip"
              onClick={() => setShowSettings((value) => !value)}
            >
              {showSettings ? "Hide settings" : "Settings"}
            </button>
          </div>

          {showSettings && (
            <div className="chat-settings">
              <label>
                System prompt
                <p className="lab-hint">
                  Hidden instructions that shape every answer. Try
                  &ldquo;You are a pirate&rdquo; and keep chatting.
                </p>
                <textarea
                  rows={3}
                  value={systemPrompt}
                  onChange={(event) => setSystemPrompt(event.target.value)}
                />
              </label>

              <label>
                Temperature: <strong>{temperature.toFixed(1)}</strong>
                <p className="lab-hint">
                  Low is focused and repeatable. High is more creative and
                  less predictable.
                </p>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.1}
                  value={temperature}
                  onChange={(event) =>
                    setTemperature(Number(event.target.value))
                  }
                />
              </label>
            </div>
          )}

          <div className="chat-messages">
            {messages.length === 0 && (
              <p className="lab-hint chat-empty">
                Say something to start. The model has no memory of its own:
                every time you send a message, this page sends the whole
                conversation again, which is how it &ldquo;remembers&rdquo;
                earlier turns.
              </p>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`chat-row ${message.role}`}
              >
                <div className="chat-bubble">
                  {message.content}
                  {streaming &&
                    index === messages.length - 1 &&
                    message.role === "assistant" && (
                      <span className="chat-cursor" />
                    )}
                </div>
              </div>
            ))}

            <div ref={bottomRef} />
          </div>

          {dropped > 0 && (
            <p className="chat-notice">
              This chat is long, so the {dropped} oldest message
              {dropped === 1 ? " was" : "s were"} left out of the last
              request. The model can no longer see{" "}
              {dropped === 1 ? "it" : "them"}.
            </p>
          )}

          {error && <div className="error">{error}</div>}

          <div className="chat-input">
            <textarea
              rows={2}
              value={input}
              placeholder="Type a message. Enter to send, Shift+Enter for a new line."
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
            />

            <div className="chat-buttons">
              {streaming ? (
                <button onClick={() => abortRef.current?.abort()}>
                  Stop
                </button>
              ) : (
                <button onClick={handleSend} disabled={!input.trim()}>
                  Send
                </button>
              )}

              <button
                className="lab-chip"
                onClick={handleRegenerate}
                disabled={!canRegenerate}
              >
                Regenerate
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
