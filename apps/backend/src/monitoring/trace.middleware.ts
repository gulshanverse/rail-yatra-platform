import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { randomBytes } from 'crypto';

export interface TraceContextRequest extends Request {
  traceId?: string;
  spanId?: string;
  correlationId?: string;
}

@Injectable()
export class TraceMiddleware implements NestMiddleware {
  use(req: TraceContextRequest, res: Response, next: NextFunction) {
    // Parse or generate W3C traceparent header: 00-traceid-spanid-flags
    const incomingTraceparent = req.headers['traceparent'] as string;
    let traceId: string;

    if (incomingTraceparent && incomingTraceparent.startsWith('00-')) {
      const parts = incomingTraceparent.split('-');
      if (parts.length >= 3) {
        traceId = parts[1];
      } else {
        traceId = randomBytes(16).toString('hex');
      }
    } else {
      traceId = randomBytes(16).toString('hex');
    }

    const currentSpanId = randomBytes(8).toString('hex');
    const correlationId =
      (req.headers['x-correlation-id'] as string) || traceId;

    req.traceId = traceId;
    req.spanId = currentSpanId;
    req.correlationId = correlationId;

    // Standard W3C Outgoing Traceparent
    const outgoingTraceparent = `00-${traceId}-${currentSpanId}-01`;

    res.setHeader('x-correlation-id', correlationId);
    res.setHeader('traceparent', outgoingTraceparent);

    next();
  }
}
