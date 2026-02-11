import type Document from "@/types/Document";
import type Proposal from "@/types/Proposal";
import type RiskiAnswer from "@/types/RiskiAnswer";
import type { ExecutionStep } from "@/types/RiskiAnswer";
import type { AgentSubscriber } from "@ag-ui/client";
import type { Message } from "@ag-ui/core";

import { HttpAgent } from "@ag-ui/client";

import { getAPIBaseURL, RISKI_AGENT_ENDPOINT } from "@/util/constants";

const buildUrl = () => `${getAPIBaseURL()}${RISKI_AGENT_ENDPOINT}`;

const generateId = (): string => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `riski-${Math.random().toString(36).slice(2, 12)}`;
};

type AgUiDocument = Record<string, unknown>;

type RiskiAgentState = {
  documents?: AgUiDocument[];
  proposals?: AgUiDocument[];
};

type AnswerUpdateCallback = (answer: RiskiAnswer) => void;

type TextFragment = {
  type: string;
  text?: unknown;
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === "object" && value !== null;
};

const isTextFragment = (value: unknown): value is TextFragment => {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof (value as Record<string, unknown>).type === "string"
  );
};

const extractAssistantResponse = (messages: Message[]): string => {
  const assistantMessage = [...messages]
    .reverse()
    .find((message) => message.role === "assistant");

  if (!assistantMessage) {
    return "";
  }

  const content: unknown = assistantMessage.content;
  if (typeof content === "string") {
    return content;
  }

  if (Array.isArray(content)) {
    return content
      .map((fragment: unknown) => {
        if (typeof fragment === "string") return fragment;
        if (
          isTextFragment(fragment) &&
          fragment.type === "text" &&
          typeof fragment.text === "string"
        ) {
          return fragment.text;
        }
        return "";
      })
      .filter((value: string) => value.length > 0)
      .join("\n");
  }

  return "";
};

const pickStringValue = (...values: unknown[]): string => {
  for (const value of values) {
    const text = stringifyValue(value);
    if (text) {
      return text;
    }
  }
  return "";
};

const getDocumentMetadata = (
  document: AgUiDocument
): Record<string, unknown> | undefined => {
  const metadataCandidate = (document as { metadata?: unknown }).metadata;
  return isRecord(metadataCandidate) ? metadataCandidate : undefined;
};

const mapDocument = (document: AgUiDocument): Document => {
  const metadata = getDocumentMetadata(document);
  const name =
    pickStringValue(
      metadata?.title,
      metadata?.name,
      document.title,
      document.name,
      metadata?.id,
      document.id
    ) || "Dokument";
  const risUrl = pickStringValue(
    metadata?.risUrl,
    metadata?.source,
    document.risUrl,
    document.source,
    metadata?.id,
    document.id
  );
  const size =
    typeof metadata?.size === "number"
      ? metadata.size
      : typeof document.size === "number"
        ? document.size
        : 0;
  const identifier = pickStringValue(
    metadata?.identifier,
    document.identifier,
    metadata?.id,
    document.id
  );

  return {
    name,
    risUrl,
    size,
    identifier,
  };
};

const mapProposal = (proposal: AgUiDocument): Proposal => {
  const metadata = getDocumentMetadata(proposal);
  const name =
    pickStringValue(
      metadata?.title,
      metadata?.name,
      proposal.title,
      proposal.name,
      metadata?.id,
      proposal.id
    ) || "";
  const identifier = pickStringValue(
    metadata?.identifier,
    metadata?.id,
    proposal.identifier,
    proposal.id
  );
  const risUrl = pickStringValue(
    metadata?.risUrl,
    metadata?.source,
    proposal.risUrl,
    proposal.source
  );

  return {
    name,
    identifier,
    risUrl,
  };
};

function stringifyValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return value.toString();
  }
  return "";
}

