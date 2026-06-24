"""AG-UI SSE client and answer aggregation.

Placeholder scaffold — the streaming client lands in issue #03 (with the typed
request/response models from issue #02).
"""

# TODO(#02): typed models (RunAgentInput, UserMessage, ConfigResponse, ...) and a
#            build_run_input(question) helper that mints fresh thread/run IDs.
# TODO(#03): BackendClient that POSTs to /api/ag-ui/riskiagent, consumes the
#            AG-UI Server-Sent Event stream, and aggregates it into a RiskiAnswer
#            (answer text, documents, proposals, mapped error_info).
