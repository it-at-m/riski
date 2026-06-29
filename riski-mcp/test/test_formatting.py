"""Tests for spoken-answer formatting and error mapping (issue #07)."""

from __future__ import annotations

import pytest
from riski_mcp.agui_client import ERROR_RUN_ERROR, ERROR_TIMEOUT, ErrorInfo, RiskiAnswer
from riski_mcp.formatting import GENERIC_ERROR_MESSAGE, MAX_ANSWER_CHARS, format_answer


@pytest.mark.parametrize(
    ("error_type", "expected_fragment"),
    [
        ("no_tool_call", "etwas konkreter"),
        ("no_documents_found", "keine passenden Dokumente"),
        ("no_relevant_documents", "keines passte zur Frage"),
        ("content_policy_violation", "nicht beantworten"),
        ("server_error", GENERIC_ERROR_MESSAGE),
        (ERROR_TIMEOUT, "zu lange gedauert"),
        (ERROR_RUN_ERROR, GENERIC_ERROR_MESSAGE),
    ],
)
def test_error_type_maps_to_sentence(error_type: str, expected_fragment: str) -> None:
    out = format_answer(RiskiAnswer(error=ErrorInfo(error_type=error_type)))
    assert expected_fragment in out


def test_unknown_error_type_falls_back_to_generic() -> None:
    out = format_answer(RiskiAnswer(error=ErrorInfo(error_type="something_new")))
    assert out == GENERIC_ERROR_MESSAGE


def test_suggestions_appended() -> None:
    answer = RiskiAnswer(
        error=ErrorInfo(
            error_type="no_documents_found",
            suggestions=["Radverkehr Altstadt", "Fahrradwege Innenstadt", "ignored third"],
        )
    )
    out = format_answer(answer)
    assert "Radverkehr Altstadt" in out
    assert "Fahrradwege Innenstadt" in out
    # Only the first two suggestions are used.
    assert "ignored third" not in out


def test_answer_with_document_and_proposal_sources() -> None:
    answer = RiskiAnswer(
        answer="Es gibt Anträge zum Radverkehr.",
        documents=[{"name": "Beschlussvorlage Radwege", "risUrl": "https://x"}],
        proposals=[{"identifier": "p1", "name": "Antrag Radverkehr", "subject": "Ausbau"}],
    )
    out = format_answer(answer, max_sources=3)
    assert out.startswith("Es gibt Anträge zum Radverkehr.")
    assert "Quelle: Beschlussvorlage Radwege." in out
    assert "Quelle: Antrag Radverkehr." in out


def test_proposal_subject_used_when_no_name() -> None:
    answer = RiskiAnswer(answer="Antwort.", proposals=[{"identifier": "p1", "subject": "Ausbau der Radwege"}])
    out = format_answer(answer)
    assert "Quelle: Ausbau der Radwege." in out


def test_slim_snapshot_document_name_from_metadata() -> None:
    answer = RiskiAnswer(answer="Antwort.", documents=[{"id": "d1", "metadata": {"name": "Sitzungsprotokoll 2023"}}])
    out = format_answer(answer)
    assert "Quelle: Sitzungsprotokoll 2023." in out


def test_sources_capped_and_deduplicated() -> None:
    docs = [{"name": f"Doc {i}"} for i in range(5)] + [{"name": "Doc 0"}]
    out = format_answer(RiskiAnswer(answer="A.", documents=docs), max_sources=2)
    assert out.count("Quelle:") == 2


def test_max_sources_zero_omits_sources() -> None:
    out = format_answer(RiskiAnswer(answer="A.", documents=[{"name": "Doc"}]), max_sources=0)
    assert "Quelle" not in out


def test_markdown_stripped_from_answer() -> None:
    answer = RiskiAnswer(answer="**Wichtig:** siehe [Antrag](https://x) und `Code`.")
    out = format_answer(answer)
    assert "*" not in out
    assert "[" not in out and "](" not in out
    assert "`" not in out
    assert "Antrag" in out


def test_answer_length_capped() -> None:
    long_answer = "Wort " * 400  # ~2000 chars
    out = format_answer(RiskiAnswer(answer=long_answer), max_sources=0)
    assert len(out) <= MAX_ANSWER_CHARS + 1  # trailing ellipsis
    assert out.endswith("…")


def test_empty_answer_without_error_is_friendly() -> None:
    out = format_answer(RiskiAnswer(answer="   "))
    assert "keine Antwort" in out
    assert "{" not in out  # never speak JSON
