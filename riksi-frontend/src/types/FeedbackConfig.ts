export interface SurveyConfig {
  url: string;
  trace_code?: string;
  search_code?: string;
}

export interface FeebackConfig {
  positive: SurveyConfig;
  negative: SurveyConfig;
}
