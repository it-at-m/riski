import type RiskiAnswer from "@/types/RiskiAnswer";
import type { DocumentCheckResult, ExecutionStep } from "@/types/RiskiAnswer";

import AgUiAgentClient from "@/api/AgUiAgentClient";

type Callback<T> = (result: T) => void;

export default class SearchService {
  /**
   * Performs a search based on the provided query.
   *
   * @param query - The search query.
   * @param onProcessed - Callback function called when a RiskiAnswer is processed.
   * @param onComplete - Callback function called when the search is complete.
   * @param signal - The AbortSignal used to cancel the search.
   * @throws {string} If the query is empty or null.
   */
  static search(
    query: string | null | undefined,
    onProcessed: Callback<RiskiAnswer>,
    onComplete: Callback<void>,
    signal: AbortSignal
  ): Promise<void> {
    if (query) {
      return SearchService.performSearch(
        query,
        onProcessed,
        onComplete,
        signal
      );
    }
    return Promise.reject("Die Anfrage ist leer");
  }

  /**
   * Performs a search operation.
   *
   * @param query - The search query.
   * @param onProcessed - Callback function called when a document is successfully processed with the answer chain.
   * @param onComplete - Callback function called when the search operation is complete.
   * @param signal - The AbortSignal used to cancel the search operation.
   * @returns A Promise that resolves when the search operation is complete.
   */
  private static async performSearch(
    query: string,
    onProcessed: Callback<RiskiAnswer>,
    onComplete: Callback<void>,
    signal: AbortSignal
  ): Promise<void> {
    const isMockMode = import.meta.env.MODE === "development";

    if (isMockMode) {
      return SearchService.localExampleAnswer(query, onProcessed)
        .then(() => {
          onComplete();
        })
        .catch((err: any) => {
          if (typeof err === "string" && !err.includes("404")) {
            console.debug(err);
          }
          onComplete();
          if (!signal.aborted) return Promise.reject(String(err));
        });
    } else {
      return AgUiAgentClient.ask(query, signal, onProcessed)
        .then(() => {
          onComplete();
        })
        .catch((err: any) => {
          if (typeof err === "string" && !err.includes("404")) {
            console.debug(err);
          }
          onComplete();
          if (!signal.aborted) return Promise.reject(String(err));
        });
    }
  }

  private static async localExampleAnswer(
    query: string,
    onProcessed: Callback<RiskiAnswer>
  ) {
    const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

    const documents = [
      { name: "Haushaltsbericht 2024", size: 64000, risUrl: "url1" },
      { name: "Stadtratsvorlage Finanzen", size: 6423000, risUrl: "url2" },
      { name: "Protokoll Finanzausschuss", size: 240000, risUrl: "url3" },
    ];
    const proposals = [
      { name: "Antrag Haushalt 2025", identifier: "A1029", risUrl: "url4" },
      { name: "Antrag Nachtragshaushalt", identifier: "A2024", risUrl: "url5" },
      { name: "Antrag Konsolidierung", identifier: "A3023", risUrl: "url6" },
    ];

    const ai_response =
      "Hier steht dann die Zusammenfassung der KI. Zum Beispiel, dass in den letztem 2 Jahren 27 Anfragen zu Haushaltsfragen im Stadtrat eingebracht wurden. Außerdem die Aufteilung auf die Fraktionen und die zentralen Ergebnisse der Anfragen.";

    const steps: ExecutionStep[] = [];

    const emit = (status?: string) =>
      onProcessed({
        response: "",
        documents: [],
        proposals: [],
        status,
        steps: structuredClone(steps),
      });

    // Step 1: model (decides to call tool)
    steps.push({ name: "model", displayName: "Denke nach", status: "running" });
    emit("Denke nach...");
    await delay(800);
    steps[0]!.status = "completed";
    emit("Denke nach...");

    // Step 2: tools (executes retrieve_documents)
    steps.push({
      name: "tools",
      displayName: undefined,
      status: "running",
      toolCalls: [
        {
          id: "tc-mock-1",
          name: "retrieve_documents",
          args: query,
          status: "running",
        },
      ],
    });
    emit("Verwende Werkzeuge...");
    await delay(1500);

    // Tool completes with results
    steps[1]!.toolCalls![0]!.status = "completed";
    steps[1]!.toolCalls![0]!.result = { documents, proposals };
    steps[1]!.status = "completed";
    emit("Werkzeug ausgeführt.");

    // Step 3: guard (checks each document individually)
    steps.push({
      name: "guard",
      displayName: "Ergebnisse prüfen",
      status: "running",
      documentChecks: [],
    });
    emit("Prüfe Ergebnisse...");
    await delay(400);

    // Simulate per-document checks
    const docChecks: DocumentCheckResult[] = [
      {
        name: "Haushaltsbericht 2024",
        relevant: true,
        reason: "Betrifft direkt die angefragte Haushaltsplanung.",
      },
      {
        name: "Stadtratsvorlage Finanzen",
        relevant: true,
        reason: "Enthält relevante Finanzinformationen zum Thema.",
      },
      {
        name: "Protokoll Finanzausschuss",
        relevant: false,
        reason: "Behandelt ein anderes Thema aus dem Finanzausschuss.",
      },
    ];

    for (const check of docChecks) {
      steps[2]!.documentChecks!.push(check);
      emit(`Prüfe: ${check.name}…`);
      await delay(600);
    }

    steps[2]!.status = "completed";
    emit("Prüfe Ergebnisse...");

    // Filter documents based on checks (remove irrelevant ones)
    const filteredDocuments = documents.filter(
      (_, i) => docChecks[i]?.relevant
    );

    // Step 4: model again (generates final answer)
    steps.push({
      name: "model",
      displayName: "Antwort generieren",
      status: "running",
    });
    emit("Generiere Antwort...");
    await delay(1200);
    steps[3]!.status = "completed";

    // Final answer
    onProcessed({
      response: ai_response,
      documents: filteredDocuments,
      proposals,
      status: "",
      steps: structuredClone(steps),
    });
  }
}
