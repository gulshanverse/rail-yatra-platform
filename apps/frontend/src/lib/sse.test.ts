import { parseSSEBuffer } from './sse';

describe('chat stream parser', () => {
  it('handles an error event', () => {
    const [events] = parseSSEBuffer('data: {"type":"error","message":"service unavailable"}\n\n');
    expect(JSON.parse(events[0].data).type).toBe('done');
  });

  it('handles a plain error body', () => {
    const [events, remainder] = parseSSEBuffer('{"statusCode":502,"message":"service unavailable"}');
    expect(remainder).toBe('');
    expect(JSON.parse(events[0].data).type).toBe('done');
  });
});
