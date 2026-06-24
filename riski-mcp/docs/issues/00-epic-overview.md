# Epic: RISKI MCP server for Reachy Mini

**Labels:** `epic`, `mcp`, `reachy-mini`

## Summary

Build `riski-mcp`, an MCP server that exposes the RISKI RIS-search agent as a
tool, deployed as a public Hugging Face **Gradio** Space so it can be installed
into the Reachy Mini conversation app. A robot user asks a spoken question about
Munich's *Ratsinformationssystem* (RIS); the conversation app calls our MCP tool;
the tool relays the question to the deployed RISKI backend's AG-UI agent endpoint,
aggregates the streamed answer, and returns a concise spoken-friendly response.

## Background / constraints

- **Gradio is mandatory** for the Reachy Mini install path. The conversation app's
  `tool-spaces add <owner/space>` only accepts public Gradio Spaces exposing the
  standard `/gradio_api/mcp/` endpoint. Non-Gradio / Docker / raw-URL MCP servers
  are not supported there. (https://huggingface.co/blog/adding-mcp-tools-to-reachy-mini)
- **Tools must be stateless** — each MCP call creates a fresh `threadId`/`runId`.
- **Thin wrapper, not a re-host.** The backend needs Postgres/pgvector + OpenAI +
  Langfuse. The Space calls an already-deployed backend over HTTPS
  (`RISKI_BACKEND_URL`); it does not bundle it.
- The backend's primary capability is `POST /api/ag-ui/riskiagent`, an AG-UI
  **streaming** endpoint — the wrapper must consume SSE events, not a JSON body.

## Scope

In scope:
- New `riski-mcp/` Python module (Gradio app + MCP server).
- AG-UI SSE client that turns the event stream into `{answer, documents, proposals, error}`.
- One or more MCP tools (primary: ask/search RIS), with docstrings + type hints.
- HF Space deployment config, README metadata, Reachy Mini install docs.
- Tests + CI.

Out of scope:
- Changes to the RISKI backend itself (unless a small, additive endpoint is needed —
  raise separately).
- Robot motion/voice choreography (handled by the conversation app).

## Acceptance criteria

- [ ] A public HF Gradio Space serves an MCP endpoint at `/gradio_api/mcp/`.
- [ ] `reachy-mini-conversation-app tool-spaces add <owner/space>` discovers the tool(s).
- [ ] Asking a RIS question through the robot returns a correct, concise answer with
      source references, backed by the live RISKI backend.
- [ ] Backend error states (no documents, timeout, content policy) become friendly
      spoken messages instead of stack traces.
- [ ] Unit + integration tests pass in CI; the MCP endpoint has a smoke test.

## Child issues

01 scaffold · 02 models/client · 03 AG-UI stream client · 04 MCP tools ·
05 config/secrets · 06 Gradio app · 07 error/voice UX · 08 HF deploy ·
09 Reachy integration · 10 testing · 11 CI/observability.