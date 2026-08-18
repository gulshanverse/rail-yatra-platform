export interface SSEEvent {
  data: string;
  event?: string;
  id?: string;
  retry?: number;
}

/**
 * Parse complete SSE events from an arbitrary network buffer.
 * The returned remainder must be retained until the next network read.
 */
export function parseSSEBuffer(buffer: string): [SSEEvent[], string] {
  const events: SSEEvent[] = [];

  while (true) {
    const separators: Array<[string, number]> = [
      ['\n\n', 2],
      ['\r\n\r\n', 4],
      ['\r\n\n', 3],
    ];
    const candidates: Array<[number, number]> = separators
      .map(([separator, length]) => [buffer.indexOf(separator), length] as [number, number])
      .filter(([index]) => index >= 0)
      .sort(([left], [right]) => left - right);

    if (candidates.length === 0) break;
    const [separatorIndex, separatorLength] = candidates[0];
    const rawEvent = buffer.slice(0, separatorIndex);
    buffer = buffer.slice(separatorIndex + separatorLength);

    const dataLines: string[] = [];
    let event: string | undefined;
    let id: string | undefined;
    let retry: number | undefined;

    for (const rawLine of rawEvent.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n')) {
      if (!rawLine || rawLine.startsWith(':')) continue;

      const separator = rawLine.indexOf(':');
      const field = separator >= 0 ? rawLine.slice(0, separator) : rawLine;
      let value = separator >= 0 ? rawLine.slice(separator + 1) : '';
      if (value.startsWith(' ')) value = value.slice(1);

      if (field === 'data') dataLines.push(value);
      else if (field === 'event') event = value;
      else if (field === 'id' && !value.includes('\u0000')) id = value;
      else if (field === 'retry' && /^\d+$/.test(value)) retry = Number(value);
    }

    if (dataLines.length > 0) events.push({ data: dataLines.join('\n'), event, id, retry });
  }

  return [events, buffer];
}

export function formatSSEEvent(event: SSEEvent): string {
  const lines: string[] = [];
  if (event.event) lines.push(`event: ${event.event}`);
  if (event.id) lines.push(`id: ${event.id}`);
  if (typeof event.retry === 'number') lines.push(`retry: ${event.retry}`);
  for (const line of event.data.split('\n')) lines.push(`data: ${line}`);
  return `${lines.join('\n')}\n\n`;
}
