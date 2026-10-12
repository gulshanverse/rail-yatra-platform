import { friendlyAIError, parseAIEvent, parseSSEBuffer } from './sse';

describe('chat stream parser', () => {
  it('preserves error events instead of converting them to done', () => {
    const [events] = parseSSEBuffer('event: ai\nid: c1:4\ndata: {"type":"error","message":"service unavailable"}\n\n');
    expect(events).toHaveLength(1);
    expect(events[0].id).toBe('c1:4');
    expect(JSON.parse(events[0].data).type).toBe('error');
  });

  it('keeps incomplete frames for the next network chunk', () => {
    const [events, remainder] = parseSSEBuffer('id: c1:1\ndata: {"type":"token","value":"hel');
    expect(events).toHaveLength(0);
    expect(remainder).toContain('hel');
    const [complete, finalRemainder] = parseSSEBuffer(`${remainder}lo"}\n\n`);
    expect(finalRemainder).toBe('');
    expect(parseAIEvent(complete[0].data)?.value).toBe('hello');
  });

  it('supports CRLF, comments, retry, and multi-line data', () => {
    const [events, remainder] = parseSSEBuffer(': heartbeat\r\nid: c1:2\r\nretry: 5000\r\nevent: message\r\ndata: {"type":"message",\r\ndata: "message":"hello"}\r\n\r\n');
    expect(remainder).toBe('');
    expect(events[0]).toMatchObject({ id: 'c1:2', event: 'message', retry: 5000, data: '{"type":"message",\n"message":"hello"}' });
  });

  it('does not treat an unframed upstream error body as a valid event', () => {
    const [events, remainder] = parseSSEBuffer('{"statusCode":502,"message":"service unavailable"}');
    expect(events).toHaveLength(0);
    expect(remainder).toContain('statusCode');
  });

  it('maps provider failures to user-facing language', () => {
    expect(friendlyAIError({ type: 'error', message: '429 resource exhausted' })).toContain('rate-limited');
    expect(friendlyAIError({ type: 'error', message: 'network timeout' })).toContain('reach');
  });
});
