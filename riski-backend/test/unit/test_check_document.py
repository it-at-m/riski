"""Unit tests for the ``check_document`` node inside ``build_guard_nodes``.

The node is a closure over ``chat_model``, ``check_document_prompt_template``,
``snippet_size``, and ``force_llm_timeout``.  We extract it by calling
``build_guard_nodes`` with a mocked ``ChatOpenAI`` and inspect only the
``check_document`` function that is returned.

All LLM calls are mocked via ``AsyncMock`` so no network is required.
"""

from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.riski_agent import (
    _assume_relevant,
    _coerce_verdict,
    build_guard_nodes,
)
from app.agent.state import DocumentCheckInput, RelevanceUpdate
from app.agent.types import CHECK_DOCUMENT_PROMPT_TEMPLATE, DocumentRelevanceVerdict
from openai import APITimeoutError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_doc(
    doc_id: str = "doc-1",
    name: str = "Test Document",
    page_content: str = "Some content about Munich city council.",
) -> dict:
    return {
        "id": doc_id,
        "page_content": page_content,
        "metadata": {"name": name},
        "is_checked": False,
        "is_relevant": True,
        "relevance_reason": "",
    }


def _make_state(doc: dict | None = None, user_query: str = "Wer hat den Antrag gestellt?") -> DocumentCheckInput:
    return DocumentCheckInput(
        doc_index=0,
        doc=doc if doc is not None else _make_doc(),
        user_query=user_query,
    )


def _make_check_document(
    verdict: DocumentRelevanceVerdict | None = None,
    llm_side_effect=None,
    force_llm_timeout: bool = False,
    prompt_template: str = CHECK_DOCUMENT_PROMPT_TEMPLATE,
    snippet_size: int = 10_000,
):
    """Build a ``check_document`` node backed by a mock LLM.

    If *verdict* is given the LLM mock returns it.  If *llm_side_effect* is
    given it is raised instead.
    """
    mock_llm = MagicMock()
    structured_mock = AsyncMock()

    if llm_side_effect is not None:
        structured_mock.ainvoke = AsyncMock(side_effect=llm_side_effect)
    else:
        structured_mock.ainvoke = AsyncMock(return_value=verdict or DocumentRelevanceVerdict(relevant=True, reason="Relevant."))

    mock_llm.with_structured_output = MagicMock(return_value=structured_mock)

    _, _, check_document, _ = build_guard_nodes(
        chat_model=mock_llm,
        check_document_prompt_template=prompt_template,
        snippet_size=snippet_size,
        force_llm_timeout=force_llm_timeout,
    )
    return check_document, mock_llm


# ---------------------------------------------------------------------------
# Phase 1 – state unpacking
# ---------------------------------------------------------------------------


class TestPhase1StateUnpacking:
    async def test_missing_doc_key_returns_assume_relevant(self):
        """State without 'doc' key must not raise – returns assume-relevant fallback."""
        check_document, _ = _make_check_document()
        bad_state = {"user_query": "some query"}  # missing 'doc'

        result = await check_document(bad_state)

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert len(updates) == 1
        assert updates[0].is_relevant is True
        assert "Unerwartetes State-Format" in updates[0].reason

    async def test_missing_user_query_key_returns_assume_relevant(self):
        """State without 'user_query' key must not raise."""
        check_document, _ = _make_check_document()
        bad_state = {"doc": _make_doc()}  # missing 'user_query'

        result = await check_document(bad_state)

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert len(updates) == 1
        assert updates[0].is_relevant is True

    async def test_state_unpack_error_returns_empty_doc_id(self):
        """When state unpacking fails the returned doc_id must be an empty string."""
        check_document, _ = _make_check_document()

        result = await check_document("not a dict at all")

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].doc_id == ""

    async def test_completely_wrong_state_type_returns_assume_relevant(self):
        """A plain string instead of a dict must not raise."""
        check_document, _ = _make_check_document()

        result = await check_document("not a dict at all")

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert len(updates) == 1
        assert updates[0].is_relevant is True

    async def test_doc_is_not_a_dict_falls_back_gracefully(self):
        """If 'doc' is not a dict, extraction falls back to empty strings."""
        check_document, _ = _make_check_document()
        state = DocumentCheckInput(doc_index=0, doc="not-a-dict", user_query="query")  # type: ignore[typeddict-item]

        result = await check_document(state)

        # doc_id will be "" – the RelevanceUpdate should still come back
        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert len(updates) == 1
        assert updates[0].is_relevant is True


