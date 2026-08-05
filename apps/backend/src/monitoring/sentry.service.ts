import { Injectable, Logger } from '@nestjs/common';

interface SentryModule {
  captureException: (exception: unknown, options?: { extra?: unknown }) => void;
  captureMessage: (message: string, level?: string) => void;
}

@Injectable()
export class SentryService {
  private readonly logger = new Logger(SentryService.name);
  private readonly isEnabled: boolean;
  private readonly environment: string;

  constructor() {
    this.environment = process.env.NODE_ENV || process.env.ENV || 'development';
    this.isEnabled = Boolean(process.env.SENTRY_DSN);

    if (this.isEnabled) {
      this.logger.log(
        `Sentry error tracking initialized for environment: ${this.environment}`,
      );
    } else {
      this.logger.log(
        'Sentry DSN not provided. Fallback structured logging active.',
      );
    }
  }

  async captureException(
    exception: unknown,
    contextData?: Record<string, unknown>,
  ) {
    const sanitizedContext = this.sanitizeData(contextData || {});

    if (this.isEnabled) {
      try {
        const sentry =
          (await import('@sentry/node')) as unknown as SentryModule;
        sentry.captureException(exception, { extra: sanitizedContext });
      } catch {
        // Fallback gracefully if package is not present
      }
    }

    // Always output structured log with correlation ID
    const errorObj =
      exception instanceof Error
        ? {
            name: exception.name,
            message: exception.message,
            stack: exception.stack,
          }
        : { raw: String(exception) };

    this.logger.error(
      JSON.stringify({
        event: 'SENTRY_CAPTURE_EXCEPTION',
        environment: this.environment,
        error: errorObj,
        context: sanitizedContext,
        timestamp: new Date().toISOString(),
      }),
    );
  }

  async captureMessage(
    message: string,
    level: 'info' | 'warning' | 'error' = 'info',
  ) {
    if (this.isEnabled) {
      try {
        const sentry =
          (await import('@sentry/node')) as unknown as SentryModule;
        sentry.captureMessage(message, level);
      } catch {
        // Fallback gracefully
      }
    }
  }

  private sanitizeData(data: Record<string, unknown>): Record<string, unknown> {
    const sanitized: Record<string, unknown> = {};
    const sensitiveKeys = [
      'password',
      'secret',
      'token',
      'authorization',
      'jwt',
      'api_key',
      'credit_card',
      'pnr',
    ];

    for (const [key, value] of Object.entries(data)) {
      const lowerKey = key.toLowerCase();
      if (sensitiveKeys.some((k) => lowerKey.includes(k))) {
        sanitized[key] = '[REDACTED_SENSITIVE_DATA]';
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitizeData(value as Record<string, unknown>);
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }
}
