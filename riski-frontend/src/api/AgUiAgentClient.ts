import type Document from "@/types/Document";
import type Proposal from "@/types/Proposal";
import type RiskiAnswer from "@/types/RiskiAnswer";
import type {
  ErrorInfo,
  ExecutionStep,
  ToolCallResult,
} from "@/types/RiskiAnswer";
import type { AgentSubscriber } from "@ag-ui/client";
import type { Message, StateSnapshotEvent } from "@ag-ui/core";

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
      m?.source,
      m?.id,
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
  steps: ExecutionStep[],
  errorInfo?: ErrorInfo
): RiskiAnswer => {
  const { response, documents, proposals } = parseResponseText(text);
  return {
    response:
      response || (status ? "" : "Unsere KI konnte keine Antwort generieren."),
    documents,
    proposals,
    status,
    steps,
    errorInfo,
  };
};

// -- Step display helpers -----------------------------------------------------

const statusLabelForStep = (stepName: string): string => {
  const labels: Record<string, string> = {
    model: "Denke nach...",
    tools: "Verwende Werkzeuge...",
    guard: "Prüfe Ergebnisse...",
    retrieve_documents: "Suche Dokumente...",
  };
  return labels[stepName] ?? `Verarbeite Schritt: ${stepName}`;
};

const displayNameForStep = (stepName: string): string | undefined => {
  if (stepName === "model") return "Denke nach";
  if (stepName === "guard") return "Ergebnisse prüfen";
  return undefined;
};

// -- Tracked-state snapshot types (mirrors backend slim shapes) ---------------

/** Slim TrackedDocument as sent by the backend (page_content stripped). */
interface TrackedDocumentSnapshot {
  id: string;
  metadata: Record<string, unknown>;
  is_checked: boolean;
  is_relevant: boolean;
  relevance_reason: string;
}

/** TrackedProposal as sent by the backend. */
interface TrackedProposalSnapshot {
  identifier: string;
  name: string;
  risUrl: string;
}

