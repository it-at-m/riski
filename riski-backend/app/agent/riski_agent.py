import json
from logging import Logger
from typing import Any, Iterable

from app.utils.logging import getLogger
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langfuse.model import TextPromptClient
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Send

from .state import (
    DocumentCheckInput,
    ErrorInfo,
    RelevanceUpdate,
    RiskiAgentState,
    RiskiAgentStateUpdate,
    TrackedDocument,
    TrackedProposal,
)
from .tools import (
    get_agent_capabilities,
)
from .types import (
    CHECK_DOCUMENT_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
    DocumentRelevanceVerdict,
    StructuredAgentResponse,
)

logger: Logger = getLogger()


def filter_tracked_proposals(
    proposals: list[TrackedProposal],
    relevant_docs: list[TrackedDocument],
) -> list[TrackedProposal]:
    """Filter proposals to those linked to relevant documents.

    Proposals without ``source_document_ids`` are kept by default.
    """
    if not proposals:
        return []

    relevant_ids = {doc.id for doc in relevant_docs if doc.id}
    if not relevant_ids:
        return []

    filtered: list[TrackedProposal] = []
    for proposal in proposals:
        source_ids = proposal.source_document_ids
        if not source_ids or any(doc_id in relevant_ids for doc_id in source_ids):
            filtered.append(proposal)

    return filtered


NODE_MODEL = "model"
NODE_TOOLS = "tools"
NODE_GUARD = "guard"
NODE_CHECK_DOCUMENT = "check_document"
NODE_COLLECT_RESULTS = "collect_results"


def _is_capabilities_answer(messages: list[AnyMessage]) -> bool:
    """Return True if the last AIMessage was generated in response to get_agent_capabilities."""
    # Walk backwards: skip the last AIMessage (the answer), then look for the
    # capabilities ToolMessage as the very next message before it.
    found_last_ai = False
    for msg in reversed(messages):
        if not found_last_ai:
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                found_last_ai = True
            continue
        # First message before the final AIMessage
        return isinstance(msg, ToolMessage) and msg.name == get_agent_capabilities.name
    return False


def _route_after_model(state: RiskiAgentState) -> str:
    """Route after the model node.

    - tool_calls present → "tools"
    - model just answered a capabilities question → END
    - tracked documents already checked & relevant → END  (final answer done)
    - no tool calls and no prior results → "guard" (will emit no-results)
    """
    last_message = state["messages"][-1] if state["messages"] else None
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return NODE_TOOLS
    if _is_capabilities_answer(state["messages"]):
        return END
    if state.has_documents and state.all_checked:
        return END
    return NODE_GUARD


def _route_after_collect(state: RiskiAgentState) -> str:
    """Route after collect_results: back to model if relevant docs exist, else end."""
    if state.has_error:
        return END
    return NODE_MODEL


def _route_after_tools(state: RiskiAgentState) -> str:
    """Route after the tools node.

    - ``get_agent_capabilities`` was called → back to model for final LLM answer.
    - Otherwise → guard as usual.
    """
    last_message = state["messages"][-1] if state["messages"] else None
    if isinstance(last_message, ToolMessage) and last_message.name == get_agent_capabilities.name:
        return NODE_MODEL
    return NODE_GUARD


