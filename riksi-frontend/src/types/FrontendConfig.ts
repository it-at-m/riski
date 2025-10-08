import type { FeebackConfig } from "./FeedbackConfig";

export default interface FrontendConfig {
  feedback: FeebackConfig;
  examples: string[];
  scrubber_enabled: boolean;
}
