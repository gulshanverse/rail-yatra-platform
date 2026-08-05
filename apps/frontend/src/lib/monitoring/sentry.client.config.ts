/**
 * Sentry Client Configuration for Next.js Frontend
 */

export function initSentryClient() {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
  const env = process.env.NODE_ENV || 'production';

  if (!dsn) {
    if (typeof window !== 'undefined') {
      console.log('[Monitoring] Client Sentry operating in log-only mode.');
    }
    return;
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-require-imports
    const Sentry = (eval)('require')('@sentry/nextjs');
    if (Sentry && typeof Sentry.init === 'function') {
      Sentry.init({
        dsn,
        environment: env,
        tracesSampleRate: 0.1,
        replaysSessionSampleRate: 0.01,
        replaysOnErrorSampleRate: 1.0,
      });
    }
  } catch {
    // Graceful fallback if Sentry SDK isn't present
  }
}
