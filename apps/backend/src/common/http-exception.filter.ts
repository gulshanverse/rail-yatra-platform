import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Logger,
  Optional,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { SentryService } from '../monitoring/sentry.service';

@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger('ExceptionFilter');

  constructor(@Optional() private readonly sentryService?: SentryService) {}

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    let displayMessage: unknown =
      'An unexpected internal server error occurred.';
    if (exception instanceof HttpException) {
      const responseBody = exception.getResponse();
      if (typeof responseBody === 'string') {
        displayMessage = responseBody;
      } else if (responseBody && typeof responseBody === 'object') {
        const bodyObj = responseBody as Record<string, unknown>;
        displayMessage = bodyObj.message || responseBody;
      }
    }

    const correlationId =
      (request.headers['x-correlation-id'] as string) ||
      (request.headers['traceparent'] as string) ||
      'system';

    let errorName = 'Error';
    let errorMessage = String(exception);
    if (exception instanceof Error) {
      errorName = exception.name;
      errorMessage = exception.message;
    } else if (exception && typeof exception === 'object') {
      const errObj = exception as Record<string, unknown>;
      if (typeof errObj.name === 'string') errorName = errObj.name;
      if (typeof errObj.message === 'string') errorMessage = errObj.message;
    }

    if (status >= 500 && this.sentryService) {
      void this.sentryService.captureException(exception, {
        path: request.url,
        method: request.method,
        status,
        correlationId,
      });
    }

    // Structured JSON logging
    this.logger.error(
      JSON.stringify({
        timestamp: new Date().toISOString(),
        logLevel: 'ERROR',
        requestId: correlationId,
        method: request.method,
        path: request.url,
        status,
        errorName,
        errorMessage,
      }),
    );

    response.setHeader('x-correlation-id', String(correlationId));
    response.status(status).json({
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      message: displayMessage,
      correlationId,
    });
  }
}
