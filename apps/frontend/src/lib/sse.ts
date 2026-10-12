export interface SSEEvent {
  data: string;
  event?: string;
  id?: string;
  retry?: number;
}

export type AIEventType =
  | 'thinking' | 'intent' | 'tool_start' | 'tool_complete' | 'message' | 'token'
  | 'train_results' | 'journey_analysis' | 'pnr_status' | 'live_tracking'
  | 'recommendation' | 'warning' | 'error' | 'done' | 'status' | 'heartbeat';

export interface AIEvent<T = Record<string, unknown>> {
  type: AIEventType | string;
  event_id?: string;
  correlation_id?: string;
  timestamp?: string;
  value?: string;
  message?: string;
  code?: string;
  reply?: string;
  payload?: T;
  options?: unknown[];
  [key: string]: unknown;
}

/**
 * Parse complete SSE frames from arbitrary text chunks. The caller must retain
 * the returned remainder until the next read. No event is silently rewritten:
 * error and done frames remain visible to the event renderer.
 */
export function parseSSEBuffer(buffer: string): [SSEEvent[], string] {
  const events: SSEEvent[] = [];
  let separatorIndex = -1;
  let separatorLength = 0;

  while (true) {
    const lf = buffer.indexOf('\n\n');
    const crlf = buffer.indexOf('\r\n\r\n');
    const mixed = buffer.indexOf('\r\n\n');
    const candidates = [
      lf >= 0 ? [lf, 2] : null,
      crlf >= 0 ? [crlf, 4] : null,
      mixed >= 0 ? [mixed, 3] : null,
    ].filter((candidate): candidate is [number, number] => Boolean(candidate));
    if (candidates.length === 0) break;
    [separatorIndex, separatorLength] = candidates.sort((a, b) => a[0] - b[0])[0];

    const rawEvent = buffer.slice(0, separatorIndex);
    buffer = buffer.slice(separatorIndex + separatorLength);
    const dataLines: string[] = [];
    let event: string | undefined;
    let id: string | undefined;
    let retry: number | undefined;

    for (const rawLine of rawEvent.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n')) {
      if (!rawLine || rawLine.startsWith(':')) continue;
      const colon = rawLine.indexOf(':');
      const field = colon >= 0 ? rawLine.slice(0, colon) : rawLine;
      let value = colon >= 0 ? rawLine.slice(colon + 1) : '';
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

export function parseAIEvent(data: string): AIEvent | null {
  try {
    const parsed = JSON.parse(data) as AIEvent;
    return parsed && typeof parsed.type === 'string' ? parsed : null;
  } catch {
    return null;
  }
}

export function friendlyAIError(event: AIEvent | null): string {
  const raw = event?.message || event?.code || 'RailYatra AI could not complete that request. Please try again.';
  if (/quota|rate.?limit|resource.?exhaust|429/i.test(raw)) return 'RailYatra AI is temporarily rate-limited. Please try again in a moment.';
  if (/offline|unreachable|network|fetch failed|timeout|timed out|502|503|504/i.test(raw)) return 'Yatri could not reach the railway service. Please try again shortly.';
  return raw;
}
