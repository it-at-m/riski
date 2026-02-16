"""State models for the RISKI Agent graph."""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Tracked document / proposal – single source of truth across the graph
# ---------------------------------------------------------------------------


class TrackedDocument(BaseModel):
    """A retrieved document enriched with relevance-check metadata.

    Lifecycle:
        1. ``retrieve_documents`` tool creates the entry (is_checked=False).
        2. ``check_document`` node sets ``is_checked=True`` and ``is_relevant``.
        3. ``call_model`` uses only documents where ``is_relevant is True``.
    """

    id: str = Field(default="", description="Unique document id (usually the DB primary key).")
    page_content: str = Field(default="", description="Text content of the document chunk.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata from the vector store.")

    # Relevance-check fields – populated by the guard
    is_checked: bool = Field(default=False, description="True once the relevance check has run.")
    is_relevant: bool = Field(default=True, description="True if the document passed the relevance check.")
    relevance_reason: str = Field(default="", description="Brief reason for the relevance decision.")

    def to_slim_dict(self) -> dict[str, Any]:
        """Return a lightweight dict without ``page_content`` for streaming to clients."""
        return self.model_dump(exclude={"page_content"})


class TrackedProposal(BaseModel):
    """A proposal (Stadtratsantrag) linked to retrieved documents."""

    identifier: str = Field(default="", description="Reference identifier of the proposal.")
    name: str = Field(default="", description="Name / title of the proposal.")
    risUrl: str = Field(default="", description="URL in the RIS system.")


# ---------------------------------------------------------------------------
# Input type for the per-document relevance check (used with Send)
# ---------------------------------------------------------------------------


class DocumentCheckInput(TypedDict):
    """Input for a single document relevance check (used with Send)."""

    doc_index: int
    doc: dict[str, Any]
    user_query: str


# ---------------------------------------------------------------------------
# Reducer: merge relevance-check results back into the tracked documents list
# ---------------------------------------------------------------------------


class RelevanceUpdate(BaseModel):
    """Carries a single relevance-check result back to the reducer."""

    doc_id: str
    is_relevant: bool
    reason: str


def _merge_tracked_documents(
    current: list[TrackedDocument],
    update: list[TrackedDocument] | list[RelevanceUpdate],
) -> list[TrackedDocument]:
    """Custom reducer for ``tracked_documents``.

    Accepts two kinds of updates:
    * A fresh ``list[TrackedDocument]`` (from the tool node) – replaces the list.
    * A ``list[RelevanceUpdate]`` (from check_document) – patches existing entries.
    """
    if not update:
        return current

    first = update[0]

    # Full replacement (tool wrote new documents)
    if isinstance(first, TrackedDocument):
        return list(update)  # type: ignore[arg-type]

    # Incremental patch (guard wrote relevance updates)
    if isinstance(first, RelevanceUpdate):
        by_id: dict[str, RelevanceUpdate] = {u.doc_id: u for u in update}  # type: ignore[union-attr]
        patched: list[TrackedDocument] = []
        for doc in current:
            if doc.id in by_id:
                upd = by_id[doc.id]
                doc = doc.model_copy(
                    update={
                        "is_checked": True,
                        "is_relevant": upd.is_relevant,
                        "relevance_reason": upd.reason,
                    }
                )
            patched.append(doc)
        return patched

    return current


# ---------------------------------------------------------------------------
# Main agent state
# ---------------------------------------------------------------------------


class RiskiAgentState(BaseModel):
    """Pydantic state for the agent graph.

    Uses a single ``tracked_documents`` list that carries documents through
    the entire retrieval → guard → generation pipeline.  The ``is_checked``
    and ``is_relevant`` flags on each entry replace the old three-list
    pattern (``documents`` / ``check_results`` / ``filtered_documents``).
    """

    # -- Chat History --
    messages: list[AnyMessage] = Field(default_factory=list)

    # -- Query inputs --
    user_query: str = Field(default="", description="The latest user query.")
    initial_question: str = Field(default="", description="The original question that started the turn.")

    # -- Unified document + proposal tracking --
    tracked_documents: Annotated[list[TrackedDocument], _merge_tracked_documents] = Field(default_factory=list)
    tracked_proposals: list[TrackedProposal] = Field(default_factory=list)

    # Pydantic Config
    model_config = {"arbitrary_types_allowed": True}

    # -- Convenience helpers (used throughout the graph) --

    def __getitem__(self, key: str):
        return getattr(self, key)

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    @property
    def has_documents(self) -> bool:
        """True if any documents have been retrieved (regardless of relevance)."""
        return len(self.tracked_documents) > 0

    @property
    def relevant_documents(self) -> list[TrackedDocument]:
        """Return only documents that passed the relevance check."""
        return [d for d in self.tracked_documents if d.is_relevant]

    @property
    def all_checked(self) -> bool:
        """True once every tracked document has been relevance-checked."""
        return bool(self.tracked_documents) and all(d.is_checked for d in self.tracked_documents)


# ---------------------------------------------------------------------------
# State update type for graph nodes
# ---------------------------------------------------------------------------


class RiskiAgentStateUpdate(TypedDict, total=False):
    """Partial state update returned by graph nodes."""

    messages: list[AnyMessage]
    user_query: str
    initial_question: str
    tracked_documents: list[TrackedDocument]
    tracked_proposals: list[TrackedProposal]
