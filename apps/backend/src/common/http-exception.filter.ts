import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger('ExceptionFilter');

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

    const correlationId = request.headers['x-correlation-id'] || 'system';

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
