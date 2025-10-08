import type { FeebackConfig } from "@/types/FeedbackConfig";

export const USE_MOCK_DATA: boolean = import.meta.env.VITE_USE_MOCK_DATA
  ? import.meta.env.VITE_USE_MOCK_DATA === "true"
  : false;

export function getAPIBaseURL(): string {
  if (import.meta.env.VITE_VUE_APP_API_URL) {
    return import.meta.env.VITE_VUE_APP_API_URL;
  } else {
    return new URL(import.meta.url).origin;
  }
}

// FEEDBACK
// prefill survey with codes https://www.limesurvey.org/manual/URL_fields/en#Prefilling_a_survey_using_GET_parameters
export const DEFAULT_FEEDBACK_CONFIG: FeebackConfig = {
  positive: {
    url: "https://test74.muenchen.de/schulung/index.php/585238?lang=de-easy",
    trace_code: "G01Q03",
    search_code: "G01Q02",
  },
  negative: {
    url: "https://test74.muenchen.de/schulung/index.php/651171?lang=de-easy",
    trace_code: "Q00",
    search_code: "G01Q04",
  },
};

// DLF-SEARCH-WEBCOMPONENT
export const DEFAULT_EXAMPLES = [
  "Was brauche ich alles, um mich umzumelden?",
  "Wie kann ich meinen Personalausweis verlängern?",
  "Wo ist mein Wahlbüro für die Bundestagswahl?",
  "Meine Oma braucht einen Computer, gibt es einen Zuschuss?",
  "Wie tausche ich meinen alten Führerschein um?",
  "Kann ich eine Sozialwohnung bekommen?",
];

export const DEFAULT_FRONTEND_CONFIG = {
  feedback: DEFAULT_FEEDBACK_CONFIG,
  examples: DEFAULT_EXAMPLES,
  scrubber_enabled: false,
};
//API
export const SCRUBBER_ENDPOINT = "/api/scrub";
export const RETRIEVAL_ENDPOINT = "/api/retrieval";
export const ANSWER_ENDPOINT = "/api/answer";
export const SCORE_ENDPOINT = "/api/score";
export const CONFIG_ENDPOINT = "/api/config";
export const QUERY_LENGTH_LIMIT_ERROR_TYPE = "string_too_long";
