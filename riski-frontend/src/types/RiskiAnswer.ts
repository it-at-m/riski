import type Document from "@/types/Document.ts";
import type Proposal from "@/types/Proposal.ts";

export interface ToolCallResult {
  documents: Document[];
  proposals: Proposal[];
}

export interface ToolCallInfo {
  id: string;
  name: string;
  args?: string;
  status: "running" | "completed";
  result?: ToolCallResult;
}

/** Result of the guard checking a single document for relevance. */
export interface DocumentCheckResult {
  /** Document name / title */
  name: string;
  /** Whether the document was deemed relevant */
  relevant: boolean;
  /** Short reason for the decision */
  reason: string;
}

/**
 * Structured error information from the agent pipeline.
 *
 * Known `errorType` values:
 * - `no_tool_call` – the model did not invoke any tool.
 * - `no_documents_found` – the tool ran but returned zero documents.
 * - `no_relevant_documents` – documents were found but none passed relevance check.
 */
export interface ErrorInfo {
  /** Machine-readable error category */
  errorType: string;
  /** Human-readable message (German) suitable for display */
  message: string;
  /** LLM-generated alternative search query suggestions */
  suggestions?: string[];
  /** Optional extra context (e.g. rejection reasons per document) */
  details?: Record<string, unknown>;
}

export interface ExecutionStep {
  name: string;
  /** Optional override for the displayed label (e.g. "Denke nach…" vs "Antwort generieren") */
  displayName?: string;
  status: "running" | "completed" | "failed";
  toolCalls?: ToolCallInfo[];
  /** Per-document relevance checks performed by the guard node */
  documentChecks?: DocumentCheckResult[];
}

export default interface RiskiAnswer {
  response: string;
  proposals: Proposal[];
  documents: Document[];
  status?: string;
  steps?: ExecutionStep[];
  /** Structured error info when the agent terminates without generating a response */
  errorInfo?: ErrorInfo;
}
