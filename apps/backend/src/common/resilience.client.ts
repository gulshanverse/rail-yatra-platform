import { Logger } from '@nestjs/common';

export interface ResilienceOptions {
  maxRetries?: number;
  initialDelayMs?: number;
  timeoutMs?: number;
  failureThreshold?: number;
  resetTimeoutMs?: number;
}

export class ResilienceClient {
  private static readonly logger = new Logger(ResilienceClient.name);

  // Circuit Breaker State
  private static state: 'CLOSED' | 'OPEN' | 'HALF-OPEN' = 'CLOSED';
  private static consecutiveFailures = 0;
  private static nextAttemptTime = 0;

  static async requestWithRetry<T>(
    requestFn: () => Promise<T>,
    options?: ResilienceOptions,
  ): Promise<T> {
    const maxRetries = options?.maxRetries ?? 3;
    const initialDelayMs = options?.initialDelayMs ?? 100;
    const timeoutMs = options?.timeoutMs ?? 5000;
    const failureThreshold = options?.failureThreshold ?? 5;
    const resetTimeoutMs = options?.resetTimeoutMs ?? 30000;

    // 1. Evaluate Circuit Breaker status
    const now = Date.now();
    if (this.state === 'OPEN') {
      if (now >= this.nextAttemptTime) {
        this.logger.warn('Circuit Breaker entering HALF-OPEN state.');
        this.state = 'HALF-OPEN';
      } else {
        this.logger.warn(
          'Circuit Breaker is OPEN. Blocking request and returning fallback.',
        );
        throw new Error(
          'Circuit Breaker is open. Downstream service is currently unreachable.',
        );
      }
    }

    let lastError: Error | null = null;
    let delay = initialDelayMs;

    // 2. Execute call loop with Timeout & Exponential Backoff retries
    for (let attempt = 1; attempt <= maxRetries + 1; attempt++) {
      try {
        const timeoutPromise = new Promise<never>((_, reject) =>
          setTimeout(
            () => reject(new Error('Request Timeout Limit Breached.')),
            timeoutMs,
          ),
        );

        const result = await Promise.race([requestFn(), timeoutPromise]);

        // Success: Reset Circuit Breaker state
        if (this.state !== 'CLOSED') {
          this.logger.log(
            'Circuit Breaker recovered. Resetting status to CLOSED.',
          );
        }
        this.state = 'CLOSED';
        this.consecutiveFailures = 0;
        return result;
      } catch (err: unknown) {
        lastError = err instanceof Error ? err : new Error(String(err));
        this.logger.warn(
          `Resilience request failed (Attempt ${attempt}/${maxRetries + 1}): ${lastError.message}`,
        );

        // If it's the last attempt, do not wait before exiting
        if (attempt <= maxRetries) {
          // Add 20% random jitter to avoid thundering herd failures
          const jitter = (Math.random() - 0.5) * 0.2 * delay;
          await new Promise((resolve) => setTimeout(resolve, delay + jitter));
          delay *= 2; // Exponential multiply
        }
      }
    }

    // 3. Mark consecutive failures and trip Circuit Breaker if threshold reached
    this.consecutiveFailures++;
    if (this.consecutiveFailures >= failureThreshold) {
      this.state = 'OPEN';
      this.nextAttemptTime = Date.now() + resetTimeoutMs;
      this.logger.error(
        `Circuit Breaker tripped to OPEN. Muting requests for ${resetTimeoutMs}ms`,
      );
    }

    if (!lastError) {
      throw new Error('Request execution failed.');
    }
    throw lastError;
  }
}
