# Reachy Mini integration & docs

**Labels:** `mcp`, `reachy-mini`, `docs`
**Depends on:** #08

## Goal

Document and verify the end-to-end path: installing the Space into the Reachy Mini
conversation app and asking a RIS question by voice.

## Tasks

- [ ] Write `riski-mcp/README` "Use with Reachy Mini" section:
  ```bash
  reachy-mini-conversation-app tool-spaces add <owner>/<space>
  ```
  Explain that `add` validates the Space, probes the MCP endpoint, discovers tools,
  and appends tool IDs to the active profile's `tools.txt`.
- [ ] Document the resulting namespaced tool name
      (`<space_alias>__search_munich_ris`) and which tools to keep enabled in
      `tools.txt` (likely just `search_munich_ris`, optionally
      `get_riski_capabilities`; exclude `riski_health`).
- [ ] Provide 3–5 example spoken prompts in German that should route to the tool
      (e.g. "Frag das RIS nach Anträgen zum Radverkehr in München.").
- [ ] Verify on real hardware or the conversation-app simulator: install → ask →
      hear a correct answer. Capture a short demo / transcript.
- [ ] Note known limitations: latency (agent + network), language, cold starts, no
      guaranteed parallel tool orchestration.

## Acceptance criteria

- [ ] `tool-spaces add` succeeds and discovers `search_munich_ris`.
- [ ] A spoken RIS question yields a correct, concise answer via the robot.
- [ ] README documents install, enabled tools, example prompts, and limitations.

## Notes

- If discovery fails, the most common causes are: Space not public, not a Gradio
  SDK Space, or the MCP endpoint not exposed (`mcp_server=True` missing). Cross-check
  with #06/#08.