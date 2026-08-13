"""Utilities for robust Server-Sent Events parsing and formatting."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SSEEvent:
    """A parsed SSE event."""

    data: str
    event: str | None = None
    event_id: str | None = None


def format_sse(data: Any, *, event: str | None = None, event_id: str | None = None) -> str:
    """Format one complete SSE event, always terminated by a blank line."""
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    lines = []
    if event:
        lines.append(f"event: {event}")
    if event_id:
        lines.append(f"id: {event_id}")
    for line in payload.splitlines() or [""]:
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


def parse_sse_buffer(buffer: str) -> tuple[list[SSEEvent], str]:
    """Parse complete SSE events and return (events, incomplete_buffer).

    Network reads are arbitrary byte chunks, so callers must retain the trailing
    incomplete event rather than trying to JSON-decode each network chunk.
    """
    events: list[SSEEvent] = []
    while True:
        separator = buffer.find("\n\n")
        separator_len = 2
        if separator < 0:
            separator = buffer.find("\r\n\r\n")
            separator_len = 4
        if separator < 0:
            break

        raw_event = buffer[:separator]
        buffer = buffer[separator + separator_len :]
        data_lines: list[str] = []
        event_name: str | None = None
        event_id: str | None = None

        for raw_line in raw_event.replace("\r\n", "\n").split("\n"):
            if not raw_line or raw_line.startswith(":"):
                continue
            field, _, value = raw_line.partition(":")
            if value.startswith(" "):
                value = value[1:]
            if field == "data":
                data_lines.append(value)
            elif field == "event":
                event_name = value
            elif field == "id":
                event_id = value

        if data_lines:
            events.append(SSEEvent("\n".join(data_lines), event_name, event_id))

    return events, buffer