def build_guard_nodes(
    chat_model: ChatOpenAI,
    check_document_prompt_template: str | TextPromptClient = CHECK_DOCUMENT_PROMPT_TEMPLATE,
):
    """Build and return the three guard-related node functions + fan-out router.

    Returns
    -------
    tuple of (guard, fan_out_checks, check_document, collect_results)
        Ready to be wired into the main ``StateGraph``.
    """

    # ----- guard node: validate state and extract user query -----
    async def guard(state: RiskiAgentState) -> dict[str, Any]:
        """Validate that tools were called and documents are present in state.

        ``tracked_documents`` and ``tracked_proposals`` are already written
        by the custom ``run_tools`` node.  This node only:
        1. Handles the edge case where no tool was called.
        2. Handles the edge case where the tool returned zero documents.
        3. Ensures ``user_query`` / ``initial_question`` are set.
        """
        messages = state["messages"]
        has_any_tool_call = any(isinstance(m, ToolMessage) for m in messages)

        # If the only tool called was get_agent_capabilities, the answer was
        # already generated – guard should never be reached in this case, but
        # defend against it here to avoid a false no_tool_call error.
        if has_any_tool_call and all(
            isinstance(m, ToolMessage) and m.name == get_agent_capabilities.name for m in messages if isinstance(m, ToolMessage)
        ):
            logger.warning("Guard reached after get_agent_capabilities – this should not happen. Skipping.")
            return {}

        if not has_any_tool_call:
            logger.warning("Guard: Model did not call any tool. Returning no-results response.")
            return {
                "error_info": ErrorInfo(
                    error_type="no_tool_call",
                    message="Das Modell hat kein Werkzeug aufgerufen. Bitte versuchen Sie es mit einer konkreteren Frage.",
                ),
            }

        # Extract user query from state (preferred) or from messages (fallback)
        user_query = state.get("user_query", "") or state.get("initial_question", "")
        if not user_query:
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
                    break

        if not state.tracked_documents:
            logger.info("Guard: Tool returned no documents. Returning no-results response.")
            return {
                "error_info": ErrorInfo(
                    error_type="no_documents_found",
                    message="Es wurden leider keine Dokumente zu Ihrer Anfrage gefunden. Versuchen Sie es mit anderen Suchbegriffen.",
                ),
            }

        return {
            "user_query": user_query,
            "initial_question": user_query,
        }

    # ----- fan-out conditional edge (Send per document) -----
    def fan_out_checks(state: RiskiAgentState) -> list[Send]:
        """Create a ``Send`` per tracked document for parallel relevance checking.

        If the guard already set error_info (no docs / no tool call),
        skip the fan-out and go straight to collect_results.
        """
        if state.has_error:
            return [Send(NODE_COLLECT_RESULTS, state)]

        return [
            Send(
                NODE_CHECK_DOCUMENT,
                DocumentCheckInput(
                    doc_index=i,
                    doc=doc.model_dump(),
                    user_query=state["user_query"],
                ),
            )
            for i, doc in enumerate(state.tracked_documents)
        ]

    # ----- check_document node (runs once per document via Send) -----
    async def check_document(state: DocumentCheckInput) -> dict[str, list[RelevanceUpdate]]:
        """Check a single document for relevance using the LLM.

        Returns a ``RelevanceUpdate`` which the custom reducer on
        ``tracked_documents`` will merge back into the main list.
        """
        doc = state["doc"]
        user_query = state["user_query"]

        doc_id: str = doc.get("id", "")
        metadata: dict = doc.get("metadata", {})
        doc_name: str = metadata.get("name", metadata.get("title", doc_id or "Dokument"))
        page_content: str = doc.get("page_content", "")
        snippet = page_content[:2000]

        if isinstance(check_document_prompt_template, TextPromptClient):
            check_prompt = check_document_prompt_template.compile(
                user_query=user_query,
                doc_name=doc_name,
                snippet=snippet,
            )
        else:
            check_prompt = check_document_prompt_template.format(
                user_query=user_query,
                doc_name=doc_name,
                snippet=snippet,
            )

        relevance_model = chat_model.with_structured_output(DocumentRelevanceVerdict)
        try:
            verdict_raw = await relevance_model.ainvoke(
                [
                    SystemMessage(content="Du bist ein Relevanz-Prüfer. Bewerte ob ein Dokument relevant für eine Benutzeranfrage ist."),
                    HumanMessage(content=check_prompt),
                ]
            )
            if isinstance(verdict_raw, DocumentRelevanceVerdict):
                verdict = verdict_raw
            elif isinstance(verdict_raw, dict):
                verdict = DocumentRelevanceVerdict(
                    relevant=bool(verdict_raw.get("relevant", True)),
                    reason=str(verdict_raw.get("reason", "Prüfung nicht eindeutig.")),
                )
            else:
                verdict = DocumentRelevanceVerdict(relevant=True, reason="Prüfung nicht eindeutig.")
        except Exception:
            logger.warning("Guard: LLM relevance check failed for doc %s, assuming relevant.", doc_id, exc_info=True)
            verdict = DocumentRelevanceVerdict(relevant=True, reason="Prüfung fehlgeschlagen, Dokument wird beibehalten.")

        if verdict.relevant:
            logger.debug("Guard: Document '%s' is relevant: %s", doc_name, verdict.reason)
        else:
            logger.info("Guard: Document '%s' is NOT relevant: %s", doc_name, verdict.reason)

        return {
            "tracked_documents": [
                RelevanceUpdate(
                    doc_id=doc_id,
                    is_relevant=verdict.relevant,
                    reason=verdict.reason,
                )
            ]
        }

    # ----- collect_results node (convergence after fan-out) -----
    async def collect_results(state: RiskiAgentState) -> dict[str, Any]:
        """Check tracked documents for relevance results and route accordingly.

        After the reducer has merged all ``RelevanceUpdate`` entries, this
        node simply inspects ``state.tracked_documents`` using the
        convenience properties.
        """
        # If the guard already short-circuited, just pass through
        if state.has_error:
            return {}

        total = len(state.tracked_documents)
        relevant = state.relevant_documents
        logger.info("Guard: %d/%d documents passed relevance check.", len(relevant), total)

        if not relevant:
            logger.info("Guard: No documents survived relevance check. Returning no-results response.")
            # Collect per-document rejection reasons for the frontend
            rejection_reasons = [
                {"name": d.metadata.get("name", d.metadata.get("title", d.id or "Dokument")), "reason": d.relevance_reason}
                for d in state.tracked_documents
                if d.is_checked and not d.is_relevant
            ]
            return {
                "error_info": ErrorInfo(
                    error_type="no_relevant_documents",
                    message="Es wurden Dokumente gefunden, aber keines davon war für Ihre Anfrage relevant. Versuchen Sie es mit einer präziseren Frage.",
                    details={
                        "total_checked": total,
                        "reasons": rejection_reasons,
                    },
                ),
            }

        filtered_proposals = filter_tracked_proposals(state.tracked_proposals, relevant)
        if filtered_proposals != state.tracked_proposals:
            return {"tracked_proposals": filtered_proposals}

        # State already contains the updated tracked_documents with
        # is_checked/is_relevant flags – nothing else to write.
        return {}

    return guard, fan_out_checks, check_document, collect_results


