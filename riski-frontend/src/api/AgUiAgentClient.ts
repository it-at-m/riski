import type Document from "@/types/Document";
import type Proposal from "@/types/Proposal";
import type RiskiAnswer from "@/types/RiskiAnswer";
import type { ExecutionStep, ToolCallResult } from "@/types/RiskiAnswer";
import type { AgentSubscriber } from "@ag-ui/client";
import type { Message } from "@ag-ui/core";

import { HttpAgent } from "@ag-ui/client";

import { getAPIBaseURL, RISKI_AGENT_ENDPOINT } from "@/util/constants";

// -- Utilities ----------------------------------------------------------------

const buildUrl = () => `${getAPIBaseURL()}${RISKI_AGENT_ENDPOINT}`;

const generateId = (): string => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `riski-${Math.random().toString(36).slice(2, 12)}`;
};

type AnswerUpdateCallback = (answer: RiskiAnswer) => void;

// -- Extract assistant text from AG-UI messages -------------------------------

type TextFragment = { type: string; text?: unknown };

const isTextFragment = (v: unknown): v is TextFragment =>
  typeof v === "object" &&
  v !== null &&
  "type" in v &&
  typeof (v as Record<string, unknown>).type === "string";

const extractAssistantResponse = (messages: Message[]): string => {
  const msg = [...messages].reverse().find((m) => m.role === "assistant");
  if (!msg) return "";

  const content: unknown = msg.content;
  if (typeof content === "string") return content;

  if (Array.isArray(content)) {
    return content
      .map((f: unknown) => {
        if (typeof f === "string") return f;
        if (
          isTextFragment(f) &&
          f.type === "text" &&
          typeof f.text === "string"
        )
          return f.text;
        return "";
      })
      .filter((v: string) => v.length > 0)
      .join("\n");
  }
  return "";
};

// -- Parse the JSON response the backend streams as text ----------------------

const isRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null;

const pickString = (...values: unknown[]): string => {
  for (const v of values) {
    if (typeof v === "string" && v) return v;
    if (typeof v === "number") return v.toString();
  }
  return "";
};

const mapDocument = (raw: Record<string, unknown>): Document => {
  const m = isRecord(raw.metadata)
    ? (raw.metadata as Record<string, unknown>)
    : undefined;
  return {
    name:
      pickString(m?.title, m?.name, raw.title, raw.name, raw.id) || "Dokument",
    risUrl: pickString(
      m?.risUrl,
      m?.source, // Sometimes source is the URL
      m?.id, // Sometimes metadata.id is the URL (e.g. from retrieval)
      raw.risUrl,
      raw.source,
      raw.id
    ),
    size:
      typeof m?.size === "number"
        ? m.size
        : typeof raw.size === "number"
          ? raw.size
          : 0,
    identifier: pickString(m?.identifier, raw.identifier, raw.id),
  };
};

const mapProposal = (raw: Record<string, unknown>): Proposal => {
  const m = isRecord(raw.metadata)
    ? (raw.metadata as Record<string, unknown>)
    : undefined;
  return {
    name: pickString(m?.title, m?.name, raw.title, raw.name) || "",
    identifier: pickString(m?.identifier, m?.id, raw.identifier, raw.id),
    risUrl: pickString(m?.risUrl, m?.source, raw.risUrl, raw.source),
  };
};

// -- Extract documents/proposals from on_tool_end event data ------------------

/**
 * Extract documents and proposals from the `on_tool_end` event data.
 *
 * The backend's `strip_tool_end_payload` replaces the raw tool output with a
 * lightweight JSON-serialisable summary shaped like:
 *   { documents: [{ id, metadata }], proposals: [{ identifier, name, risUrl }] }
 */
