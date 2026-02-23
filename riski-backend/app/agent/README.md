# RISKI Agent

The RISKI Agent is a LangGraph-based retrieval-augmented generation (RAG) pipeline that helps users research documents and proposals from the City of Munich's Council Information System (RIS).

## Graph Overview

```text
START → model → tools → guard → check_document (×N) → collect_results → model → END
```

The agent executes in two phases: **retrieval** (tool call + relevance guard) and **generation** (structured LLM answer). If any phase fails to produce usable results, the pipeline terminates early with a structured `ErrorInfo` instead of generating a hallucinated response.

## Nodes

| Node | Description |
|---|---|
| **model** | Invokes the LLM. On the first call it decides which tool to use. On the second call (after the guard) it generates a structured answer from the filtered documents. |
| **tools** | Executes the `retrieve_documents` tool via `ToolNode`. Extracts `TrackedDocument` and `TrackedProposal` entries from the tool artifact and writes them to state. |
| **guard** | Validates that a tool was called and that documents were returned. Sets `error_info` on state if not. Extracts the `user_query` for downstream use. |
| **check_document** | Runs once per document (fan-out via `Send`). Uses the LLM to judge whether a document is relevant to the user's query. Returns a `RelevanceUpdate` that the state reducer merges back. |
| **collect_results** | Convergence node after the fan-out. Inspects the relevance flags and either routes back to model (with filtered docs) or sets `error_info` if no documents survived. |

## Routing

```text
model
  ├── tool_calls present       → tools
  ├── documents already checked → END  (final answer was already generated)
  └── otherwise                → guard

tools → guard (always)

guard
  ├── error_info set    → collect_results (pass-through)
  └── documents present → check_document ×N → collect_results

collect_results
  ├── error_info set      → END
  └── relevant docs exist → model (generation pass)
```

## State

The central state object is `RiskiAgentState` (Pydantic model):

| Field | Type | Description |
|---|---|---|
| `messages` | `list[AnyMessage]` | LangChain chat history |
| `user_query` | `str` | The current user question |
| `initial_question` | `str` | The original question that started the turn |
| `tracked_documents` | `list[TrackedDocument]` | Retrieved documents with relevance flags (`is_checked`, `is_relevant`) |
| `tracked_proposals` | `list[TrackedProposal]` | Proposals (Stadtratsanträge) linked to retrieved documents |
| `error_info` | `ErrorInfo \| None` | Structured error when the pipeline cannot generate an answer |

### TrackedDocument lifecycle

1. **`retrieve_documents` tool** creates entries with `is_checked=False`.
2. **`check_document` node** sets `is_checked=True` and `is_relevant` via the custom reducer.
3. **`call_model`** (generation pass) uses only documents where `is_relevant=True`.

### Custom reducer

`tracked_documents` uses a custom reducer (`_merge_tracked_documents`) that accepts two update shapes:

- `list[TrackedDocument]` — full replacement (from the tool node).
- `list[RelevanceUpdate]` — incremental patch (from `check_document` fan-out).

## Error Handling

Instead of generating a response when no useful data is available, the agent writes an `ErrorInfo` to state:

| `error_type` | When | Message shown to user |
|---|---|---|
| `no_tool_call` | The LLM did not call any tool | "Versuchen Sie es mit einer konkreteren Frage." |
| `no_documents_found` | The tool ran but returned 0 documents | "Versuchen Sie es mit anderen Suchbegriffen." |
| `no_relevant_documents` | Documents were found but all failed the relevance check | "Versuchen Sie es mit einer präziseren Fragestellung." |

The `error_info` is propagated to the frontend via AG-UI state snapshots. The frontend renders an appropriate message instead of the generic "Unsere KI konnte keine Antwort generieren" fallback.

## Frontend Integration (AG-UI)

The agent is exposed via an AG-UI HTTP endpoint (`/api/ag-ui/riskiagent`). State snapshots are streamed to the frontend and processed by a `SnapshotStripper` that:

1. Strips `page_content` from documents to reduce payload size.
2. Merges incremental `RelevanceUpdate` entries from `check_document` fan-out nodes.
3. Passes `error_info` through to the client.

The frontend `AgUiAgentClient` diffs consecutive snapshots to detect new documents, relevance changes, and error states, then updates the UI accordingly.

## Files

| File | Purpose |
|---|---|
| `builder.py` | Constructs the `LangGraphAgent` with model, tools, checkpointer, and prompts from Langfuse |
| `riski_agent.py` | Graph definition: nodes, routing, guard logic |
| `state.py` | Pydantic state models (`RiskiAgentState`, `TrackedDocument`, `ErrorInfo`, etc.) |
| `tools.py` | `retrieve_documents` tool (vector search + proposal lookup) |
| `types.py` | Prompt templates, response schemas, agent context type |
