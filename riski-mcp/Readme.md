---
title: RISKI RIS Search (MCP)
emoji: 🏛️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "6.19.0"
app_file: app.py
pinned: false
tags:
  - mcp
  - reachy-mini-tool
---

# RISKI MCP Server

An [MCP](https://modelcontextprotocol.io) server that exposes the RISKI RIS-search
agent as a tool, deployed as a public **Hugging Face Gradio Space** so it can be
installed into the [Reachy Mini](https://huggingface.co/blog/reachy-mini)
conversation app.

A robot user asks a spoken question about Munich's *Ratsinformationssystem* (RIS);
the conversation app calls this MCP tool; the tool relays the question to the
deployed RISKI backend's AG-UI agent endpoint, aggregates the streamed answer, and
returns a concise, spoken-friendly response.

## Architecture

```
Reachy Mini conversation app
        │  MCP (streamable HTTP / SSE)  →  https://<space>.hf.space/gradio_api/mcp/
        ▼
riski-mcp  (Gradio Space, this module)   ── thin, stateless wrapper
        │  HTTPS POST /api/ag-ui/riskiagent  (consumes AG-UI SSE event stream)
        ▼
RISKI backend (already deployed; Postgres/pgvector + OpenAI + Langfuse)
```

The Space is a thin client pointed at an already-deployed backend via the
`RISKI_MCP__BACKEND_URL` secret — it does not bundle the backend. Each call is
**stateless** (fresh `threadId`/`runId`).

## Tools

The Space exposes two MCP tools (auto-derived from the functions in
`src/riski_mcp/tools.py`):

| Tool | Purpose |
|------|---------|
| `search_munich_ris(question: str) -> str` | Primary tool. Relays a RIS question to the agent and returns a concise, spoken-friendly German answer with up to a few sources. |
| `get_riski_capabilities() -> str` | Describes what the agent can answer about, to help the robot's planner decide when to call `search_munich_ris`. Takes no arguments and does not call the backend. |

## Use with Reachy Mini

Install this Space as a tool source in the conversation app:

```bash
reachy-mini-conversation-app tool-spaces add <owner>/<space>
```

`add` validates that the Space is a public Gradio SDK Space, probes its MCP
endpoint (`/gradio_api/mcp/`), discovers the tools, and appends their IDs to the
active profile's `tools.txt`.

Tools are namespaced on the robot as `<space_alias>__<tool>`, e.g.
`<space_alias>__search_munich_ris`. Keep `search_munich_ris` enabled in
`tools.txt`; `get_riski_capabilities` is optional (it helps planning but adds a
little noise).

Example spoken prompts (German) that should route to the tool:

- „Frag das RIS nach Anträgen zum Radverkehr in München.“
- „Was hat der Stadtrat zum Thema Wohnungsbau beschlossen?“
- „Gibt es Beschlussvorlagen zur Begrünung der Innenstadt?“
- „Suche im Ratsinformationssystem nach Protokollen zum Nahverkehr.“

### Known limitations

- **Latency:** an agent run streams over several seconds (LLM + DB + network);
  expect a noticeable pause before the robot speaks.
- **Cold starts:** a sleeping Space takes time to wake on the first request.
- **Language:** answers are German (matching the backend's user-facing wording).
- **Discovery failures** are almost always: Space not public, not a Gradio SDK
  Space, or the MCP endpoint not exposed (`mcp_server=True` missing).

## Local development

```powershell
# from riski-mcp/
uv sync
Copy-Item .\.env.example .\.env -Force   # then fill in RISKI_MCP__BACKEND_URL
uv run pytest
python app.py                            # serves the UI + MCP endpoint locally
```

The opt-in live MCP smoke test (which launches the app and probes `tools/list`)
is gated behind an env flag:

```powershell
$env:RUN_MCP_SMOKE="1"; uv run pytest test/test_app.py
```

## Dependencies

Local dev / CI dependencies live in `pyproject.toml` (managed with `uv`).
`requirements.txt` is the **HF Space** install manifest and is **auto-generated**
from `uv.lock` — do not edit it by hand. A pre-commit hook regenerates it whenever
`pyproject.toml` or `uv.lock` changes; to regenerate manually:

```powershell
uv export --no-dev --no-emit-project --no-hashes -o requirements.txt
```

## Configuration

All settings use the `RISKI_MCP__` prefix and can be supplied via environment
variables or a local `.env` file. See [`.env.example`](.env.example) for the full
list.

| Key | Default | HF mapping |
|-----|---------|-----------|
| `RISKI_MCP__BACKEND_URL` | — (required) | **Secret** |
| `RISKI_MCP__BACKEND_AUTH_HEADER` | none | **Secret** (if backend is protected) |
| `RISKI_MCP__REQUEST_TIMEOUT_SECONDS` | 60 | Variable |
| `RISKI_MCP__CONNECT_TIMEOUT_SECONDS` | 10 | Variable |
| `RISKI_MCP__MAX_SOURCES` | 3 | Variable |
| `RISKI_MCP__VERIFY_SSL` | true | Variable |
| `RISKI_MCP__LOG_LEVEL` | INFO | Variable |

On Hugging Face, **Space secrets and variables are injected as environment
variables** at runtime, so no extra SDK is needed. Set `RISKI_MCP__BACKEND_URL`
(and an auth header if the backend is protected) as **secrets**; the rest can be
public **variables**. The server fails fast at startup with a clear error if
`BACKEND_URL` is missing.

> **Reachability:** the public Space must be able to reach the backend over the
> internet. If the backend is on a private network, expose it at an allowed URL or
> plan a gateway. A public Space also means the backend is callable by anyone who
> finds it — consider an auth header / rate limiting on the backend side.

## Project layout

```
riski-mcp/
├── app.py                     # Gradio entrypoint + MCP server (issue #06)
├── src/riski_mcp/
│   ├── config.py              # settings (issue #05)
│   ├── models.py              # typed wire models + build_run_input (issue #02)
│   ├── client.py              # non-streaming BackendClient (issue #02)
│   ├── agui_client.py         # AG-UI SSE client + answer aggregation (issue #03)
│   ├── formatting.py          # spoken-answer + error formatting (issue #07)
│   └── tools.py               # MCP tool definitions (issue #04)
├── docs/openapi.json          # vendored backend contract
├── test/
├── requirements.txt           # HF Space runtime deps (auto-generated)
└── pyproject.toml             # local dev / CI deps (uv)
```
