# RISKI MCP Server — Implementation Plan

This folder contains the implementation plan for **`riski-mcp`**: a Model Context
Protocol (MCP) server that exposes the RISKI backend's RIS search capability as a
tool, deployed as a **public Hugging Face Gradio Space** so it can be installed
into the **Reachy Mini conversation app** with one command.

## Goal

Let a Reachy Mini robot answer spoken questions about Munich's *Rats­informations­system*
(RIS) by calling the existing RISKI agent. The robot's conversation app discovers
the tool over MCP, invokes it with the user's question, and speaks back the answer.

## Why Gradio + HF Space (the binding constraint)

The Reachy Mini conversation app installs remote tools **only** from public
**Gradio** Spaces that expose the standard `/gradio_api/mcp/` endpoint
(`reachy-mini-conversation-app tool-spaces add <owner/space>`). Non-Gradio Spaces,
Docker-only MCP servers, and arbitrary raw MCP URLs are **not** supported by that
mechanism. Therefore the MCP server is implemented as a Gradio app
(`demo.launch(mcp_server=True)`), not a standalone FastMCP/Docker service.

Refs:
- https://huggingface.co/blog/adding-mcp-tools-to-reachy-mini
- https://huggingface.co/blog/gradio-mcp

## Architecture (decided default)

```
Reachy Mini conversation app
        │  MCP (streamable HTTP / SSE)  →  https://<space>.hf.space/gradio_api/mcp/
        ▼
riski-mcp  (Gradio Space, this module)   ── thin, stateless wrapper
        │  HTTPS POST /api/ag-ui/riskiagent  (consumes AG-UI SSE event stream)
        ▼
RISKI backend (already deployed; Postgres/pgvector + OpenAI + Langfuse)
```

The Space does **not** bundle the backend (which is heavy and stateful). It is a
thin client pointed at an already-deployed backend via a Space secret
(`RISKI_BACKEND_URL`). The non-trivial work is consuming the AG-UI Server-Sent
Event stream and folding it into one stateless, voice-friendly answer.

Backend contract (see `riski-backend/openapi.json` and
`riski-backend/app/api/routers/ag_ui.py`):
- `POST /api/ag-ui/riskiagent` — streams AG-UI events (`RUN_STARTED`,
  `TEXT_MESSAGE_*`, `TOOL_CALL_*`, `STATE_SNAPSHOT`, `RUN_FINISHED`, `RUN_ERROR`).
  Request body is `RunAgentInput`. The final answer text streams as
  `TEXT_MESSAGE_CONTENT` deltas from the `model` node (a JSON
  `StructuredAgentResponse`); `STATE_SNAPSHOT` carries `tracked_documents`,
  `tracked_proposals`, and `error_info`.
- `GET /api/config` — app metadata (title, URLs, version).
- `GET /api/healthz` — health/version.

## Issues (suggested order)

| # | Issue | Depends on |
|---|-------|-----------|
| 00 | [Epic: RISKI MCP server for Reachy Mini](00-epic-overview.md) | — |
| 01 | [Project scaffold & tooling](01-project-scaffold.md) | — |
| 02 | [Typed models & HTTP client from openapi.json](02-openapi-models-client.md) | 01 |
| 03 | [AG-UI SSE stream client & answer aggregation](03-ag-ui-stream-client.md) | 02 |
| 04 | [MCP tool definitions (stateless, voice-friendly)](04-mcp-tools-definition.md) | 03 |
| 05 | [Configuration & secrets](05-configuration-secrets.md) | 01 |
| 06 | [Gradio app exposing the MCP server](06-gradio-app-mcp-server.md) | 04, 05 |
| 07 | [Error handling & spoken-answer UX](07-error-handling-voice-ux.md) | 03, 04 |
| 08 | [Hugging Face Space deployment](08-hf-space-deployment.md) | 06 |
| 09 | [Reachy Mini integration & docs](09-reachy-mini-integration.md) | 08 |
| 10 | [Testing (unit, integration, MCP smoke)](10-testing.md) | 03, 04, 06 |
| 11 | [CI & observability](11-ci-observability.md) | 06, 10 |

Each file is written to be copy-pasteable into a GitHub issue.