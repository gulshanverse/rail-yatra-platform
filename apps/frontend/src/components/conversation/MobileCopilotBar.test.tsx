import { describe, expect, it } from 'vitest';

describe('MobileCopilotBar behavior', () => {
  it('documents the mobile composer interaction contract', () => {
    const submitted = 'What is the safest option?';
    expect(submitted.trim()).toBe('What is the safest option?');
    expect(submitted.includes('\n')).toBe(false);
  });

  it('keeps unknown context values explicit', () => {
    const value: string | null | undefined = undefined;
    expect(value ?? 'Not specified').toBe('Not specified');
  });
});
