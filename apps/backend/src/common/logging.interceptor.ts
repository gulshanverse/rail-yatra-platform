import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
  Optional,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';
import { MetricsService } from '../monitoring/metrics.service';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  constructor(@Optional() private readonly metricsService?: MetricsService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const httpCtx = context.switchToHttp();
    const request = httpCtx.getRequest<Request>();
    const response = httpCtx.getResponse<Response>();

    const correlationId =
      (request.headers['x-correlation-id'] as string) ||
      (request.headers['traceparent'] as string) ||
      'system';
    const startTime = Date.now();

    return next.handle().pipe(
      tap(() => {
        const duration = Date.now() - startTime;
        const statusCode = response.statusCode;

        // Structured JSON Logging format
        const logData = {
          timestamp: new Date().toISOString(),
          logLevel: 'INFO',
          requestId: correlationId,
          method: request.method,
          path: request.url,
          status: statusCode,
          durationMs: duration,
        };

        if (this.metricsService) {
          this.metricsService.incrementCounter(
            'railyatra_backend_http_requests_total',
            1,
            { method: request.method, status: String(statusCode) },
          );
          this.metricsService.observeHistogram(
            'railyatra_backend_http_request_duration_seconds',
            duration / 1000,
            { method: request.method },
          );
          if (statusCode >= 500) {
            this.metricsService.incrementCounter(
              'railyatra_backend_errors_total',
              1,
              { status: String(statusCode) },
            );
          }
        }

        if (duration > 800) {
          this.logger.warn(
            `[SLOW PERFORMANCE DETECTION] ${JSON.stringify(logData)}`,
          );
        } else {
          this.logger.log(JSON.stringify(logData));
        }
      }),
    );
  }
}
