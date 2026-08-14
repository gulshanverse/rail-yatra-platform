import { describe, expect, it } from 'vitest';
import { getTradeoffLeaders } from './JourneyComparison';
import type { JourneyWorkspaceOption } from './JourneyDecisionWorkspace';

const options: JourneyWorkspaceOption[] = [
  { id: 'a', trainNumber: 'A', duration: '8h 30m', fare: '₹1200', changes: 1, risk: 'medium' },
  { id: 'b', trainNumber: 'B', duration: '7h 15m', fare: '₹900', changes: 0, risk: 'low' },
  { id: 'c', trainNumber: 'C', duration: '9h', fare: '₹700', changes: 2, risk: 'high' },
];

describe('getTradeoffLeaders', () => {
  it('identifies the fastest, cheapest, fewest-change and lowest-risk options', () => {
    const leaders = getTradeoffLeaders(options);

    expect(leaders.find((item) => item.metric === 'duration')?.winnerId).toBe('b');
    expect(leaders.find((item) => item.metric === 'fare')?.winnerId).toBe('c');
    expect(leaders.find((item) => item.metric === 'changes')?.winnerId).toBe('b');
    expect(leaders.find((item) => item.metric === 'risk')?.winnerId).toBe('b');
  });

  it('does not invent a winner when a metric is missing', () => {
    const leaders = getTradeoffLeaders([
      { id: 'unknown', trainNumber: 'U', className: '3A' },
      { id: 'unknown-2', trainNumber: 'V', className: 'SL' },
    ]);

    expect(leaders.find((item) => item.metric === 'duration')?.winnerId).toBeUndefined();
    expect(leaders.find((item) => item.metric === 'fare')?.winnerId).toBeUndefined();
    expect(leaders.find((item) => item.metric === 'changes')?.winnerId).toBeUndefined();
    expect(leaders.find((item) => item.metric === 'risk')?.winnerId).toBeUndefined();
  });
});
