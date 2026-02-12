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

export interface ExecutionStep {
  name: string;
  /** Optional override for the displayed label (e.g. "Denke nach…" vs "Antwort generieren") */
  displayName?: string;
  status: "running" | "completed" | "failed";
  toolCalls?: ToolCallInfo[];
}

export default interface RiskiAnswer {
  response: string;
  proposals: Proposal[];
  documents: Document[];
  status?: string;
  steps?: ExecutionStep[];
}
