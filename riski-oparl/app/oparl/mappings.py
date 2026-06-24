"""Mapping of RISKI enum/string values to OParl-recommended values.

The data model stores German RIS terminology. OParl defines recommended (not
mandatory) vocabularies for some fields. We map where a clear OParl equivalent
exists and otherwise pass the original value through unchanged.
"""

# Meeting.meetingState -> OParl recommended values (scheduled | invited | conducted)
MEETING_STATE = {
    "geplant": "scheduled",
    "eingeladen": "invited",
    "durchgeführt": "conducted",
    "durchgefuehrt": "conducted",
    "abgehalten": "conducted",
}


def map_meeting_state(value: str | None) -> str | None:
    if not value:
        return None
    return MEETING_STATE.get(value.strip().casefold(), value)
