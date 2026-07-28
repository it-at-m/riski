# AG-UI SSE stream client & answer aggregation

**Labels:** `mcp`, `core`
**Depends on:** #02

## Goal

Implement the core of the wrapper: an async client that POSTs a `RunAgentInput` to
`/api/ag-ui/riskiagent`, consumes the AG-UI Server-Sent Event stream, and folds it
into a single result object:

```python
@dataclass
class RiskiAnswer:
    answer: str                 # final, human-readable text
    documents: list[dict]       # tracked_documents (slim) from last STATE_SNAPSHOT
    proposals: list[dict]       # tracked_proposals
    error: ErrorInfo | None     # mapped backend error_info, if any
```

This is the hardest issue — everything downstream depends on getting it right.

## Event contract (from `riski-backend/app/api/routers/ag_ui.py`)

The backend emits these event types (others are filtered out server-side):
`RUN_STARTED`, `STEP_STARTED`, `STEP_FINISHED`, `TOOL_CALL_START`,
`TOOL_CALL_ARGS`, `TOOL_CALL_END`, `STATE_SNAPSHOT`, `TEXT_MESSAGE_START`,
`TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`, `RUN_FINISHED`, `RUN_ERROR`.

Key facts to handle:
- **Final answer** streams as `TEXT_MESSAGE_CONTENT` deltas. The server only lets
  through text from the `model` node *after* a tool call, so concatenating
  `TEXT_MESSAGE_CONTENT` deltas between the relevant `TEXT_MESSAGE_START`/`_END`
  yields the answer. The content is a **JSON `StructuredAgentResponse`** — parse it
  and extract the user-facing field (e.g. `.response`); fall back to raw text if it
  isn't valid JSON.
- **Documents/proposals/errors** arrive in `STATE_SNAPSHOT.snapshot` as
  `tracked_documents`, `tracked_proposals`, `user_query`, and `error_info`. Keep the
  **last** snapshot; `error_info` is `null` when there's no error.
- **`error_info`** has `error_type` ∈ {`no_tool_call`, `no_documents_found`,
  `no_relevant_documents`, `timeout`, `content_policy_violation`, ...}, a German
  `message`, and optional `suggestions`. When present, there is usually no answer —
  surface the message (see #07).
- **`RUN_ERROR`** → the backend hit an internal error; map to a generic failure.

## Tasks

- [ ] Use `httpx.AsyncClient.stream("POST", ...)` and parse SSE frames
      (`event:` / `data:` lines). Confirm the content type the backend uses via
      `EventEncoder` (`text/event-stream`); the Accept header is echoed — send
      `Accept: text/event-stream`.
- [ ] State machine: accumulate text deltas, track current node, retain last
      `STATE_SNAPSHOT`, capture `RUN_ERROR`, stop on `RUN_FINISHED`.
- [ ] Parse the final text as `StructuredAgentResponse` JSON; degrade gracefully.
- [ ] Map `error_info` → `RiskiAnswer.error`; if set and no answer, leave `answer`
      empty (caller formats the spoken message).
- [ ] Enforce an overall timeout (the agent can take many seconds; default generous,
      configurable in #05) and cancel the stream cleanly.
- [ ] Robustness: malformed/partial SSE frames, mid-stream disconnects, empty stream.

## Acceptance criteria

- [ ] Given a recorded happy-path SSE stream fixture, returns the expected `answer`
      + documents + proposals.
- [ ] Given a `no_documents_found` stream, returns `error` set and empty `answer`.
- [ ] Given a `RUN_ERROR` stream, returns a generic error result, no exception.
- [ ] Respects the configured timeout and cancels the underlying request.

## Notes

- Capture real SSE fixtures by running the backend locally and saving a stream for
  a known query — reuse them in #10 tests.
- Do not import backend internals; treat the event stream as the contract.