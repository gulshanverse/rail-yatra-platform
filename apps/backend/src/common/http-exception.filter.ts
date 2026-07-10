import { ExceptionFilter, Catch, ArgumentsHost, HttpException, HttpStatus, Logger } from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger('ExceptionFilter');

  catch(exception: any, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    
    const status = exception instanceof HttpException 
      ? exception.getStatus() 
      : HttpStatus.INTERNAL_SERVER_ERROR;

    const message = exception instanceof HttpException 
      ? exception.getResponse() 
      : 'An unexpected internal server error occurred.';

    const correlationId = request.headers['x-correlation-id'] || 'system';

    // Structured JSON logging
    this.logger.error(
      JSON.stringify({
        timestamp: new Date().toISOString(),
        logLevel: 'ERROR',
        requestId: correlationId,
        method: request.method,
        path: request.url,
        status,
        errorName: exception?.name || 'Error',
        errorMessage: exception?.message || String(exception),
      })
    );

    response.setHeader('x-correlation-id', String(correlationId));
    response.status(status).json({
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      message: typeof message === 'object' ? (message as any).message || message : message,
      correlationId,
    });
  }
}