const parseToolOutput = (
  data: Record<string, unknown> | undefined
): ToolCallResult | undefined => {
  const output = data?.output;
  if (!isRecord(output)) return undefined;

  const documents: Document[] = [];
  const proposals: Proposal[] = [];

  if (Array.isArray(output.documents)) {
    for (const d of output.documents) {
      if (isRecord(d)) documents.push(mapDocument(d));
    }
  }
  if (Array.isArray(output.proposals)) {
    for (const p of output.proposals) {
      if (isRecord(p)) proposals.push(mapProposal(p));
    }
  }

  if (documents.length === 0 && proposals.length === 0) return undefined;
  return { documents, proposals };
};

/**
 * Parse the final text produced by the agent. The backend wraps everything
 * in a JSON object: {"response":"...","documents":[...],"proposals":[...]}.
 * If parsing fails we fall back to returning the raw text as the response.
 */
const parseResponseText = (
  text: string
): { response: string; documents: Document[]; proposals: Proposal[] } => {
  try {
    const json = JSON.parse(text);
    if (isRecord(json)) {
      return {
        response: typeof json.response === "string" ? json.response : "",
        documents: Array.isArray(json.documents)
          ? json.documents.filter(isRecord).map(mapDocument)
          : [],
        proposals: Array.isArray(json.proposals)
          ? json.proposals.filter(isRecord).map(mapProposal)
          : [],
      };
    }
  } catch {
    // Partial JSON while streaming: extract just the response field
    if (text.trimStart().startsWith("{")) {
      const match = text.match(/"response"\s*:\s*"((?:[^"\\]|\\.)*)(?:"|$)/);
      if (match?.[1]) {
        const response = match[1]
          .replace(/\\"/g, '"')
          .replace(/\\n/g, "\n")
          .replace(/\\\\/g, "\\");
        return { response, documents: [], proposals: [] };
      }
    }
  }
  return { response: text, documents: [], proposals: [] };
};

// -- Abort helper -------------------------------------------------------------

const createAbortController = (signal: AbortSignal): AbortController => {
  const controller = new AbortController();
  if (signal.aborted) {
    controller.abort(signal.reason);
  } else {
    signal.addEventListener("abort", () => controller.abort(signal.reason), {
      once: true,
    });
  }
  return controller;
};

// -- Build the answer object emitted to the UI --------------------------------

const buildAnswer = (
  text: string,
  status: string | undefined,
  steps: ExecutionStep[]
): RiskiAnswer => {
  const { response, documents, proposals } = parseResponseText(text);
  return {
    response:
      response || (status ? "" : "Unsere KI konnte keine Antwort generieren."),
    documents,
    proposals,
    status,
    steps,
  };
};

// -- Step display helpers -----------------------------------------------------

const statusLabelForStep = (stepName: string): string => {
  const labels: Record<string, string> = {
    model: "Denke nach...",
    tools: "Verwende Werkzeuge...",
    retrieve_documents: "Suche Dokumente...",
  };
  return labels[stepName] ?? `Verarbeite Schritt: ${stepName}`;
};

const displayNameForStep = (stepName: string): string | undefined => {
  if (stepName === "model") return "Denke nach";
  return undefined;
};

// -- Main client --------------------------------------------------------------

export default class AgUiAgentClient {
  static async ask(
    question: string,
    signal: AbortSignal,
    onProgress?: AnswerUpdateCallback
  ): Promise<RiskiAnswer> {
    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: question,
    };

    const agent = new HttpAgent({
      url: buildUrl(),
      threadId: generateId(),
      initialMessages: [userMessage],
    });

    const abortController = createAbortController(signal);
    let latestText = "";
    let latestStatus = "Initialisiere...";
    let steps: ExecutionStep[] = [];

    // -- Progress emission ----------------------------------------------------

    const emitProgress = () => {
      if (!onProgress || signal.aborted || abortController.signal.aborted)
        return;
      onProgress(
        buildAnswer(
          latestText || extractAssistantResponse(agent.messages),
          latestStatus,
          structuredClone(steps)
        )
      );
    };

    // -- Step / tool-call lookup -----------------------------------------------

    const currentStep = (): ExecutionStep | undefined =>
      steps.find((s) => s.status === "running");

