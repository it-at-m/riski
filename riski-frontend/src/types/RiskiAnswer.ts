import type Proposal from "@/types/Proposal.ts";
import type Document from "@/types/Document.ts";

export default interface RiskiAnswer {
  ai_response: string;
  proposals: Proposal[];
  documents: Document[];
}
