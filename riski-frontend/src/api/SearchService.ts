import type RiskiAnswer from "@/types/RiskiAnswer";

import {
  ANSWER_ENDPOINT,
  getAPIBaseURL,
} from "@/util/constants";


type Callback<T> = (result: T) => void;

/**
 * Service class for performing search operations against the backend API.
 */
export default class SearchService {
  static answer(
    input: { question: string },
    signal: AbortSignal
  ): Promise<RiskiAnswer | undefined> {
    return fetch(`${getAPIBaseURL()}${ANSWER_ENDPOINT}`, {
      method: "POST",
      signal: signal,
      body: JSON.stringify(input), // Add the input as the request body
      headers: {
        "Content-Type": "application/json", // Set the content type header
      },
    }).then((response) => {
      if (response.status !== 200) {
        return Promise.reject(
          response.status + ": Antwort konnte nicht generiert werden"
        );
      } else return response.json() as unknown as RiskiAnswer;
    });
  }

  /**
   * Performs a search based on the provided query.
   *
   * @param query - The search query.
   * @param onProcessed - Callback function called when a DLFDocument is processed.
   * @param onComplete - Callback function called when the search is complete.
   * @param signal - The AbortSignal used to cancel the search.
   * @throws {string} If the query is empty or null.
   */
  static search(
    query: string | null | undefined,
    onProcessed: Callback<RiskiAnswer>,
    onComplete: Callback<void>,
    signal: AbortSignal,
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
   * @param onProcessed - Callback function called when a document is succesfully processed with the answer chain.
   * @param onComplete - Callback function called when the search operation is complete.
   * @param signal - The AbortSignal used to cancel the search operation.
   * @returns A Promise that resolves when the search operation is complete.
   */
  private static async performSearch(
    query: string,
    onProcessed: Callback<RiskiAnswer>,
    onComplete: Callback<void>,
    signal: AbortSignal,
  ): Promise<void> {

    if(import.meta.env.VITE_NODE_ENV=="development"){
      return SearchService.localExampleAnswer()
              .then((answer) => {
                if (answer) onProcessed(answer);
                onComplete();
              })
              .catch((err: any) => {
                if (!err.includes("404")) {
                  console.debug(err);
                }
                onComplete();
                if (!signal.aborted) return Promise.reject(String(err));
              });
    } else {
      return SearchService.answer(
          {
            question: query,
          },
          signal
      )
          .then((answer) => {
            if (answer) onProcessed(answer);
            onComplete();
          })
          .catch((err: string) => {
            if (!err.includes("404")) {
              console.debug(err);
            }
            onComplete();
            if (!signal.aborted) return Promise.reject(String(err));
          });
    }
  }

  private static async localExampleAnswer() {
    const secondsToWait = Math.floor(Math.random() * 7) + 3;
    await new Promise(r => setTimeout(r, secondsToWait * 1000));

    const ai_response = "Hier steht dann die Zusammenfassung der KI. Zum Beispiel, dass in den letztem 2 Jahren 27 Anfragen zu Haushaltsfragen im Stadtrat eingebracht wurden. Außerdem die Aufteilung auf die Fraktionen und die zentralen Ergebnisse der Anfragen."

    let answer: RiskiAnswer = { ai_response: ai_response, proposals: [], documents: [], };

    answer.proposals.push({name:"Name 1", identifier: "A1029", risUrl: "url4"})
    answer.proposals.push({name:"Name 2", identifier: "A2024", risUrl: "url5"})
    answer.proposals.push({name:"Name 3", identifier: "A3023", risUrl: "url6"})

    answer.documents.push({name:"Name 1", size: 64000, risUrl: "url1"})
    answer.documents.push({name:"Name 2", size: 6423000, risUrl: "url2"})
    answer.documents.push({name:"Name 3", size: 240000, risUrl: "url3"})

    return  Promise.resolve(answer);
  }
}
