import json

from langchain_postgres import PGVectorStore
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.util.typing import TypedDict


class AgentContext(TypedDict):
    vectorstore: PGVectorStore
    db_sessionmaker: async_sessionmaker
    agent_capabilities: str


NO_RESULTS_RESPONSE: str = json.dumps(
    {
        "response": "Es wurden leider keine relevanten Dokumente zu Ihrer Anfrage gefunden.",
        "documents": [],
        "proposals": [],
    }
)

SYSTEM_PROMPT: str = (
    "You are the RISKI Agent, an AI assistant designed to help users research and "
    "analyze documents and proposals from the City of Munich's Council Information System. "
    "Your goal is to provide accurate, concise, and relevant information based on the "
    "user's queries and the documents available to you.\n\n"
    "Tools:\n"
    "You have access to the following tools to assist you in your tasks:\n"
    "1. retrieve_documents: Use this tool to search for and retrieve documents relevant to the user's query.\n\n"
    "You MUST always call the retrieve_documents tool before answering a question."
)

CHECK_DOCUMENT_PROMPT_TEMPLATE: str = (
    "Prüfe, ob das folgende Dokument für die Benutzeranfrage relevant ist.\n\n"
    "Benutzeranfrage: {user_query}\n\n"
    "Dokumentname: {doc_name}\n"
    "Dokumentinhalt (Auszug):\n{snippet}\n\n"
    "Ist dieses Dokument relevant für die Anfrage?"
)

AGENT_CAPABILITIES_PROMPT: str = (
    "Der RISKI Agent hilft bei der Recherche und Analyse von Dokumenten und Beschlussvorlagen "
    "aus dem Rats-Informations-System (RIS) der Stadt München.\n\n"
    "Fähigkeiten:\n"
    "- Suche nach relevanten Dokumenten und Beschlussvorlagen der Stadtverwaltung, des Stadtrats "
    "und der Bezirksausschüsse über eine semantische Ähnlichkeitssuche.\n"
    "- Beantwortung von inhaltlichen Fragen zu Stadtratsanträgen, Beschlüssen, Sitzungsprotokollen "
    "und anderen öffentlichen Dokumenten aus dem RIS.\n"
    "- Antworten in der Sprache der jeweiligen Nutzerfrage (Deutsch, Englisch, Französisch u.\u202fa.).\n\n"
    "Wissensbasis:\n"
    "- Ausschließlich öffentliche Dokumente der Stadt München aus dem Zeitraum 2020 bis heute "
    "(aktuelle Legislaturperiode).\n"
    "- Keine Dokumente aus früheren Legislaturperioden oder externen Quellen.\n\n"
    "Grenzen:\n"
    "- Keine statistischen Auswertungen möglich (z.\u202fB. 'Wie viele Dokumente gibt es zum Thema X?').\n"
    "- Keine Echtzeitdaten oder Informationen außerhalb des RIS.\n"
    "- Keine allgemeinen Anfragen ohne Bezug zur Münchner Stadtverwaltung, zum Stadtrat "
    "oder zu den Bezirksausschüssen (z.\u202fB. Code schreiben, Gedichte verfassen, Mathe-Aufgaben lösen)."
)


class DocumentReference(BaseModel):
    name: str = Field(description="The name or title of the document.")
    risUrl: str = Field(description="The URL of the document in the RIS system.")
    size: int = Field(default=0, description="The file size in bytes.")
    identifier: str = Field(default="", description="An optional identifier for the document.")


class ProposalReference(BaseModel):
    identifier: str = Field(description="The reference identifier of the proposal.")
    name: str = Field(description="The name or title of the proposal.")
    risUrl: str = Field(description="The URL of the proposal in the RIS system.")


class StructuredAgentResponse(BaseModel):
    response: str = Field(description="The final answer to the user's question.")
    documents: list[DocumentReference] = Field(description="List of documents supporting the answer.")
    proposals: list[ProposalReference] = Field(description="List of proposals related to the supporting documents.")


class DocumentRelevanceVerdict(BaseModel):
    """LLM verdict on whether a single document is relevant to the user's query."""

    relevant: bool = Field(description="True if the document is relevant to the user's query.")
    reason: str = Field(description="Brief reason for the relevance decision (1-2 sentences, in German).")


class SuggestionsResponse(BaseModel):
    """LLM-generated alternative search query suggestions."""

    suggestions: list[str] = Field(
        description=(
            "2 to 3 alternative, more specific search queries or reformulations that are "
            "likely to find relevant documents in the Munich RIS. Each entry is a short, "
            "self-contained search phrase in the same language as the original query."
        ),
        min_length=0,
        max_length=3,
    )
