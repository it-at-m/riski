import type Document from "@/types/Document.ts";
import type Proposal from "@/types/Proposal.ts";

export default interface RiskiAnswer {
  ai_response: string;
  proposals: Proposal[];
  documents: Document[];
}