/** The shape of snapshot.snapshot after backend stripping. */
interface AgentStateSnapshot {
  tracked_documents: TrackedDocumentSnapshot[];
  tracked_proposals: TrackedProposalSnapshot[];
  user_query: string;
  messages: unknown[];
  error_info?: {
    error_type: string;
    message: string;
    details?: Record<string, unknown>;
  } | null;
}

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
    let latestErrorInfo: ErrorInfo | undefined;

    // -- Previous snapshot for diffing ----------------------------------------
    let prevDocs: TrackedDocumentSnapshot[] = [];
    let prevProposals: TrackedProposalSnapshot[] = [];
    let prevUserQuery = "";

    // -- Progress emission ----------------------------------------------------

    const emitProgress = () => {
      if (!onProgress || signal.aborted || abortController.signal.aborted)
        return;
      onProgress(
        buildAnswer(
          latestText || extractAssistantResponse(agent.messages),
          latestStatus,
          structuredClone(steps),
          latestErrorInfo ? structuredClone(latestErrorInfo) : undefined
        )
      );
    };

    // -- Step / tool-call lookup -----------------------------------------------

    const currentStep = (): ExecutionStep | undefined =>
      steps.find((s) => s.status === "running");

    // -- AG-UI subscriber -----------------------------------------------------

    const subscriber: AgentSubscriber = {
      onRunStartedEvent: () => {
        steps = [];
        prevDocs = [];
        prevProposals = [];
        prevUserQuery = "";
        latestErrorInfo = undefined;
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
        } else if (step?.name === "guard") {
          step.displayName = "Ergebnisse prüfen";
          latestStatus = "Prüfe Ergebnisse...";
        }
        emitProgress();
      },

      // -- Derive tool calls & document checks from state snapshot diffs ------
      onStateSnapshotEvent: ({ event }: { event: StateSnapshotEvent }) => {
        const snap = event.snapshot as AgentStateSnapshot | undefined;
        if (!snap) return;

        const docs: TrackedDocumentSnapshot[] = snap.tracked_documents ?? [];
        const proposals: TrackedProposalSnapshot[] =
          snap.tracked_proposals ?? [];
        const userQuery = snap.user_query ?? "";

        const step = currentStep();
        let changed = false;

        // -- user_query changed -----------------------------------------------
        if (userQuery && userQuery !== prevUserQuery) {
          prevUserQuery = userQuery;
          changed = true;
        }

        // -- Detect newly appeared documents (tool result) --------------------
        const prevDocIds = new Set(prevDocs.map((d) => d.id));
        const newDocs = docs.filter((d) => d.id && !prevDocIds.has(d.id));

        if (newDocs.length > 0 && step) {
          const result: ToolCallResult = {
            documents: newDocs.map((d) =>
              mapDocument(d as unknown as Record<string, unknown>)
            ),
            proposals: proposals.map((p) =>
              mapProposal(p as unknown as Record<string, unknown>)
            ),
          };

          if (!step.toolCalls) step.toolCalls = [];
          const runningTc = step.toolCalls.find(
            (tc) => tc.status === "running"
          );
          if (runningTc) {
            runningTc.result = result;
            runningTc.status = "completed";
          } else {
            step.toolCalls.push({
              id: generateId(),
              name: "retrieve_documents",
              status: "completed",
              result,
            });
          }
          latestStatus = "Dokumente gefunden.";
          changed = true;
        }

        // -- Detect relevance changes (is_checked / is_relevant flipped) ------
        for (const doc of docs) {
          const prev = prevDocs.find((p) => p.id === doc.id);

          const prevChecked = prev?.is_checked ?? false;
          const prevRelevant = prev?.is_relevant ?? false;

          const relevanceChanged =
            (doc.is_checked && !prevChecked) ||
            (doc.is_relevant !== prevRelevant && prev !== undefined);

          if (!relevanceChanged) continue;

          if (step) {
            if (!step.documentChecks) step.documentChecks = [];

            const docName =
              pickString(
                (doc.metadata as Record<string, unknown>)?.name,
                (doc.metadata as Record<string, unknown>)?.title,
                doc.id
              ) || "Dokument";

            // Avoid duplicate entries for the same document in this step
            const existing = step.documentChecks.find(
              (c) => c.name === docName
            );
            if (existing) {
              existing.relevant = doc.is_relevant;
              existing.reason = doc.relevance_reason || "";
            } else {
              step.documentChecks.push({
                name: docName,
                relevant: doc.is_relevant,
                reason: doc.relevance_reason || "",
              });
            }
            latestStatus = `Prüfe: ${docName}…`;
          }
          changed = true;
        }

        // -- Detect newly appeared proposals (without new docs) ---------------
        if (
          !changed &&
          proposals.length > 0 &&
          proposals.length !== prevProposals.length
        ) {
          changed = true;
        }

        // -- Detect error_info from the backend state -------------------------
        if (snap.error_info && !latestErrorInfo) {
          const ei = snap.error_info;
          latestErrorInfo = {
            errorType: ei.error_type,
            message: ei.message,
            details: ei.details,
          };
          latestStatus = ei.message;
          changed = true;
        }

        // Update previous snapshot for next diff
        prevDocs = docs;
        prevProposals = proposals;

        if (changed) emitProgress();
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
      onToolCallStartEvent: () => {},
      onToolCallEndEvent: () => {},
      onToolCallResultEvent: () => {},
    };

    // -- Execute --------------------------------------------------------------

    try {
      await agent.runAgent({ abortController }, subscriber);
      const responseText =
        latestText || extractAssistantResponse(agent.messages);
      return buildAnswer(responseText, latestStatus, steps, latestErrorInfo);
    } catch (error) {
      console.error("Agent execution failed:", error);
      return buildAnswer(
        "Ein Fehler ist bei der Verarbeitung Ihrer Anfrage aufgetreten.",
        "Fehler",
        steps,
        latestErrorInfo
      );
    } finally {
      abortController.abort();
    }
  }
}
