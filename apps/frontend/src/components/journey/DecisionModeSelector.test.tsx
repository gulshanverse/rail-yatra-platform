import { describe, expect, it } from 'vitest';
import { rankOptions, type DecisionMode } from './DecisionModeSelector';
import type { JourneyWorkspaceOption } from './JourneyDecisionWorkspace';

const options: JourneyWorkspaceOption[] = [
  { id: 'slow', duration: '10h 30m', fare: '₹900', changes: 1, risk: 'medium', className: 'SL' },
  { id: 'fast', duration: '7h 15m', fare: '₹1400', changes: 0, risk: 'low', className: '3A' },
  { id: 'cheap', duration: '9h 20m', fare: '₹700', changes: 0, risk: 'low', className: 'SL' },
];

describe('rankOptions', () => {
  const cases: Array<[DecisionMode, string]> = [
    ['fastest', 'fast'],
    ['cheapest', 'cheap'],
    ['lowest-risk', 'fast'],
    ['overall', 'cheap'],
  ];

  it.each(cases)('prioritizes the expected option for %s', (mode, expected) => {
    expect(rankOptions(options, mode)[0]?.id).toBe(expected);
  });

  it('does not rank cheapest when fares are missing', () => {
    expect(rankOptions([{ id: 'unknown', duration: '8h' }], 'cheapest')).toHaveLength(0);
  });

  it('does not rank fastest when durations are missing', () => {
    expect(rankOptions([{ id: 'unknown', fare: '₹800' }], 'fastest')).toHaveLength(0);
  });
});