const extractAnswerFromState = (
  state: RiskiAgentState
): Pick<RiskiAnswer, "documents" | "proposals"> => {
  const documents = Array.isArray(state?.documents)
    ? state.documents.map(mapDocument)
    : [];

  const proposals = Array.isArray(state?.proposals)
    ? state.proposals.map(mapProposal)
    : [];

  return {
    documents,
    proposals,
  };
};

/**
 * Turn a Python repr-style dict string into a (best-effort) JSON string.
 * Handles single → double quote conversion and converts Python keywords
 * None / True / False.
 */
const pythonDictToJson = (s: string): string =>
  s
    .replace(/'/g, '"')
    .replace(/\bNone\b/g, "null")
    .replace(/\bTrue\b/g, "true")
    .replace(/\bFalse\b/g, "false");

/**
 * Extract documents and proposals from the Python repr string returned by
 * the LangGraph backend in tool-output events.
 *
 * The string looks like:
 *   {'documents': [Document(id='…', metadata={…}, page_content='…'), …],
 *    'proposals': [{'identifier': '…', …}, …]}
 *
 * Because `Document(…)` is a Python constructor call (not valid JSON), we
 * extract each Document with a regex and parse its `metadata` dict, which
 * contains the fields the UI actually needs (id/risUrl, name, size).
 * Proposals are plain Python dicts so we can parse them after quote
 * conversion.
 */
const extractToolOutputIntoState = (
  data: Record<string, unknown> | undefined,
  state: RiskiAgentState
): void => {
  if (!data) return;

  const output = data.output as Record<string, unknown> | undefined;
  if (!output || typeof output !== "object") return;

  const content = output.content as string | undefined;
  if (typeof content !== "string") return;

  try {
    // ── Documents ──────────────────────────────────────────────────────
    // Each document appears as  Document(id='…', metadata={…}, page_content='…')
    // We only need id + metadata (the UI does not render page_content).
    // The metadata dict is flat: {'id': '…', 'name': '…', 'size': 123}
    const docRegex = /Document\(id='([^']*)',\s*metadata=(\{[^}]*\})/g;
    let match: RegExpExecArray | null;
    const docs: AgUiDocument[] = [];

    while ((match = docRegex.exec(content)) !== null) {
      const docId = match[1];
      const metadataRaw = match[2]; // e.g. {'id': '…', 'name': '…', 'size': 123}
      try {
        const metadata = JSON.parse(pythonDictToJson(metadataRaw ?? "{}"));
        docs.push({ id: docId, metadata });
      } catch {
        // Metadata not parseable – skip this document
      }
    }

    if (docs.length > 0) {
      state.documents = [...(state.documents || []), ...docs];
    }

    // ── Proposals ──────────────────────────────────────────────────────
    // Proposals are plain Python dicts inside 'proposals': [{…}, …]
    // Extract the array substring and parse it.
    const proposalsMatch = content.match(/'proposals':\s*(\[[\s\S]*\])\s*\}/);
    if (proposalsMatch) {
      try {
        const proposals = JSON.parse(
          pythonDictToJson(proposalsMatch[1] ?? "[]")
        );
        if (Array.isArray(proposals)) {
          const props = proposals.filter(isRecord) as AgUiDocument[];
          if (props.length > 0) {
            state.proposals = [...(state.proposals || []), ...props];
          }
        }
      } catch {
        // Proposals not parseable
      }
    }
  } catch {
    // Content is not parseable – that's fine, we'll get the data from the
    // final state snapshot instead.
  }
};

const createAbortController = (signal: AbortSignal): AbortController => {
  const controller = new AbortController();
  const abortListener = () => controller.abort(signal.reason);
  if (signal.aborted) {
    controller.abort(signal.reason);
  } else {
    signal.addEventListener("abort", abortListener, { once: true });
  }
  return controller;
};

const attachResultsToToolCalls = (
  steps: ExecutionStep[] | undefined,
  documents: Document[],
  proposals: Proposal[]
): void => {
  if (!steps || (documents.length === 0 && proposals.length === 0)) return;

  for (const step of steps) {
    if (!step.toolCalls) continue;
    for (const toolCall of step.toolCalls) {
      if (toolCall.name === "retrieve_documents" && !toolCall.result) {
        toolCall.result = { documents, proposals };
      }
    }
  }
};

