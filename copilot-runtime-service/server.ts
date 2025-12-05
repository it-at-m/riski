import { createServer } from "node:http";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  LangGraphHttpAgent,
  copilotRuntimeNodeHttpEndpoint,
} from "@copilotkit/runtime";

const RISKI_AGENT_URL =
  process.env.RISKI_AGENT_URL ?? "http://localhost:8080/api/ag-ui/riskiagent";
const RISKI_AGENT_NAME = process.env.RISKI_AGENT_NAME ?? "riski_agent";

const serviceAdapter = new ExperimentalEmptyAdapter();
const allowedOrigin = process.env.CORS_ORIGIN ?? "http://localhost:5173";

const createRuntime = () =>
  new CopilotRuntime({
    agents: {
      [RISKI_AGENT_NAME]: new LangGraphHttpAgent({
        url: RISKI_AGENT_URL,
        description: "RISKI AG-UI LangGraph agent",
        agentId: RISKI_AGENT_NAME,
      }),
    },
  });

const server = createServer((req, res) => {
  res.setHeader("Access-Control-Allow-Origin", allowedOrigin);
  res.setHeader("Vary", "Origin");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader(
    "Access-Control-Allow-Headers",
    [
      "Content-Type",
      "Authorization",
      "CopilotKit-Api-Key",
      "X-Copilotkit-Runtime-Client-Gql-Version",
    ].join(", ")
  );

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  const runtime = createRuntime();

  const handler = copilotRuntimeNodeHttpEndpoint({
    endpoint: "/copilotkit",
    runtime,
    serviceAdapter,
  });

  return handler(req, res);
});

server.listen(4000, () => {
  console.log(
    `Proxying CopilotKit requests at http://localhost:4000/copilotkit -> ${RISKI_AGENT_URL}`
  );
});
