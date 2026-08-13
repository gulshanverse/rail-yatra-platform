/**
 * Parse complete SSE events from arbitrary browser ReadableStream chunks.
 * The returned remainder must be retained until the next network read so
 * fragmented JSON payloads are never parsed prematurely.
 */
export interface SSEEvent {
  data: string;
  event?: string;
  id?: string;
}

interface SSEErrorPayload {
  type?: string;
  message?: string;
  error?: string;
}

const DEFAULT_CHAT_ERROR = 'RailYatra AI could not complete that request. Please try again.';

function normalizeErrorEvent(data: string): string {
  try {
    const payload = JSON.parse(data) as SSEErrorPayload;
    if (payload.type !== 'error') return data;

    const rawMessage = typeof payload.message === 'string'
      ? payload.message
      : typeof payload.error === 'string'
        ? payload.error
        : '';

    const message = rawMessage
      .replace(/^AI Service error \(\d+\):\s*/i, '')
      .replace(/\s+/g, ' ')
      .trim();

    const friendly = /quota|rate.?limit|resource.?exhaust|429/i.test(message)
      ? 'RailYatra AI is temporarily rate-limited. Please try again in a moment.'
      : /offline|unreachable|network|fetch failed|timeout|timed out/i.test(message)
        ? 'RailYatra AI is temporarily unavailable. Please try again in a moment.'
        : message || DEFAULT_CHAT_ERROR;

    return JSON.stringify({ type: 'done', reply: friendly });
  } catch {
    return data;
  }
}

export function parseSSEBuffer(buffer: string): [SSEEvent[], string] {
  const events: SSEEvent[] = [];
  while (true) {
    let separator = buffer.indexOf("\n\n");
    let separatorLength = 2;
    if (separator < 0) {
      separator = buffer.indexOf("\r\n\r\n");
      separatorLength = 4;
    }
    if (separator < 0) break;

    const rawEvent = buffer.slice(0, separator);
    buffer = buffer.slice(separator + separatorLength);
    const dataLines: string[] = [];
    let event: string | undefined;
    let id: string | undefined;

    for (const rawLine of rawEvent.replace(/\r\n/g, "\n").split("\n")) {
      if (!rawLine || rawLine.startsWith(":")) continue;
      const colon = rawLine.indexOf(":");
      const field = colon >= 0 ? rawLine.slice(0, colon) : rawLine;
      let value = colon >= 0 ? rawLine.slice(colon + 1) : "";
      if (value.startsWith(" ")) value = value.slice(1);
      if (field === "data") dataLines.push(value);
      else if (field === "event") event = value;
      else if (field === "id") id = value;
    }

    if (dataLines.length > 0) {
      events.push({ data: normalizeErrorEvent(dataLines.join("\n")), event, id });
    }
  }
  return [events, buffer];
}
