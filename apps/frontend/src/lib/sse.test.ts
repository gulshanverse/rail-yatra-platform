import { parseSSEBuffer } from './sse';

describe('SSE parser', () => {
  it('keeps incomplete data', () => {
    const [events, remainder] = parseSSEBuffer('data: {"type":"token","value":"Hello"}\n\ndata: partial');
    expect(events).toHaveLength(1);
    expect(remainder).toContain('partial');
  });
});
