"""AG-UI SSE client and answer aggregation.

Placeholder scaffold — the streaming client lands in issue #03 (with the typed
request/response models from issue #02).
"""

# Typed models (RunAgentInput, UserMessage, build_run_input) live in models.py and
# the non-streaming BackendClient in client.py — both landed in issue #02.
#
# TODO(#03): an async stream client that POSTs build_run_input(question) to
#            /api/ag-ui/riskiagent, consumes the AG-UI Server-Sent Event stream,
#            and aggregates it into a RiskiAnswer (answer text, documents,
#            proposals, mapped error_info).
