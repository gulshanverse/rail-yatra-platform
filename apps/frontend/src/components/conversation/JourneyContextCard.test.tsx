import { describe, expect, it } from 'vitest';

describe('JourneyContext', () => {
  it('keeps missing journey values explicit', () => {
    const context = { origin: null, destination: 'Patna', date: null };
    expect(context.origin ?? 'Not specified').toBe('Not specified');
    expect(context.date ?? 'Not specified').toBe('Not specified');
    expect(context.destination).toBe('Patna');
  });

  it('keeps context scoped as plain data', () => {
    const first = { conversationId: 'a', destination: 'Patna' };
    const second = { conversationId: 'b', destination: 'Delhi' };
    expect(first.conversationId).not.toBe(second.conversationId);
    expect(first.destination).not.toBe(second.destination);
  });
});
