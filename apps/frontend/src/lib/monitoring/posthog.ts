/**
 * PostHog Product Analytics SDK Wrapper
 */

export function trackEvent(eventName: string, properties: Record<string, unknown> = {}) {
  const apiKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!apiKey || typeof window === 'undefined') {
    return;
  }

  // Anonymize properties prior to tracking
  const safeProperties = { ...properties };
  delete safeProperties.email;
  delete safeProperties.phone;
  delete safeProperties.pnr;
  delete safeProperties.password;

  try {
    const win = window as unknown as { posthog?: { capture: (name: string, props: unknown) => void } };
    if (win.posthog) {
      win.posthog.capture(eventName, safeProperties);
    }
  } catch {
    // Fallback gracefully
  }
}
