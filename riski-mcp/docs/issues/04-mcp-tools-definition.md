# MCP tool definitions (stateless, voice-friendly)

**Labels:** `mcp`
**Depends on:** #03

## Goal

Define the Python functions that become MCP tools. With Gradio, each exposed
function is auto-converted to an MCP tool: the **name**, **docstring**
(→ description), and **type hints** (→ input schema) are what the robot's LLM sees,
so they must be precise and LLM-friendly.

## Proposed tools

1. **`search_munich_ris(question: str) -> str`** (primary)
   - Relays `question` to the RISKI agent via the AG-UI client (#03) and returns a
     concise, spoken-friendly answer including brief source references.
   - Stateless: fresh `threadId`/`runId` per call.
   - Docstring must tell the LLM *when* to use it: questions about Munich city
     council documents, motions/proposals (*Stadtratsanträge*), and RIS content.
2. **`get_riski_capabilities() -> str`** (optional, recommended)
   - Returns what the agent can answer about, sourced from the agent's own
     capabilities (the backend exposes this internally via `get_agent_capabilities`;
     if not reachable through the public API, derive a static description and note
     the gap). Helps the robot's planner decide when to call `search_munich_ris`.
3. **`riski_health() -> str`** (optional)
   - Wraps `/api/healthz`; useful for diagnostics. Consider excluding from the
     robot's `tools.txt` to avoid LLM noise.

## Tasks

- [ ] Implement the tools in `src/riski_mcp/tools.py` as plain async/sync functions
      with full type hints + Google-style docstrings (Gradio reads `Args:`).
- [ ] Keep outputs **strings** optimized for text-to-speech: short answer first,
      then up to ~3 sources ("Quelle: <name>"), no raw JSON, no markdown tables.
- [ ] Truncate/strip long content; the robot speaks the result aloud.
- [ ] Decide which tools to enable by default in the documented `tools.txt`.
- [ ] Ensure no hidden state between calls (no module-level mutable caches keyed by
      session).

## Acceptance criteria

- [ ] Each tool has a clear docstring + typed signature that produces a sensible MCP
      input schema (verify via the MCP `tools/list` probe in #10).
- [ ] `search_munich_ris("...")` returns a concise spoken-friendly string end-to-end
      against a live backend.
- [ ] Error paths return a friendly sentence (see #07), never a traceback.

## Notes

- Tool names become namespaced on the robot as `<space_alias>__search_munich_ris`.
  Pick names that read well after namespacing.
- Keep the tool surface small — fewer, well-described tools work better with the
  conversation app's planner.