# Gradio app exposing the MCP server

**Labels:** `mcp`, `core`
**Depends on:** #04, #05

## Goal

Wire the tools (#04) into a Gradio app that (a) launches the MCP server at the
standard `/gradio_api/mcp/` endpoint and (b) offers a minimal human UI for manual
testing and as the Space's landing page.

## Tasks

- [ ] `app.py`: build a `gr.Blocks`/`gr.Interface` whose backing functions are the
      MCP tools from #04, and `demo.launch(mcp_server=True)`
      (or `GRADIO_MCP_SERVER=true`).
- [ ] Confirm the MCP endpoint is served (`/gradio_api/mcp/`, SSE at
      `/gradio_api/mcp/sse`) and that `tools/list` returns the expected tools.
- [ ] Minimal UI: a textbox for a question + a "Ask RISKI" button that calls
      `search_munich_ris` and shows the answer + sources. This doubles as the Space
      preview and a manual smoke test.
- [ ] Call `truststore.inject_into_ssl()` and load settings (#05) at startup.
- [ ] Set `server_name="0.0.0.0"` and respect the `PORT`/`GRADIO_SERVER_PORT` that
      HF Spaces provides.
- [ ] Graceful behavior when `BACKEND_URL` is unset (UI shows a clear config error
      rather than crashing the Space).

## Acceptance criteria

- [ ] `python app.py` locally serves the UI and the MCP endpoint.
- [ ] An MCP client (or `mcp` CLI / curl probe) lists the tools and can call
      `search_munich_ris`.
- [ ] The UI returns an answer for a real query against a configured backend.

## Notes

- Only functions you intend as tools should be exposed; avoid leaking helper
  functions into the MCP tool list.
- Keep the UI thin — the real consumer is the robot over MCP, not humans.