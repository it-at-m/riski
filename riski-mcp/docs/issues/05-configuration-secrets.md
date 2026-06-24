# Configuration & secrets

**Labels:** `mcp`, `chore`
**Depends on:** #01

## Goal

Centralize configuration via `pydantic-settings`, matching the backend's style, and
define which values are HF Space **secrets** vs. public **variables**.

## Settings

| Key | Default | Notes |
|-----|---------|-------|
| `RISKI_MCP__BACKEND_URL` | — (required) | Base URL of the deployed RISKI backend. **Secret** on HF. |
| `RISKI_MCP__BACKEND_AUTH_HEADER` | none | Optional `Authorization`/API-key header if the backend is protected. **Secret**. |
| `RISKI_MCP__REQUEST_TIMEOUT_SECONDS` | 60 | Overall AG-UI stream timeout. |
| `RISKI_MCP__CONNECT_TIMEOUT_SECONDS` | 10 | httpx connect timeout. |
| `RISKI_MCP__MAX_SOURCES` | 3 | Max sources spoken back. |
| `RISKI_MCP__VERIFY_SSL` | true | Allow disabling for self-signed corp certs; prefer truststore. |
| `RISKI_MCP__LOG_LEVEL` | INFO | |

## Tasks

- [ ] `src/riski_mcp/config.py`: `Settings(AppBaseSettings-like)` with
      `env_prefix="RISKI_MCP__"`, `.env` support, `@lru_cache get_settings()`.
- [ ] Use `truststore.inject_into_ssl()` at startup (parity with backend) for
      corporate CA handling; `VERIFY_SSL` as an escape hatch.
- [ ] Fail fast with a clear message if `BACKEND_URL` is missing.
- [ ] Update `.env.example` and document each key in the README.
- [ ] Document the HF Spaces mapping: secrets vs. variables, and that they surface
      as environment variables in the Space runtime.

## Acceptance criteria

- [ ] Missing `BACKEND_URL` raises a clear startup error (not a 500 mid-request).
- [ ] Settings load from env and `.env`; secrets never logged.
- [ ] Timeouts are actually applied by the client (#03) and httpx layer.

## Notes

- HF Space secrets are injected as env vars at runtime — no extra SDK needed.
- Keep secret values out of logs and out of any Gradio UI output.