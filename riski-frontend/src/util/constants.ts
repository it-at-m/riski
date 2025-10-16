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

export const DEFAULT_FRONTEND_CONFIG = {
  scrubber_enabled: false,
};
//API
export const SCRUBBER_ENDPOINT = "/api/scrub";
export const RETRIEVAL_ENDPOINT = "/api/retrieval";
export const ANSWER_ENDPOINT = "/api/answer";
export const SCORE_ENDPOINT = "/api/score";
export const CONFIG_ENDPOINT = "/api/config";
export const QUERY_LENGTH_LIMIT_ERROR_TYPE = "string_too_long";