# ---------------------------------------------------------------------------
# Phase 2 – prompt compilation
# ---------------------------------------------------------------------------


class TestPhase2PromptCompilation:
    async def test_braces_in_snippet_do_not_raise(self):
        """Braces in page_content are safe – they end up as literal characters in the
        substituted value and do not interfere with str.format() key lookup."""
        doc = _make_doc(page_content='Inhalt mit {unbekannte_variable} und {"json": true}')
        check_document, _ = _make_check_document()

        result = await check_document(_make_state(doc=doc))

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert len(updates) == 1
        # The LLM was still invoked – result comes from the mock (relevant=True)
        assert updates[0].is_relevant is True

    async def test_doc_name_falls_back_to_metadata_title(self):
        """When metadata has no 'name' key, 'title' is used as the document name."""
        doc = _make_doc()
        doc["metadata"] = {"title": "Fallback Title"}  # only 'title', no 'name'
        check_document, mock_llm = _make_check_document()

        await check_document(_make_state(doc=doc))

        call_args = mock_llm.with_structured_output.return_value.ainvoke.call_args
        human_message_content: str = call_args.args[0][1].content
        assert "Fallback Title" in human_message_content

    async def test_textpromptclient_compile_returning_non_string_assumes_relevant(self):
        """If TextPromptClient.compile() returns a non-string, the node falls back to assume-relevant."""
        mock_template = MagicMock()
        mock_template.compile.return_value = 42  # not a str

        with patch("app.agent.riski_agent.TextPromptClient", type(mock_template)):
            check_document, _ = _make_check_document(prompt_template=mock_template)
            result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True
        assert "Prompt-Kompilierung" in updates[0].reason

    async def test_format_exception_returns_assume_relevant(self):
        """A deliberately broken template that raises on .format() returns a safe fallback."""
        # Template with a missing positional argument causes KeyError
        broken_template = "Query: {user_query} Doc: {doc_name} {this_key_does_not_exist}"
        check_document, _ = _make_check_document(prompt_template=broken_template)

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert len(updates) == 1
        assert updates[0].is_relevant is True
        assert "Prompt-Kompilierung" in updates[0].reason

    async def test_langfuse_textpromptclient_is_called_correctly(self):
        """When the template is a TextPromptClient its .compile() method is used."""
        mock_template = MagicMock()
        mock_template.compile.return_value = "Compiled prompt text"

        # Make isinstance(..., TextPromptClient) return True for our mock
        with patch("app.agent.riski_agent.TextPromptClient", type(mock_template)):
            check_document, _ = _make_check_document(prompt_template=mock_template)
            result = await check_document(_make_state())

        mock_template.compile.assert_called_once()
        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert len(updates) == 1

    async def test_textpromptclient_compile_raises_returns_assume_relevant(self):
        """If TextPromptClient.compile() raises, the node returns a safe fallback."""
        mock_template = MagicMock()
        mock_template.compile.side_effect = RuntimeError("Langfuse connection lost")

        with patch("app.agent.riski_agent.TextPromptClient", type(mock_template)):
            check_document, _ = _make_check_document(prompt_template=mock_template)
            result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True
        assert "Prompt-Kompilierung" in updates[0].reason

    async def test_snippet_is_truncated_to_snippet_size(self):
        """page_content longer than snippet_size is truncated before prompt compilation."""
        long_content = "x" * 20_000
        doc = _make_doc(page_content=long_content)
        check_document, mock_llm = _make_check_document(snippet_size=100)

        await check_document(_make_state(doc=doc))

        # Verify the prompt passed to the LLM contains at most snippet_size chars of content
        call_args = mock_llm.with_structured_output.return_value.ainvoke.call_args
        human_message_content: str = call_args[0][0][1].content  # messages[1] = HumanMessage
        assert "x" * 101 not in human_message_content
        assert "x" * 100 in human_message_content


# ---------------------------------------------------------------------------
# Phase 3 – LLM relevance check
# ---------------------------------------------------------------------------