def _sanitize_messages(messages: list[AnyMessage]) -> list[AnyMessage]:
    """Remove any ToolMessages that are not preceded by an AIMessage with matching tool_calls.

    OpenAI rejects a message sequence where a ``ToolMessage`` appears without a
    directly preceding ``AIMessage`` that contains the corresponding ``tool_call_id``.
    This can happen when the message history is reconstructed across turns (e.g.
    after the generation pass strips ToolMessages but leaves AIMessages with
    tool_calls, or vice-versa).
    """
    # Collect all tool_call_ids that are covered by an AIMessage in the list
    covered_ids: set[str] = set()
    for msg in messages:
        if isinstance(msg, AIMessage):
            for tc in msg.tool_calls or []:
                if tc.get("id"):
                    covered_ids.add(str(tc["id"]))

    sanitized: list[AnyMessage] = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            if msg.tool_call_id not in covered_ids:
                logger.debug("Dropping orphan ToolMessage (tool_call_id=%s)", msg.tool_call_id)
                continue
        sanitized.append(msg)

    # Also drop AIMessages whose tool_calls have no matching ToolMessage response
    # (avoids the reverse problem: AIMessage with tool_calls but no ToolMessage)
    tool_message_ids: set[str] = {msg.tool_call_id for msg in sanitized if isinstance(msg, ToolMessage)}
    result: list[AnyMessage] = []
    for msg in sanitized:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            missing = [tc["id"] for tc in msg.tool_calls if tc["id"] not in tool_message_ids]
            if missing:
                logger.debug("Dropping AIMessage with unmatched tool_call_ids: %s", missing)
                continue
        result.append(msg)
    return result


