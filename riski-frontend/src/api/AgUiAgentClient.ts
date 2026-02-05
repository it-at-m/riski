import type Document from "@/types/Document";
import type Proposal from "@/types/Proposal";
import type RiskiAnswer from "@/types/RiskiAnswer";
import type { ExecutionStep, ToolCallInfo } from "@/types/RiskiAnswer";
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
    document.source
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

      return {
        response: response || "Unsere KI konnte keine Antwort generieren.",
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
        return {
          response: response,
          documents: [],
          proposals: [],
          status,
          steps,
        };
      }
    }
  }

  const { documents, proposals } = extractAnswerFromState(state);
  return {
    response: text || "Unsere KI konnte keine Antwort generieren.",
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
      const answer = buildAnswer(
        latestText || extractAssistantResponse(agent.messages),
        latestState,
        latestStatus,
        latestSteps
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
          // If we are receiving text content, we are definitely generating the answer now
          if (currentStep.name === "model") {
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
        // Could be specific about what tool finished
        latestStatus = "Werkzeug ausgeführt.";
        emitProgress();
      },
      onToolCallStartEvent: ({ event }) => {
        const currentStep = latestSteps.find(
          (step) => step.status === "running"
        );
        if (currentStep) {
          if (!currentStep.toolCalls) currentStep.toolCalls = [];

          let toolArgs = "";
          // Check for RAW event data structure which might contain input args
          if ("rawEvent" in event) {
            const raw = event.rawEvent as any;
            if (raw?.event?.data?.input?.query) {
              toolArgs = raw.event.data.input.query;
            }
          }

          currentStep.toolCalls.push({
            id: event.toolCallId,
            name: event.toolCallName,
            args: toolArgs,
            status: "running",
          });
          // Check if we are in the 'model' step, which proposes tool calls (thinking)
          if (currentStep.name === "model") {
            latestStatus = `Entscheide für Werkzeug: ${event.toolCallName}...`;
          }
        }
        emitProgress();
      },
      onToolCallEndEvent: ({ event }) => {
        const currentStep = latestSteps.find(
          (step) => step.status === "running"
        );
        if (currentStep && currentStep.toolCalls) {
          const toolCall = currentStep.toolCalls.find(
            (tc) => tc.id === event.toolCallId
          );
          if (toolCall) {
            toolCall.status = "completed";
          }
        }
        emitProgress();
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
