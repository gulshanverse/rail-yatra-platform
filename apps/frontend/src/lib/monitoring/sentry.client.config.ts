/**
 * Sentry Client Configuration for Next.js Frontend
 */

export async function initSentryClient() {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
  const env = process.env.NODE_ENV || 'production';

  if (!dsn) {
    if (typeof window !== 'undefined') {
      console.log('[Monitoring] Client Sentry operating in log-only mode.');
    }
    return;
  }

  try {
    const Sentry = await import('@sentry/nextjs');
    Sentry.init({
      dsn,
      environment: env,
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0.01,
      replaysOnErrorSampleRate: 1.0,
      beforeSend(event) {
        // Redact PII from client error events
        if (event.request && event.request.headers) {
          delete event.request.headers['authorization'];
          delete event.request.headers['cookie'];
        }
        return event;
      },
    });
  } catch {
    // Graceful fallback if Sentry SDK isn't present
  }
}
