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
    RelevanceUpdate,
    RiskiAgentState,
    RiskiAgentStateUpdate,
    TrackedDocument,
    TrackedProposal,
)
from .types import (
    CHECK_DOCUMENT_PROMPT_TEMPLATE,
    NO_RESULTS_RESPONSE,
    SYSTEM_PROMPT,
    DocumentRelevanceVerdict,
    StructuredAgentResponse,
)

logger: Logger = getLogger()

NODE_MODEL = "model"
NODE_TOOLS = "tools"
NODE_GUARD = "guard"
NODE_CHECK_DOCUMENT = "check_document"
NODE_COLLECT_RESULTS = "collect_results"


def _route_after_model(state: RiskiAgentState) -> str:
    """Route after the model node.

    - tool_calls present → "tools"
    - tracked documents already checked & relevant → END (final answer done)
    - no tool calls and no prior results → "guard" (will emit no-results)
    """
    last_message = state["messages"][-1] if state["messages"] else None
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return NODE_TOOLS
    if state.has_documents and state.all_checked:
        return END
    return NODE_GUARD


def _route_after_collect(state: RiskiAgentState) -> str:
    """Route after collect_results: back to model if relevant docs exist, else end."""
    last_message = state["messages"][-1] if state["messages"] else None
    if isinstance(last_message, AIMessage) and last_message.additional_kwargs.get("__guard_terminal"):
        return END
    return NODE_MODEL


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

        if not has_any_tool_call:
            logger.warning("Guard: Model did not call any tool. Returning no-results response.")
            return {
                "messages": [
                    AIMessage(
                        content=NO_RESULTS_RESPONSE,
                        additional_kwargs={"__guard_terminal": True},
                    )
                ],
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
                "messages": [
                    AIMessage(
                        content=NO_RESULTS_RESPONSE,
                        additional_kwargs={"__guard_terminal": True},
                    )
                ],
            }

        return {
            "user_query": user_query,
            "initial_question": user_query,
        }

    # ----- fan-out conditional edge (Send per document) -----
    def fan_out_checks(state: RiskiAgentState) -> list[Send]:
        """Create a ``Send`` per tracked document for parallel relevance checking.

        If the guard already emitted a terminal AIMessage (no docs / no tool
        call), skip the fan-out and go straight to collect_results.
        """
        last = state["messages"][-1] if state["messages"] else None
        if isinstance(last, AIMessage) and last.additional_kwargs.get("__guard_terminal"):
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
        last = state["messages"][-1] if state["messages"] else None
        if isinstance(last, AIMessage) and last.additional_kwargs.get("__guard_terminal"):
            return {}

        total = len(state.tracked_documents)
        relevant = state.relevant_documents
        logger.info("Guard: %d/%d documents passed relevance check.", len(relevant), total)

        if not relevant:
            logger.info("Guard: No documents survived relevance check. Returning no-results response.")
            return {
                "messages": [
                    AIMessage(
                        content=NO_RESULTS_RESPONSE,
                        additional_kwargs={"__guard_terminal": True},
                    )
                ]
            }

        # State already contains the updated tracked_documents with
        # is_checked/is_relevant flags – nothing else to write.
        return {}

    return guard, fan_out_checks, check_document, collect_results


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

        if relevant_docs:
            # -- Generation pass: we have guard-filtered documents --
            question = state.get("initial_question") or state.get("user_query") or ""

            synthetic_context = HumanMessage(
                content="Nutze die folgenden gefilterten Dokumente und Vorschläge, um die Nutzerfrage zu beantworten."
            )
            docs_payload = {
                "documents": [d.model_dump(exclude={"is_checked", "is_relevant", "relevance_reason"}) for d in relevant_docs],
                "proposals": [p.model_dump() for p in state.tracked_proposals],
            }
            docs_message = HumanMessage(content=json.dumps(docs_payload))

            # Build a clean message list: system + human messages only (skip ToolMessages)
            base_messages: list[AnyMessage] = []
            for msg in state["messages"]:
                if isinstance(msg, ToolMessage):
                    continue
                base_messages.append(msg)

            if question:
                base_messages.insert(0, HumanMessage(content=question))

            messages = [system_message, *base_messages, synthetic_context, docs_message]
            structured_model = chat_model.with_structured_output(StructuredAgentResponse)
            response = await structured_model.ainvoke(messages)
            if isinstance(response, StructuredAgentResponse):
                ai_msg = AIMessage(content=json.dumps(response.model_dump()))
            else:
                ai_msg = AIMessage(content=json.dumps(response))
            return {"messages": [ai_msg]}

        # -- First pass: extract user query and let the model decide which tool(s) to call --
        user_query = state.get("user_query", "") or state.get("initial_question", "")
        if not user_query:
            for msg in state["messages"]:
                if isinstance(msg, HumanMessage):
                    user_query = msg.content if isinstance(msg.content, str) else str(msg.content)
                    break

        messages = [system_message, *state["messages"]]
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
        """
        # Delegate actual tool execution to the standard ToolNode
        result: dict[str, Any] = await tool_node.ainvoke(state)
        tool_messages: list[ToolMessage] = result.get("messages", [])

        # Extract tracked state from the artifact(s)
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
    graph.add_edge(NODE_TOOLS, NODE_GUARD)
    graph.add_conditional_edges(NODE_GUARD, fan_out_checks, [NODE_CHECK_DOCUMENT, NODE_COLLECT_RESULTS])
    graph.add_edge(NODE_CHECK_DOCUMENT, NODE_COLLECT_RESULTS)
    graph.add_conditional_edges(NODE_COLLECT_RESULTS, _route_after_collect, {NODE_MODEL: NODE_MODEL, END: END})

    return graph
