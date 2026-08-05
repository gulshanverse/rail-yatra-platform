/**
 * Sentry Server Configuration for Next.js Server Components
 */

export function initSentryServer() {
  const dsn = process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN;
  const env = process.env.NODE_ENV || 'production';

  if (!dsn) {
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
      });
    }
  } catch {
    // Fallback gracefully
  }
}