class TestPhase3LLMRelevanceCheck:
    async def test_relevant_verdict_is_returned(self):
        verdict = DocumentRelevanceVerdict(relevant=True, reason="Sehr relevant.")
        check_document, _ = _make_check_document(verdict=verdict)

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True
        assert updates[0].reason == "Sehr relevant."

    async def test_not_relevant_verdict_is_returned(self):
        verdict = DocumentRelevanceVerdict(relevant=False, reason="Nicht relevant.")
        check_document, _ = _make_check_document(verdict=verdict)

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is False
        assert updates[0].reason == "Nicht relevant."

    async def test_dict_verdict_is_coerced(self):
        """LLM returning a plain dict is coerced to DocumentRelevanceVerdict."""
        check_document, mock_llm = _make_check_document()
        mock_llm.with_structured_output.return_value.ainvoke = AsyncMock(return_value={"relevant": False, "reason": "Dict-Antwort."})

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is False
        assert updates[0].reason == "Dict-Antwort."

    async def test_unknown_verdict_type_assumes_relevant(self):
        """LLM returning an unexpected type is treated as relevant."""
        check_document, mock_llm = _make_check_document()
        mock_llm.with_structured_output.return_value.ainvoke = AsyncMock(return_value=42)

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True

    async def test_api_timeout_error_assumes_relevant(self):
        """APITimeoutError during the LLM call returns assume-relevant."""
        check_document, _ = _make_check_document(llm_side_effect=APITimeoutError.__new__(APITimeoutError))

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True
        assert "Zeitüberschreitung" in updates[0].reason

    async def test_generic_exception_assumes_relevant(self):
        """Any unexpected exception during LLM invocation returns assume-relevant."""
        check_document, _ = _make_check_document(llm_side_effect=RuntimeError("Something exploded"))

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True
        assert "fehlgeschlagen" in updates[0].reason

    async def test_force_llm_timeout_flag_triggers_timeout_path(self):
        """force_llm_timeout=True must exercise the APITimeoutError fallback path."""
        check_document, _ = _make_check_document(force_llm_timeout=True)

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True
        assert "Zeitüberschreitung" in updates[0].reason

    async def test_connection_error_assumes_relevant(self):
        """A network-level ConnectionError is also caught and returns assume-relevant."""
        check_document, _ = _make_check_document(llm_side_effect=ConnectionError("Network unreachable"))

        result = await check_document(_make_state())

        updates: list[RelevanceUpdate] = result["tracked_documents"]
        assert updates[0].is_relevant is True


# ---------------------------------------------------------------------------
# Phase 4 – result shape
# ---------------------------------------------------------------------------


class TestPhase4ResultShape:
    async def test_result_always_contains_tracked_documents_key(self):
        check_document, _ = _make_check_document()
        result = await check_document(_make_state())
        assert "tracked_documents" in result

    async def test_result_contains_exactly_one_update(self):
        check_document, _ = _make_check_document()
        result = await check_document(_make_state())
        assert len(result["tracked_documents"]) == 1

    async def test_doc_id_is_propagated_to_update(self):
        doc = _make_doc(doc_id="my-unique-id")
        check_document, _ = _make_check_document()
        result = await check_document(_make_state(doc=doc))
        assert result["tracked_documents"][0].doc_id == "my-unique-id"

    async def test_updates_are_relevance_update_instances(self):
        check_document, _ = _make_check_document()
        result = await check_document(_make_state())
        assert all(isinstance(u, RelevanceUpdate) for u in result["tracked_documents"])


# ---------------------------------------------------------------------------
# Unit tests for extracted helper functions
# ---------------------------------------------------------------------------


class TestAssumeRelevant:
    def test_returns_dict_with_tracked_documents(self):
        result = _assume_relevant("doc-42", "Some reason")
        assert "tracked_documents" in result
        assert len(result["tracked_documents"]) == 1

    def test_sets_is_relevant_true(self):
        update = _assume_relevant("doc-42", "reason")["tracked_documents"][0]
        assert update.is_relevant is True

    def test_propagates_doc_id_and_reason(self):
        update = _assume_relevant("doc-42", "My reason")["tracked_documents"][0]
        assert update.doc_id == "doc-42"
        assert update.reason == "My reason"

    def test_empty_doc_id_is_allowed(self):
        update = _assume_relevant("", "reason")["tracked_documents"][0]
        assert update.doc_id == ""


class TestCoerceVerdict:
    def test_passthrough_for_correct_type(self):
        v = DocumentRelevanceVerdict(relevant=True, reason="ok")
        assert _coerce_verdict(v, "doc", "id") is v

    def test_dict_with_relevant_false(self):
        result = _coerce_verdict({"relevant": False, "reason": "nope"}, "doc", "id")
        assert result.relevant is False
        assert result.reason == "nope"

    def test_dict_missing_keys_defaults_to_relevant_true(self):
        result = _coerce_verdict({}, "doc", "id")
        assert result.relevant is True

    def test_unexpected_type_returns_relevant_true(self):
        result = _coerce_verdict(object(), "doc", "id")
        assert result.relevant is True

    def test_none_returns_relevant_true(self):
        result = _coerce_verdict(None, "doc", "id")
        assert result.relevant is True


