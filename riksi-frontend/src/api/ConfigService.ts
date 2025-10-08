import type FrontendConfig from "@/types/FrontendConfig";

import {
  CONFIG_ENDPOINT,
  DEFAULT_FRONTEND_CONFIG,
  getAPIBaseURL,
} from "@/util/constants";

/**
 * Service class for getting frontend config
 */
export default class ConfigService {
  static async get(): Promise<FrontendConfig> {
    const response = await fetch(`${getAPIBaseURL()}${CONFIG_ENDPOINT}`, {
      method: "GET",
      headers: {
        Accept: "application/json", // Set the accept header to application/json
      },
    });
    if (response.status !== 200) {
      console.error(
        "Error loading config, using default config. Status code: " +
          response.status
      );
      return DEFAULT_FRONTEND_CONFIG;
    } else return (await response.json()) as unknown as FrontendConfig;
  }
}