def build_riski_graph(
    chat_model: ChatOpenAI,
    tools: Iterable[Any],
    system_prompt: str = SYSTEM_PROMPT,
    check_document_prompt_template: str | TextPromptClient = CHECK_DOCUMENT_PROMPT_TEMPLATE,
) -> StateGraph:
    """Build the RISKI agent graph with core nodes and guard pipeline."""
    tools = list(tools)
    model_with_tools = chat_model.bind_tools(tools)
    system_message = SystemMessage(content=system_prompt)

    # -- Node: call the model --
    async def call_model(state: RiskiAgentState) -> RiskiAgentStateUpdate:
        """Invoke the LLM.

        When relevant documents are available in state (after the guard),
        they are injected directly into the prompt — no ToolMessage parsing.
        On the first call (no documents yet) the model decides which tool to call.
        """
        relevant_docs = state.relevant_documents

        # -- Capabilities pass: model was routed back after get_agent_capabilities --
        # With add_messages the full history is intact, so state["messages"] already
        # contains the correct [... HumanMessage, AIMessage(tool_calls), ToolMessage]
        # sequence that OpenAI expects.
        last_message = state["messages"][-1] if state["messages"] else None
        if isinstance(last_message, ToolMessage) and last_message.name == get_agent_capabilities.name:
            caps_messages: list[AnyMessage] = [system_message, *state["messages"]]
            logger.debug(
                "Capabilities pass message sequence: %s",
                [type(m).__name__ for m in caps_messages],
            )
            response = await chat_model.ainvoke(caps_messages)
            return {"messages": [response]}

        if relevant_docs:
            # -- Generation pass: we have guard-filtered documents --
            # Build a clean prompt: keep only non-ToolMessages from history
            # (OpenAI rejects AIMessage(tool_calls) without a matching ToolMessage
            # if that pair is mixed with injected document messages), then append
            # the retrieved documents as a synthetic context message.
            synthetic_context = HumanMessage(
                content="Nutze die folgenden gefilterten Dokumente und Vorschläge, um die Nutzerfrage zu beantworten."
            )
            docs_payload = {
                "documents": [d.model_dump(exclude={"is_checked", "is_relevant", "relevance_reason"}) for d in relevant_docs],
                "proposals": [p.model_dump() for p in state.tracked_proposals],
            }
            docs_message = HumanMessage(content=json.dumps(docs_payload))

            # Strip AIMessage(tool_calls)/ToolMessage pairs — they are no longer
            # meaningful and would make the sequence invalid for the generation call.
            base_messages = [
                msg
                for msg in state["messages"]
                if not isinstance(msg, (ToolMessage, AIMessage)) or (isinstance(msg, AIMessage) and not msg.tool_calls)
            ]

            messages = [system_message, *base_messages, synthetic_context, docs_message]
            structured_model = chat_model.with_structured_output(StructuredAgentResponse)
            try:
                response = await structured_model.ainvoke(messages)
                try:
                    if isinstance(response, StructuredAgentResponse):
                        content = json.dumps(response.model_dump())
                    elif isinstance(response, dict):
                        content = json.dumps(response)
                    elif isinstance(response, str):
                        content = response
                    else:
                        content = json.dumps({"response": str(response)})
                except (TypeError, ValueError):
                    logger.warning(
                        "Structured generation parse failed, returning raw response.",
                        exc_info=True,
                    )
                    content = str(response)
            except Exception:
                logger.warning(
                    "Structured generation failed, returning safe response.",
                    exc_info=True,
                )
                content = json.dumps(
                    {
                        "error": "structured_generation_failed",
                        "response": "Antwort konnte nicht strukturiert erzeugt werden.",
                    }
                )

            ai_msg = AIMessage(content=content)
            return {"messages": [ai_msg]}

        # -- First pass: extract user query and let the model decide which tool(s) to call --
        user_query = state.get("user_query", "") or state.get("initial_question", "")
        if not user_query:
            for msg in state["messages"]:
                if isinstance(msg, HumanMessage):
                    user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
                    break

        messages = [system_message, *_sanitize_messages(state["messages"])]
        response = await model_with_tools.ainvoke(messages)

        result = RiskiAgentStateUpdate(messages=[response])
        if user_query:
            result["user_query"] = user_query
            result["initial_question"] = user_query
        return result

    # -- Node: run tools and write tracked state directly --
    tool_node = ToolNode(tools)

    async def run_tools(state: RiskiAgentState) -> RiskiAgentStateUpdate:
        """Run tools via ToolNode and extract tracked state from the artifact.

        This replaces the plain ``ToolNode`` so that ``tracked_documents``
        and ``tracked_proposals`` are written to state immediately —
        no extra guard parsing step needed.

        Special case: if ``get_agent_capabilities`` was called, the capabilities
        text is used to synthesize a final ``AIMessage`` directly — no second
        LLM call is required and the message history stays clean.
        """
        # Delegate actual tool execution to the standard ToolNode
        result: dict[str, Any] = await tool_node.ainvoke(state)
        tool_messages: list[ToolMessage] = result.get("messages", [])

        # -- Short-circuit for get_agent_capabilities -------------------------
        for msg in tool_messages:
            if isinstance(msg, ToolMessage) and msg.name == get_agent_capabilities.name:
                # Return only the ToolMessage – the model node will do the final LLM call
                return {"messages": [msg]}

        # -- Normal path: extract tracked state from the artifact(s) ----------
        tracked_docs: list[TrackedDocument] = []
        tracked_proposals: list[TrackedProposal] = []

        for msg in tool_messages:
            if not isinstance(msg, ToolMessage) or not isinstance(msg.artifact, dict):
                continue
            for d in msg.artifact.get("documents", []):
                if isinstance(d, dict):
                    tracked_docs.append(TrackedDocument(**d))
            for p in msg.artifact.get("proposals", []):
                if isinstance(p, dict):
                    tracked_proposals.append(TrackedProposal(**p))

        state_update: RiskiAgentStateUpdate = {"messages": tool_messages}
        if tracked_docs:
            state_update["tracked_documents"] = tracked_docs
        if tracked_proposals:
            state_update["tracked_proposals"] = tracked_proposals

        return state_update

    # -- Build the guard nodes --
    guard, fan_out_checks, check_document, collect_results = build_guard_nodes(
        chat_model,
        check_document_prompt_template=check_document_prompt_template,
    )

    graph = StateGraph(RiskiAgentState)

    graph.add_node(NODE_MODEL, call_model)
    graph.add_node(NODE_TOOLS, run_tools)
    graph.add_node(NODE_GUARD, guard)
    graph.add_node(NODE_CHECK_DOCUMENT, check_document)
    graph.add_node(NODE_COLLECT_RESULTS, collect_results)

    graph.add_edge(START, NODE_MODEL)
    graph.add_conditional_edges(NODE_MODEL, _route_after_model, {NODE_TOOLS: NODE_TOOLS, NODE_GUARD: NODE_GUARD, END: END})
    graph.add_conditional_edges(NODE_TOOLS, _route_after_tools, {NODE_MODEL: NODE_MODEL, NODE_GUARD: NODE_GUARD})
    graph.add_conditional_edges(NODE_GUARD, fan_out_checks, [NODE_CHECK_DOCUMENT, NODE_COLLECT_RESULTS])
    graph.add_edge(NODE_CHECK_DOCUMENT, NODE_COLLECT_RESULTS)
    graph.add_conditional_edges(NODE_COLLECT_RESULTS, _route_after_collect, {NODE_MODEL: NODE_MODEL, END: END})

    return graph
