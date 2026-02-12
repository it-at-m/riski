import type ConfigResponse from "@/types/ConfigResponse";

import { getAPIBaseURL } from "@/util/constants";

export default class SystemClient {
  static async getConfig(): Promise<ConfigResponse> {
    const isMockMode = import.meta.env.MODE === "development";
    if (isMockMode) {
      return {
        version: "0.1.0-dev",
        frontend_version: "0.1.0-dev",
        title: "RIS KI Suche (Beta-Version)",
      };
    }

    const url = `${getAPIBaseURL()}/api/config`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch config: ${response.statusText}`);
    }
    return await response.json();
  }
}