    const findToolCall = (
      step: ExecutionStep,
      runId: string | undefined,
      toolName: string | undefined
    ) =>
      step.toolCalls?.find((tc) => {
        if (tc.status !== "running") return false;
        return runId ? tc.id === runId : tc.name === toolName;
      });

    // -- AG-UI subscriber -----------------------------------------------------

    const subscriber: AgentSubscriber = {
      onRunStartedEvent: () => {
        steps = [];
        emitProgress();
      },

      onStepStartedEvent: ({ event }) => {
        latestStatus = statusLabelForStep(event.stepName);
        steps.push({
          name: event.stepName,
          displayName: displayNameForStep(event.stepName),
          status: "running",
          toolCalls: [],
        });
        emitProgress();
      },

      onStepFinishedEvent: ({ event }) => {
        const step = steps
          .slice()
          .reverse()
          .find((s) => s.name === event.stepName && s.status === "running");
        if (step) step.status = "completed";
        emitProgress();
      },

      onTextMessageContentEvent: ({ textMessageBuffer }) => {
        latestText = textMessageBuffer;
        const step = currentStep();
        if (step?.name === "model") {
          step.displayName = "Antwort generieren";
          latestStatus = "Generiere Antwort...";
        }
        emitProgress();
      },

      onRawEvent: ({ event }) => {
        const raw = event.event as Record<string, unknown> | undefined;
        if (!raw || typeof raw !== "object") return;

        const eventName = raw.event as string | undefined;
        const data = raw.data as Record<string, unknown> | undefined;
        const toolName = raw.name as string | undefined;
        const runId = raw.run_id as string | undefined;

        if (eventName === "on_tool_start") {
          const step = currentStep();
          if (step) {
            if (!step.toolCalls) step.toolCalls = [];
            const input = data?.input as Record<string, unknown> | undefined;
            step.toolCalls.push({
              id: runId || generateId(),
              name: toolName || "unknown",
              args: typeof input?.query === "string" ? input.query : undefined,
              status: "running",
            });
            latestStatus = `Verwende Werkzeug: ${toolName || "unknown"}...`;
          }
          emitProgress();
        } else if (eventName === "on_tool_end") {
          const step = currentStep();
          if (step) {
            const tc = findToolCall(step, runId, toolName);
            if (tc) {
              tc.status = "completed";
              // Extract documents/proposals from tool output immediately
              const result = parseToolOutput(data);
              if (result) tc.result = result;
            }
          }
          latestStatus = "Werkzeug ausgeführt.";
          emitProgress();
        }
      },

      onRunFinishedEvent: () => {
        latestStatus = "";
        for (const step of steps) {
          if (step.status === "running") step.status = "completed";
          step.toolCalls?.forEach((tc) => {
            if (tc.status === "running") tc.status = "completed";
          });
        }
        latestText = extractAssistantResponse(agent.messages) || latestText;
        emitProgress();
      },

      onRunErrorEvent: () => {
        latestStatus = "Fehler aufgetreten.";
        for (const step of steps) {
          if (step.status === "running") step.status = "failed";
        }
        emitProgress();
      },

      // Unused AG-UI lifecycle hooks
      onStateDeltaEvent: () => {},
      onStateSnapshotEvent: () => {},
      onToolCallStartEvent: () => {},
      onToolCallEndEvent: () => {},
      onToolCallResultEvent: () => {},
    };

    // -- Execute --------------------------------------------------------------

    try {
      await agent.runAgent({ abortController }, subscriber);
      const responseText =
        latestText || extractAssistantResponse(agent.messages);
      return buildAnswer(responseText, latestStatus, steps);
    } catch (error) {
      console.error("Agent execution failed:", error);
      return buildAnswer(
        "Ein Fehler ist bei der Verarbeitung Ihrer Anfrage aufgetreten.",
        "Fehler",
        steps
      );
    } finally {
      abortController.abort();
    }
  }
}
