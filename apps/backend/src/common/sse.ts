export interface SSEEvent {
  data: string;
  event?: string;
  id?: string;
}

/**
 * Parse complete SSE events from an arbitrary network buffer.
 * The returned remainder must be retained until the next network read.
 */
export function parseSSEBuffer(buffer: string): [SSEEvent[], string] {
  const events: SSEEvent[] = [];

  while (true) {
    let separatorIndex = buffer.indexOf('\n\n');
    let separatorLength = 2;

    if (separatorIndex < 0) {
      separatorIndex = buffer.indexOf('\r\n\r\n');
      separatorLength = 4;
    }

    if (separatorIndex < 0) break;

    const rawEvent = buffer.slice(0, separatorIndex);
    buffer = buffer.slice(separatorIndex + separatorLength);

    const dataLines: string[] = [];
    let event: string | undefined;
    let id: string | undefined;

    for (const rawLine of rawEvent.replace(/\r\n/g, '\n').split('\n')) {
      if (!rawLine || rawLine.startsWith(':')) continue;

      const separator = rawLine.indexOf(':');
      const field = separator >= 0 ? rawLine.slice(0, separator) : rawLine;
      let value = separator >= 0 ? rawLine.slice(separator + 1) : '';
      if (value.startsWith(' ')) value = value.slice(1);

      if (field === 'data') dataLines.push(value);
      else if (field === 'event') event = value;
      else if (field === 'id') id = value;
    }

    if (dataLines.length > 0) {
      events.push({ data: dataLines.join('\n'), event, id });
    }
  }

  return [events, buffer];
}
