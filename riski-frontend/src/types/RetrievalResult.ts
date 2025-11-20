export interface RetrievedDocument {
  id: string;
  name: string;
}

export default interface RetrievalResult {
  run_id: string;
  retrieval_documents: RetrievedDocument[];
}
