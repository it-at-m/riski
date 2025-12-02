from __future__ import annotations

import time
from functools import lru_cache
from typing import Annotated, NotRequired, TypedDict

from ag_ui_langgraph import LangGraphAgent
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

_RETRIEVAL_DELAY_SECONDS = 0.4
_RESPONSE_DELAY_SECONDS = 0.6
_RETRIEVAL_NODE = "RETRIEVAL"
_GENERATE_NODE = "GENERATE"


class RiskiAgentState(TypedDict, total=False):
    """State propagated between LangGraph nodes for the mock agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    documents: NotRequired[list[Document]]
    proposals: NotRequired[list[Document]]


def _simulate_delay(duration: float) -> None:
    """Sleep for a short amount of time to mimic remote processing."""

    if duration <= 0:
        return
    time.sleep(duration)


def _extract_latest_question(messages: list[BaseMessage] | None) -> str:
    """Return the last human utterance from the conversation history."""

    if not messages:
        return ""

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            if isinstance(message.content, str):
                return message.content
            if isinstance(message.content, list):
                text_fragments = [
                    fragment.get("text", "")
                    for fragment in message.content
                    if isinstance(fragment, dict) and fragment.get("type") == "text"
                ]
                merged = " ".join(text_fragments).strip()
                if merged:
                    return merged
    return ""


def _build_document_candidates(question: str) -> list[Document]:
    """Return a list of pseudo-documents tailored to the question topic."""

    summary_suffix = " in Bezug auf '%s'" % question if question else " für die zuletzt gestellte Frage"
    template = {
        "snippet": "Allgemeine Hinweise und Kontextinformation %s." % summary_suffix,
    }
    return [
        Document(
            page_content=template["snippet"],
            metadata={
                "id": "total-echtes-doc-1",
                "identifier": "BR-2024-001",
                "title": "Wissen zu riskanten, streng geheimen KI Protokollen",
                "source": "mock://documents/1",
                "risUrl": "https://riski.mock/documents/1",
                "score": 0.92,
                "size": 2,
            },
        ),
        Document(
            page_content=template["snippet"],
            metadata={
                "id": "total-echtes-doc-2",
                "identifier": "BR-2024-002",
                "title": "Weniger relevantes Wissen",
                "source": "mock://documents/2",
                "risUrl": "https://riski.mock/documents/2",
                "score": 0.50,
                "size": 3,
            },
        ),
    ]


def _build_proposal_candidates(question: str) -> list[Document]:
    """Return a list of pseudo-proposals to mirror document structure."""

    topic = "'%s'" % question if question else "aktuelles Thema"
    base_metadata = {
        "source": "mock://proposals",
        "risUrl": "https://riski.mock/proposals",
        "size": 1,
    }

    return [
        Document(
            page_content="Beschlussvorlage mit Schwerpunkt %s." % topic,
            metadata={
                **base_metadata,
                "id": "proposal-1",
                "identifier": "BV-2024-001",
                "title": "Maßnahmenpaket für sichere KI",
                "source": f"{base_metadata['source']}/1",
                "risUrl": f"{base_metadata['risUrl']}/1",
            },
        ),
        Document(
            page_content="Alternativvorschlag zur weiteren Diskussion %s." % topic,
            metadata={
                **base_metadata,
                "id": "proposal-2",
                "identifier": "BV-2024-002",
                "title": "Pilotprojekt Datenräume",
                "source": f"{base_metadata['source']}/2",
                "risUrl": f"{base_metadata['risUrl']}/2",
            },
        ),
    ]


def _retrieve_documents(state: RiskiAgentState) -> RiskiAgentState:
    """Mock retriever returning pseudo-documents with a short delay."""
    _simulate_delay(_RETRIEVAL_DELAY_SECONDS)
    question = _extract_latest_question(state.get("messages"))
    docs = _build_document_candidates(question)
    proposals = _build_proposal_candidates(question)
    return {"documents": docs, "proposals": proposals}


def _generate(state: RiskiAgentState) -> RiskiAgentState:
    """Return a richer mock response referencing retrieved documents."""

    _simulate_delay(_RESPONSE_DELAY_SECONDS)
    question = _extract_latest_question(state.get("messages")) or "deine Frage"
    content = (
        "Ich habe folgende Hinweise zu '%s' zusammengetragen:\n\n" % question
        + ""
        + "Das ist die Zusammenfassung <>"
        + ""
        + "**Hinweis**"
        + "Dies ist ein höchstriskanter MOCK Agent. Sobald AGI Verfügbar, bitte austauschen"
    )
    return {"messages": [AIMessage(content=content)]}


def _build_riski_graph() -> CompiledStateGraph:
    """Create the LangGraph graph powering the mock agent."""

    graph = StateGraph(RiskiAgentState)
    graph.add_node(_RETRIEVAL_NODE, _retrieve_documents)
    graph.add_node(_GENERATE_NODE, _generate)
    graph.set_entry_point(_RETRIEVAL_NODE)
    graph.add_edge(_RETRIEVAL_NODE, _GENERATE_NODE)
    graph.add_edge(_GENERATE_NODE, END)
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


@lru_cache(maxsize=1)
def get_riski_agent() -> LangGraphAgent:
    """Return the cached riski agent"""

    compiled_graph = _build_riski_graph()
    return LangGraphAgent(
        name="RISKI mock agent",
        description="Placeholder riski agent till AGI is archieved",
        graph=compiled_graph,
    )
