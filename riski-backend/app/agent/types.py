import json
from datetime import date
from typing import Literal, TypedDict

from core.model.data_models import PaperSubtypeEnum, PaperTypeEnum
from langchain_postgres import PGVectorStore
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker


class AgentContext(TypedDict):
    vectorstore: PGVectorStore
    db_sessionmaker: async_sessionmaker
    agent_capabilities: str
    top_k_docs: int
    db_query_timeout_seconds: int
    db_query_total_timeout_seconds: int
    vectorstore_timeout_seconds: int
    force_vectorstore_timeout: bool
    force_db_timeout: bool
    force_llm_timeout: bool


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
    "1. retrieve_documents: Use this tool to search for and retrieve documents relevant to content questions.\n"
    "2. get_faction_activity: Use this tool for exact counts and rankings of papers submitted by council factions.\n\n"
    "You MUST call the appropriate tool before answering. For faction activity statistics, use get_faction_activity "
    "instead of retrieve_documents and reproduce its exact SQL-derived counts without estimating."
)

CHECK_DOCUMENT_SYSTEM_PROMPT: str = "Du bist ein Relevanz-Prüfer. Bewerte ob ein Dokument relevant für eine Benutzeranfrage ist."

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
    "- Exakte SQL-basierte Statistiken zur Aktivität von Stadtratsfraktionen, gruppiert und gerankt nach Fraktion, "
    "filterbar nach Dokumenttyp, Untertyp und Zeitraum (einschließlich vorheriger Wahlperiode).\n"
    "- Antworten in der Sprache der jeweiligen Nutzerfrage (Deutsch, Englisch, Französisch u.\u202fa.).\n\n"
    "Wissensbasis:\n"
    "- Ausschließlich öffentliche Dokumente der Stadt München aus dem Zeitraum 2020 bis heute "
    "(aktuelle Legislaturperiode).\n"
    "- Statistische Metadaten können auch nach gespeicherten früheren Legislaturperioden gefiltert werden.\n\n"
    "Grenzen:\n"
    "- Inhaltsbasierte Freitext-Statistiken sind nicht möglich; Fraktionsstatistiken nach Typ, Untertyp und Datum sind möglich.\n"
    "- Keine Echtzeitdaten oder Informationen außerhalb des RIS.\n"
    "- Keine allgemeinen Anfragen ohne Bezug zur Münchner Stadtverwaltung, zum Stadtrat "
    "oder zu den Bezirksausschüssen (z.\u202fB. Code schreiben, Gedichte verfassen, Mathe-Aufgaben lösen)."
)


class DocumentReference(BaseModel):
    name: str = Field(description="The name or title of the document.")
    risUrl: str = Field(description="The URL of the document in the RIS system.")
    size: int = Field(
        default=0,
        description=(
            "File size in bytes. Copy the value from the document's metadata 'size' field. "
            "Use 0 if the metadata does not contain a 'size' entry. Do NOT invent a value."
        ),
    )
    identifier: str = Field(default="", description="An optional identifier for the document.")


class ProposalReference(BaseModel):
    identifier: str = Field(description="The reference identifier of the proposal.")
    name: str = Field(description="The name or title of the proposal.")
    subject: str = Field(default="", description="The subject or description of the proposal.")
    date: str | None = Field(default=None, description="The reference date of the proposal in ISO format.")
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


class FactionActivityArgs(BaseModel):
    paper_type: PaperTypeEnum | None = Field(default=None, description="Optional OParl paper type, e.g. 'Stadtratsantrag'.")
    paper_subtype: PaperSubtypeEnum | None = Field(default=None, description="Optional subtype, e.g. 'Antrag' or 'Anfrage'.")
    start_date: date | None = Field(default=None, description="Inclusive start date (YYYY-MM-DD).")
    end_date: date | None = Field(default=None, description="Inclusive end date (YYYY-MM-DD).")
    period: Literal["previous_legislative_term"] | None = Field(
        default=None, description="Use the most recently completed legislative term as the date range."
    )
    faction_name: str | None = Field(default=None, description="Optional exact faction name or short name, case-insensitive.")
    ranking: Literal["descending", "ascending"] = Field(default="descending", description="Order by paper count.")
    limit: int | None = Field(default=None, ge=1, le=100, description="Optional number of ranked factions to return.")
