# Testing (unit, integration, MCP smoke)

**Labels:** `mcp`, `testing`
**Depends on:** #03, #04, #06

## Goal

Cover the wrapper with tests at three levels, mirroring the backend's pytest setup
(`pytest`, `pytest-asyncio`, `pytest-cov`).

## Tasks

- [ ] **Unit — AG-UI client (#03):** feed recorded SSE fixtures and assert the parsed
      `RiskiAnswer`:
  - happy path (answer + documents + proposals)
  - `no_documents_found`, `no_relevant_documents`, `timeout`, `content_policy_violation`
  - `RUN_ERROR`
  - malformed/truncated stream, empty stream, mid-stream disconnect
- [ ] **Unit — models (#02):** `build_run_input` produces a schema-valid payload with
      fresh IDs.
- [ ] **Unit — formatter (#07):** each `error_type` → expected sentence; source
      capping; markdown stripped; length cap.
- [ ] **Integration (opt-in, marked):** against a locally running backend, run a real
      query and assert a non-empty answer. Skip by default in CI (needs DB + LLM
      keys); document how to run.
- [ ] **MCP smoke:** start the Gradio app, hit `/gradio_api/mcp/` `tools/list`, assert
      `search_munich_ris` is present with the expected input schema; optionally call
      it against a mocked backend.
- [ ] Capture/commit SSE fixtures (sanitized — no secrets/PII) for reuse.

## Acceptance criteria

- [ ] `uv run pytest` passes; coverage on `agui_client`, `tools`, formatter is solid.
- [ ] Integration test passes locally against a real backend (documented, skipped in CI).
- [ ] MCP smoke test confirms tool discovery + schema.

## Notes

- Record fixtures once from a live backend; afterwards tests run offline.
- Use `respx`/`httpx` mock transport to simulate streaming responses deterministically.