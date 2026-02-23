from app.agent.riski_agent import filter_tracked_proposals
from app.agent.state import TrackedDocument, TrackedProposal


def test_filter_tracked_proposals_keeps_linked_and_unlinked():
    docs = [
        TrackedDocument(id="doc-1", page_content="", metadata={}, is_checked=True, is_relevant=True),
        TrackedDocument(id="doc-2", page_content="", metadata={}, is_checked=True, is_relevant=False),
    ]

    proposals = [
        TrackedProposal(identifier="p1", name="Proposal 1", risUrl="1", source_document_ids=["doc-1"]),
        TrackedProposal(identifier="p2", name="Proposal 2", risUrl="2", source_document_ids=["doc-2"]),
        TrackedProposal(identifier="p3", name="Proposal 3", risUrl="3", source_document_ids=[]),
    ]

    filtered = filter_tracked_proposals(proposals, [docs[0]])

    assert [p.identifier for p in filtered] == ["p1", "p3"]


def test_filter_tracked_proposals_drops_all_without_relevant_docs():
    proposals = [
        TrackedProposal(identifier="p1", name="Proposal 1", risUrl="1", source_document_ids=["doc-1"]),
        TrackedProposal(identifier="p2", name="Proposal 2", risUrl="2", source_document_ids=[]),
    ]

    assert filter_tracked_proposals(proposals, []) == []
