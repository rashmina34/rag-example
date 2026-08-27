"use client";

import { useState, useEffect } from "react";

const API_URL = "http://localhost:8000";

type WorkflowStep = {
  id: string;
  name: string;
  type: "prompt";
  system_prompt: string;
  prompt: string;
  temperature: number;
};

const initialSteps: WorkflowStep[] = [
  {
    id: "step1",
    name: "Analyze Topic",
    type: "prompt",
    system_prompt:
      "You are an expert AI analyst.",
    prompt:
      "Analyze this topic:\n\n{{input}}\n\nIdentify the key concepts and difficulty level.",
    temperature: 0.3,
  },
  {
    id: "step2",
    name: "Generate Explanation",
    type: "prompt",
    system_prompt:
      "You are an expert teacher.",
    prompt:
      "Using this analysis:\n\n{{step1.output}}\n\nExplain the topic to a beginner.",
    temperature: 0.7,
  },
  {
    id: "step3",
    name: "Create Summary",
    type: "prompt",
    system_prompt:
      "You create concise educational summaries.",
    prompt:
      "Summarize this explanation in exactly 5 bullet points:\n\n{{step2.output}}",
    temperature: 0.3,
  },
];

export default function Home() {

  const [workflowName, setWorkflowName] =
    useState("AI Learning Pipeline");

  const [input, setInput] =
    useState("Vector databases");

  const [steps, setSteps] =
    useState<WorkflowStep[]>(initialSteps);

  const [result, setResult] =
    useState<any>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [workflows, setWorkflows] =
    useState<any[]>([]);

  const [selectedWorkflowId, setSelectedWorkflowId] =
    useState("");

  function updateStep(
    index: number,
    field: keyof WorkflowStep,
    value: string | number
  ) {

    setSteps((current) => {

      const updated = [...current];

      updated[index] = {
        ...updated[index],
        [field]: value,
      };

      return updated;
    });
  }

  async function loadWorkflows() {

    const response = await fetch(
      `${API_URL}/api/workflows`
    );

    const data = await response.json();

    setWorkflows(data);

    if (data.length > 0) {
      setSelectedWorkflowId(data[0].id);
    }
  }

  async function runWorkflow() {

    if (!selectedWorkflowId) {
      setError(
        "Save or select a workflow first."
      );

      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {

      const response = await fetch(
        `${API_URL}/api/workflows/${selectedWorkflowId}/execute`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            input,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Execution failed: ${response.status}`
        );
      }

      const data = await response.json();

      setResult(data);

    } catch (error) {

      console.error(error);

      setError(
        error instanceof Error
          ? error.message
          : "Workflow execution failed."
      );

    } finally {

      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkflows();
  }, []);

  async function saveWorkflow() {

    setError("");

    try {

      const response = await fetch(
        `${API_URL}/api/workflows`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            id: "learning-new-pipeline",
            name: workflowName,
            description:
              "AI learning pipeline",
            steps,
          }),
        }
      );

      if (!response.ok) {

        const error =
          await response.json();

        throw new Error(
          error.detail ||
          "Failed to save workflow"
        );
      }

      await loadWorkflows();

    } catch (error) {

      setError(
        error instanceof Error
          ? error.message
          : "Failed to save workflow"
      );
    }
  }

  return (
    <main className="min-h-screen bg-gray-100">

      <header className="border-b bg-white">

        <div className="mx-auto max-w-7xl px-6 py-5">

          <h1 className="text-2xl font-bold">
            AI Workbench
          </h1>

          <p className="text-sm text-gray-500">
            Milestone 3 — Prompt Orchestration
          </p>

        </div>

      </header>

      <div className="mx-auto max-w-7xl p-6">

        <div className="grid gap-6 lg:grid-cols-2">

          {/* WORKFLOW */}

          <section className="rounded-xl border bg-white shadow-sm">

            <div className="border-b p-6">

              <h2 className="text-lg font-semibold">
                Workflow Builder
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                Connect multiple prompt steps together.
              </p>

            </div>

            <div className="space-y-6 p-6">

              <div>

                <label className="mb-2 block text-sm font-medium">
                  Workflow Name
                </label>

                <input
                  value={workflowName}
                  onChange={(e) =>
                    setWorkflowName(e.target.value)
                  }
                  className="w-full rounded-lg border p-3 text-sm"
                />

              </div>

              <div>

                <label className="mb-2 block text-sm font-medium">
                  Workflow Input
                </label>

                <textarea
                  value={input}
                  onChange={(e) =>
                    setInput(e.target.value)
                  }
                  rows={3}
                  className="w-full rounded-lg border p-3 text-sm"
                />

              </div>

              {steps.map((step, index) => (

                <div key={step.id}>

                  <div className="mb-2 text-center text-gray-400">
                    {index > 0 && "↓"}
                  </div>

                  <div className="rounded-xl border-2 border-gray-200 p-5">

                    <div className="mb-4 flex items-center gap-3">

                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-black text-sm font-bold text-white">
                        {index + 1}
                      </span>

                      <h3 className="font-semibold">
                        {step.name}
                      </h3>

                    </div>

                    <label className="mb-2 block text-xs font-medium uppercase text-gray-500">
                      Step Name
                    </label>

                    <input
                      value={step.name}
                      onChange={(e) =>
                        updateStep(
                          index,
                          "name",
                          e.target.value
                        )
                      }
                      className="mb-4 w-full rounded-lg border p-3 text-sm"
                    />

                    <label className="mb-2 block text-xs font-medium uppercase text-gray-500">
                      System Prompt
                    </label>

                    <textarea
                      value={step.system_prompt}
                      onChange={(e) =>
                        updateStep(
                          index,
                          "system_prompt",
                          e.target.value
                        )
                      }
                      rows={3}
                      className="mb-4 w-full rounded-lg border p-3 text-sm"
                    />

                    <label className="mb-2 block text-xs font-medium uppercase text-gray-500">
                      Prompt
                    </label>

                    <textarea
                      value={step.prompt}
                      onChange={(e) =>
                        updateStep(
                          index,
                          "prompt",
                          e.target.value
                        )
                      }
                      rows={6}
                      className="w-full rounded-lg border p-3 font-mono text-sm"
                    />

                    <div className="mt-4">

                      <label className="mb-2 block text-xs font-medium uppercase text-gray-500">
                        Temperature:{" "}
                        {step.temperature}
                      </label>

                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={step.temperature}
                        onChange={(e) =>
                          updateStep(
                            index,
                            "temperature",
                            Number(e.target.value)
                          )
                        }
                        className="w-full"
                      />

                    </div>

                  </div>

                </div>

              ))}

              <button
                onClick={runWorkflow}
                disabled={loading}
                className="w-full rounded-lg bg-black px-5 py-3 font-medium text-white disabled:bg-gray-400"
              >
                {loading
                  ? "Running Workflow..."
                  : "Run Workflow"}
              </button>

              <button
                onClick={saveWorkflow}
                className="rounded-lg border px-5 py-3 font-medium"
              >
                Save Workflow
              </button>
              {error && (

                <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  {error}
                </div>

              )}

            </div>

          </section>

          {/* RESULTS */}

          <section className="rounded-xl border bg-white shadow-sm">

            <div className="border-b p-6">

              <h2 className="text-lg font-semibold">
                Workflow Execution
              </h2>

            </div>

            <div className="p-6">

              {!result && !loading && (

                <div className="flex min-h-[500px] items-center justify-center text-center">

                  <div>

                    <div className="mb-4 text-4xl">
                      ⚡
                    </div>

                    <p className="font-medium">
                      Workflow not executed
                    </p>

                    <p className="mt-2 text-sm text-gray-500">
                      Configure your steps and run the workflow.
                    </p>

                  </div>

                </div>

              )}

              {loading && (

                <div className="flex min-h-[500px] items-center justify-center">

                  <div className="text-center">

                    <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-black" />

                    <p className="text-sm text-gray-500">
                      Executing workflow...
                    </p>

                  </div>

                </div>

              )}

              {result && (

                <div className="space-y-5">

                  {result.steps.map(
                    (step: any, index: number) => (

                      <div
                        key={step.step_id}
                        className="rounded-lg border p-4"
                      >

                        <div className="mb-3 flex items-center gap-3">

                          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium">
                            Step {index + 1}
                          </span>

                          <span className="font-medium">
                            {step.step_name}
                          </span>

                        </div>

                        <div className="whitespace-pre-wrap rounded bg-gray-50 p-3 text-sm">
                          {step.output}
                        </div>

                      </div>

                    )
                  )}

                  <div>

                    <h3 className="mb-3 font-semibold">
                      Final Output
                    </h3>

                    <div className="whitespace-pre-wrap rounded-lg bg-black p-5 text-sm leading-7 text-white">
                      {result.output}
                    </div>

                  </div>

                </div>

              )}

            </div>

          </section>

        </div>

      </div>

    </main>
  );
}