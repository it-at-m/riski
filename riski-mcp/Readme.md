# RISKI MCP Server

An [MCP](https://modelcontextprotocol.io) server that exposes the RISKI RIS-search
agent as a tool, deployed as a public **Hugging Face Gradio Space** so it can be
installed into the [Reachy Mini](https://huggingface.co/blog/reachy-mini)
conversation app.

A robot user asks a spoken question about Munich's *Ratsinformationssystem* (RIS);
the conversation app calls this MCP tool; the tool relays the question to the
deployed RISKI backend's AG-UI agent endpoint, aggregates the streamed answer, and
returns a concise, spoken-friendly response.

> **Status:** scaffolding. See [`docs/issues/`](docs/issues/README.md) for the full
> implementation plan. This issue (#01) sets up the project skeleton only; the
> client, tools, and Gradio app land in later issues.

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
`RISKI_MCP__BACKEND_URL` secret — it does not bundle the backend.

## Local development

```powershell
# from riski-mcp/
uv sync
Copy-Item .\.env.example .\.env -Force   # then fill in RISKI_MCP__BACKEND_URL
uv run pytest
```

Running the Gradio app and the MCP endpoint is covered by issue #06.

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
list. On Hugging Face, `RISKI_MCP__BACKEND_URL` (and any auth header) are configured
as **Space secrets**.

## Project layout

```
riski-mcp/
├── app.py                     # Gradio entrypoint + MCP server (issue #06)
├── src/riski_mcp/
│   ├── config.py              # settings (issue #05)
│   ├── agui_client.py         # AG-UI SSE client + answer aggregation (issue #03)
│   └── tools.py               # MCP tool definitions (issue #04)
├── test/
├── requirements.txt           # HF Space runtime deps
└── pyproject.toml             # local dev / CI deps (uv)
```