# ---------------------------------------------------------------------------
# Regression tests – real-world inputs that previously caused failures
# ---------------------------------------------------------------------------

# Exact payload that triggered the original tracing error
# "check_document: ERROR / ERROR / <object object at 0x...>" before the fix.
_REGRESSION_STATE_WASSERRECHT: DocumentCheckInput = DocumentCheckInput(
    doc_index=2,
    doc={
        "id": "76419393-a954-4683-9fdc-8459b33bb576",
        "page_content": (
            "Telefon: 0 233-47574\nTelefax: 0 233-47580\n"
            "Referat für Klima- und Umweltschutz\nUmweltschutz\nWasserrecht\nRKU-IV-13\n\n"
            "Personalbedarf im Sachgebiet Wasserrecht sowie\n"
            "technische Sachverständigen-Dienstleistungen\n"
            "Produkt 45561300 Umweltschutz\nBeschluss über die Finanzierung ab 2023\n\n"
            "Sitzungsvorlage Nr. 20-26 / V 07523\n\n"
            "Beschluss der Vollversammlung des Stadtrates\nvom 30.11.2022\nÖffentliche Sitzung\n\n"
            "I. Vortrag und Antrag der Referentin\n"
            "wie in der Sitzung des Ausschusses für Klima- und Umweltschutz am 15.11.2022. "
            "Der Ausschuss hat die Annahme des Antrages empfohlen.\n\n"
            "II. Beschluss\nnach Antrag.\n\n"
            "Der Stadtrat der Landeshauptstadt München\n\n"
            "Die / Der Vorsitzende\nDie Referentin\n\n"
            "Ober-/Bürgermeister/-in\nebenso. Stadträtin / ea. Stadtrat\n\n"
            "Christine Kugler\nBerufsmäßige Stadträtin\n\nSeite 2 von 2\n\n"
            "III. Abdruck von I. mit II. (Beglaubigungen)\n"
            "über das Direktorium HA II/V - Stadtratsprotokolle\n"
            "an das Revisionsamt\nan das Direktorium – Dokumentationsstelle\n"
            "an das Referat für Klima- und Umweltschutz, Beschlusswesen (RKU-GL3)\n\n"
            "IV. Wv Referat für Klima- und Umweltschutz, Beschlusswesen (RKU-GL3)\n"
            "zur weiteren Veranlassung (Archivierung, Hinweis-Mail)."
        ),
        "metadata": {
            "id": "https://risi.muenchen.de/risi/dokument/v/7382233",
            "name": "Personalbedarf_Wasserrecht_Deckblatt_VV",
            "size": 55992,
        },
        "is_checked": False,
        "is_relevant": True,
        "relevance_reason": "",
    },
    user_query="Stadtentwässerung Isar Renaturierung Beschlussvorlage aus den Jahr vor 2015",
)


class TestRegressionRealWorldInputs:
    async def test_wasserrecht_doc_does_not_raise(self):
        """Regression: the Wasserrecht payload must reach the LLM without raising."""
        check_document, mock_llm = _make_check_document(verdict=DocumentRelevanceVerdict(relevant=False, reason="Nicht relevant."))

        result = await check_document(_REGRESSION_STATE_WASSERRECHT)

        assert "tracked_documents" in result
        assert mock_llm.with_structured_output.return_value.ainvoke.called, "LLM must be invoked"

    async def test_wasserrecht_doc_id_is_propagated(self):
        """Regression: doc_id from the Wasserrecht payload is preserved in the update."""
        check_document, _ = _make_check_document()

        result = await check_document(_REGRESSION_STATE_WASSERRECHT)

        assert result["tracked_documents"][0].doc_id == "76419393-a954-4683-9fdc-8459b33bb576"

    async def test_wasserrecht_doc_not_relevant_verdict_is_returned(self):
        """Regression: an 'irrelevant' LLM verdict is passed through correctly."""
        verdict = DocumentRelevanceVerdict(relevant=False, reason="Thema passt nicht zur Anfrage.")
        check_document, _ = _make_check_document(verdict=verdict)

        result = await check_document(_REGRESSION_STATE_WASSERRECHT)

        update = result["tracked_documents"][0]
        assert update.is_relevant is False
        assert update.reason == "Thema passt nicht zur Anfrage."