const buildAnswer = (
  text: string,
  state: RiskiAgentState,
  status?: string,
  steps?: ExecutionStep[]
): RiskiAnswer => {
  try {
    const json = JSON.parse(text);
    if (isRecord(json)) {
      const response = typeof json.response === "string" ? json.response : "";
      const documents = Array.isArray(json.documents)
        ? json.documents.filter(isRecord).map(mapDocument)
        : [];
      const proposals = Array.isArray(json.proposals)
        ? json.proposals.filter(isRecord).map(mapProposal)
        : [];

      attachResultsToToolCalls(steps, documents, proposals);
      return {
        response:
          response ||
          (status ? "" : "Unsere KI konnte keine Antwort generieren."),
        documents,
        proposals,
        status,
        steps,
      };
    }
  } catch {
    // Attempt to extract partial response if it looks like a JSON stream
    if (text.trimStart().startsWith("{")) {
      const match = text.match(/"response"\s*:\s*"((?:[^"\\]|\\.)*)(?:"|$)/);
      if (match && typeof match[1] === "string") {
        const response = match[1]
          .replace(/\\"/g, '"')
          .replace(/\\n/g, "\n")
          .replace(/\\\\/g, "\\");

        // Use documents/proposals from state even during partial JSON streaming
        const { documents, proposals } = extractAnswerFromState(state);
        attachResultsToToolCalls(steps, documents, proposals);
        return {
          response: response,
          documents,
          proposals,
          status,
          steps,
        };
      }
    }
  }

  const { documents, proposals } = extractAnswerFromState(state);
  attachResultsToToolCalls(steps, documents, proposals);
  return {
    response:
      text || (status ? "" : "Unsere KI konnte keine Antwort generieren."),
    documents,
    proposals,
    status,
    steps,
  };
};

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
    let latestState: RiskiAgentState = {};
    let latestStatus = "Initialisiere...";
    let latestSteps: ExecutionStep[] = [];

    const emitProgress = () => {
      if (!onProgress || signal.aborted || abortController.signal.aborted) {
        return;
      }
      // Deep-clone steps so Vue detects the change (same array reference won't trigger reactivity)
      const stepsSnapshot = structuredClone(latestSteps);
      const answer = buildAnswer(
        latestText || extractAssistantResponse(agent.messages),
        latestState,
        latestStatus,
        stepsSnapshot
      );

      onProgress(answer);
    };

    const subscriber: AgentSubscriber = {
      onTextMessageContentEvent: ({ textMessageBuffer }) => {
        latestText = textMessageBuffer;
        // Update content of current running step if it exists
        const currentStep = latestSteps.find(
          (step) => step.status === "running"
        );
        if (currentStep) {
          currentStep.content = textMessageBuffer;
          // If we are receiving text content in a model step, it's generating the answer (not just thinking)
          if (currentStep.name === "model") {
            currentStep.displayName = "Antwort generieren";
            latestStatus = "Generiere Antwort...";
          }
        }
        emitProgress();
      },
      onStateDeltaEvent: ({ state }) => {
        latestState = (state as RiskiAgentState) || {};
        emitProgress();
      },
      onStateSnapshotEvent: ({ state }) => {
        latestState = (state as RiskiAgentState) || {};
        emitProgress();
      },
      onRunFinishedEvent: () => {
        latestStatus = "";
        // Finish any running steps
        latestSteps.forEach((step) => {
          if (step.status === "running") step.status = "completed";
          // Also complete any running tool calls
          step.toolCalls?.forEach((tc) => {
            if (tc.status === "running") tc.status = "completed";
          });
        });
        latestState = (agent.state as RiskiAgentState) || latestState;
        latestText = extractAssistantResponse(agent.messages) || latestText;
        emitProgress();
      },
      onRunErrorEvent: () => {
        latestStatus = "Fehler aufgetreten.";
        // Fail any running steps
        latestSteps.forEach((step) => {
          if (step.status === "running") step.status = "failed";
        });
        emitProgress();
      },
      onRunStartedEvent: () => {
        latestSteps = [];
        emitProgress();
      },
      onStepStartedEvent: ({ event }) => {
        if (event.stepName === "model") {
          latestStatus = "Denke nach...";
        } else if (event.stepName === "tools") {
          latestStatus = "Verwende Werkzeuge...";
        } else if (event.stepName === "retrieve_documents") {
          latestStatus = "Suche Dokumente...";
        } else {
          latestStatus = `Verarbeite Schritt: ${event.stepName}`;
        }
        latestSteps.push({
          name: event.stepName,
          displayName: event.stepName === "model" ? "Denke nach" : undefined,
          status: "running",
          content: "",
          toolCalls: [],
        });
        emitProgress();
      },
      onStepFinishedEvent: ({ event }) => {
        const step = latestSteps
          .slice()
          .reverse()
          .find((s) => s.name === event.stepName && s.status === "running");
        if (step) {
          step.status = "completed";
        }
        emitProgress();
      },
      onToolCallResultEvent: () => {
        // Tool results are handled by onRawEvent("on_tool_end") which has
        // richer data (output.content with documents/proposals).
      },
      onToolCallStartEvent: () => {
        // Tool call starts are handled by onRawEvent("on_tool_start") which
        // provides the input query via data.input.query.
      },
      onToolCallEndEvent: () => {
        // Tool call ends are handled by onRawEvent("on_tool_end") which
        // also extracts documents/proposals from the output.
      },
      onRawEvent: ({ event }) => {
        const raw = event.event as Record<string, unknown> | undefined;
        if (!raw || typeof raw !== "object") return;

        const eventName = raw.event as string | undefined;
        const data = raw.data as Record<string, unknown> | undefined;
        const toolName = raw.name as string | undefined;
        const runId = raw.run_id as string | undefined;

        if (eventName === "on_tool_start") {
          const currentStep = latestSteps.find(
            (step) => step.status === "running"
          );
          if (currentStep) {
            if (!currentStep.toolCalls) currentStep.toolCalls = [];

            const input = data?.input as Record<string, unknown> | undefined;
            const toolArgs =
              typeof input?.query === "string" ? input.query : "";

            currentStep.toolCalls.push({
              id: runId || generateId(),
              name: toolName || "unknown",
              args: toolArgs,
              status: "running",
            });

            latestStatus = `Verwende Werkzeug: ${toolName || "unknown"}...`;
          }
          emitProgress();
        } else if (eventName === "on_tool_end") {
          const currentStep = latestSteps.find(
            (step) => step.status === "running"
          );
          if (currentStep && currentStep.toolCalls) {
            const toolCall = currentStep.toolCalls.find(
              (tc) =>
                tc.status === "running" &&
                (tc.id === runId || tc.name === toolName)
            );
            if (toolCall) {
              toolCall.status = "completed";
            }
          }

          // Extract documents/proposals from tool output and merge into latestState
          // so they appear immediately, without waiting for the final RUN_FINISHED state.
          extractToolOutputIntoState(data, latestState);

          latestStatus = "Werkzeug ausgeführt.";
          emitProgress();
        }
      },
    };

    try {
      await agent.runAgent(
        {
          abortController,
        },
        subscriber
      );

      latestState = (agent.state as RiskiAgentState) || latestState;
      const responseText =
        latestText || extractAssistantResponse(agent.messages);

      return buildAnswer(responseText, latestState, latestStatus, latestSteps);
    } catch (error) {
      console.error("Agent execution failed:", error);
      // Return a user-friendly error response
      return buildAnswer(
        "Ein Fehler ist bei der Verarbeitung Ihrer Anfrage aufgetreten.",
        latestState,
        "Fehler",
        latestSteps
      );
    } finally {
      abortController.abort();
    }
  }
}
