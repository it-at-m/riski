# Copilot React Frontend

This Vite + React app hosts the CopilotKit experience for RISKI. It connects directly to the LangGraph agent served by the FastAPI backend (`/api/ag-ui/riskiagent`) and visualises the live Retrieval Augmented Generation (RAG) state.

## Features

- **Copilot sidebar** powered by CopilotKit that streams answers from the RISKI LangGraph agent.
- **Live RAG dashboard** mirroring the active LangGraph node, retrieved documents and proposals.
- **Prompt library** with one-click copy for common research tasks.
- Tailwind-based dark layout optimised for embedding inside the wider RISKI experience.

## Prerequisites

  - `RISKI_AGENT_URL` (defaults to `http://localhost:8080/api/ag-ui/riskiagent`)
  - `RISKI_AGENT_NAME` (defaults to `riski_agent`)

## Run the stack locally

```powershell
# 1) Start the FastAPI backend (from riski-backend)
uvicorn app.backend:backend --reload --port 8080

# 2) Start the Copilot runtime proxy (from copilot-runtime-service)
npm install
npm run dev

# 3) Start this frontend (from copilot-react-frontend)
npm install
npm run dev
```

The frontend expects the runtime proxy at `http://localhost:4000/copilotkit`. Adjust the forwarding behaviour via environment variables before launching the proxy:

```powershell
$env:RISKI_AGENT_URL="http://localhost:8080/api/ag-ui/riskiagent"
$env:RISKI_AGENT_NAME="riski_agent"
npm run dev
```


