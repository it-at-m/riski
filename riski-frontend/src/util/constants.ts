export function getAPIBaseURL(): string {
  if (import.meta.env.VITE_VUE_APP_API_URL) {
    return import.meta.env.VITE_VUE_APP_API_URL;
  } else {
    return new URL(import.meta.url).origin;
  }
}

export const ANSWER_ENDPOINT = "/api/answer";
export const RISKI_AGENT_ENDPOINT = "/api/ag-ui/riskiagent";

export const EXAMPLE_QUESTIONS = [
  "Welche Anträge gibt es zum Thema Radverkehr?",
  "Was wurde zum Thema Schulbau beschlossen?",
  "Gibt macht die Stadt in Richtung KI?",
];
