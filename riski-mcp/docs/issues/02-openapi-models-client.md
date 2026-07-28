# Typed models & HTTP client from openapi.json

**Labels:** `mcp`
**Depends on:** #01

## Goal

Produce the request/response models the wrapper needs to talk to the backend,
derived from `riski-backend/openapi.json`, plus a thin async `httpx` client for the
non-streaming endpoints (`/api/config`, `/api/healthz`). The streaming endpoint is
handled in #03 but reuses these models.

## Context

`openapi.json` defines `RunAgentInput` (the request body of
`POST /api/ag-ui/riskiagent`) with required fields:
`threadId`, `runId`, `state`, `messages`, `tools`, `context`, `forwardedProps`
(plus optional `parentRunId`, `resume`). `messages` is a discriminated union on
`role`; we only need to *produce* a `UserMessage` (`{id, role:"user", content}`).
`ConfigResponse` and `HealthCheckResponse` are the read models.

## Tasks

- [ ] Add `pydantic` models for the subset we use:
  - `UserMessage` (id, role="user", content: str)
  - `RunAgentInput` (with sane defaults: `state={}`, `tools=[]`, `context=[]`,
    `forwardedProps={}`)
  - `ConfigResponse`, `HealthCheckResponse`
- [ ] Helper `build_run_input(question: str) -> RunAgentInput` that generates fresh
      `threadId`/`runId` (uuid4) per call — **stateless** per MCP-tool requirement.
- [ ] Async `BackendClient` (httpx.AsyncClient) with:
  - `get_config()` → `ConfigResponse`
  - `healthz()` → `HealthCheckResponse`
  - shared base URL, timeout, and headers (filled from config in #05).
- [ ] Decide model-generation strategy: hand-write the small subset (recommended —
      only ~4 models needed) vs. `datamodel-code-generator`. Document the choice.

## Acceptance criteria

- [ ] `build_run_input("...")` yields a payload that validates against the backend's
      `RunAgentInput` schema (verify by posting to a running backend or against the
      JSON schema).
- [ ] `BackendClient.healthz()`/`get_config()` work against a local backend.
- [ ] Unit tests cover `build_run_input` (fresh IDs, correct shape).

## Notes

- Do **not** depend on the backend's internal `ag_ui`/`ag-ui-langgraph` types — keep
  the wrapper decoupled; model only the wire contract from `openapi.json`.
- If hand-writing, add a CI check (or doc note) to re-verify against `openapi.json`
  when the backend version bumps.