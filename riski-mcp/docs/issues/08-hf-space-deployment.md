# Hugging Face Space deployment

**Labels:** `mcp`, `deployment`
**Depends on:** #06

## Goal

Publish `riski-mcp` as a **public Gradio Space** with the metadata and tags required
for Reachy Mini discovery, plus the secrets needed to reach the backend.

## Tasks

- [ ] Add HF Space README front-matter (`Readme.md` / `README.md` in the Space root):
  ```yaml
  ---
  title: RISKI RIS Search (MCP)
  emoji: 🏛️
  colorFrom: blue
  colorTo: indigo
  sdk: gradio
  sdk_version: "<pin>"
  app_file: app.py
  pinned: false
  tags:
    - mcp
    - reachy-mini-tool
  ---
  ```
- [ ] `requirements.txt` present and complete (`gradio[mcp]`, `httpx`, `pydantic`,
      `pydantic-settings`, `truststore`). Verify the Space builds from it.
- [ ] Configure Space **secrets**: `RISKI_MCP__BACKEND_URL` (+ auth header if any).
- [ ] Decide hosting of the Space repo: standalone HF repo vs. mirror/subtree of
      `riski-mcp/`. Document the sync workflow (manual push vs. GitHub Action to HF).
- [ ] Verify the live MCP endpoint: `https://<owner>-<space>.hf.space/gradio_api/mcp/`
      responds and `tools/list` returns our tools.
- [ ] Confirm the Space stays warm enough / note cold-start behavior for robot UX.

## Acceptance criteria

- [ ] Space builds and runs publicly; landing UI works.
- [ ] MCP endpoint is reachable and lists the tools.
- [ ] `search_munich_ris` works end-to-end on the live Space against the deployed
      backend.
- [ ] Tags `mcp` + `reachy-mini-tool` are set for discoverability.

## Notes

- The Space and the backend must agree on network reachability — if the backend is
  on a private network, the Space (public internet) cannot reach it. Confirm the
  backend is exposed at a public/allowed URL, or plan a gateway. **Raise early.**
- Public Space ⇒ the backend is effectively callable by anyone who finds the Space.
  Consider an auth header / rate limiting on the backend side (see #07, #11).