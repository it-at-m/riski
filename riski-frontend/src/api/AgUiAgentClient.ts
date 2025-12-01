import type Document from "@/types/Document";
import type Proposal from "@/types/Proposal";
import type RiskiAnswer from "@/types/RiskiAnswer";
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

const mapDocument = (document: AgUiDocument): Document => {
  const name =
    stringifyValue(document.title) || stringifyValue(document.id) || "Dokument";
  const risUrl =
    stringifyValue(document.source) || stringifyValue(document.risUrl) || "";
  const size = typeof document.size === "number" ? document.size : 0;

  return {
    name,
    risUrl,
    size,
  };
};

const mapProposal = (proposal: AgUiDocument): Proposal => ({
  name: stringifyValue(proposal.name) || stringifyValue(proposal.title) || "",
  identifier:
    stringifyValue(proposal.identifier) || stringifyValue(proposal.id) || "",
  risUrl:
    stringifyValue(proposal.risUrl) || stringifyValue(proposal.source) || "",
});

const stringifyValue = (value: unknown): string => {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return value.toString();
  }
  return "";
};

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

const buildAnswer = (text: string, state: RiskiAgentState): RiskiAnswer => {
  const { documents, proposals } = extractAnswerFromState(state);
  return {
    ai_response: text || "Unsere KI konnte keine Antwort generieren.",
    documents,
    proposals,
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

    const emitProgress = () => {
      if (!onProgress || signal.aborted || abortController.signal.aborted) {
        return;
      }
      const answer = buildAnswer(
        latestText || extractAssistantResponse(agent.messages),
        latestState
      );
      onProgress(answer);
    };

    const subscriber: AgentSubscriber = {
      onTextMessageContentEvent: ({ textMessageBuffer }) => {
        latestText = textMessageBuffer;
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
        latestState = (agent.state as RiskiAgentState) || latestState;
        latestText = extractAssistantResponse(agent.messages) || latestText;
        emitProgress();
      },
      onRunErrorEvent: () => {
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

      return buildAnswer(responseText, latestState);
    } finally {
      abortController.abort();
    }
  }
}
