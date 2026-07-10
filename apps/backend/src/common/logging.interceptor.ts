import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const httpCtx = context.switchToHttp();
    const request = httpCtx.getRequest<Request>();
    const response = httpCtx.getResponse<Response>();

    const correlationId = request.headers['x-correlation-id'] || 'system';
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
