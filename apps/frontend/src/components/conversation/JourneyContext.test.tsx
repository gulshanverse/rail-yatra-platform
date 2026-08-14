import { describe, expect, it } from 'vitest';
import { JourneyContext } from './JourneyContext';

void JourneyContext;

describe('JourneyContext', () => {
  it('keeps missing journey fields explicit instead of inventing values', () => {
    const context = { origin: 'Bilaspur', destination: null, date: null, passengers: null, className: null };
    expect(context.origin).toBe('Bilaspur');
    expect(context.destination).toBeNull();
    expect(context.date).toBeNull();
    expect(context.passengers).toBeNull();
    expect(context.className).toBeNull();
  });
});
