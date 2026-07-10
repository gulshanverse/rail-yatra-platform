import { Injectable, NestMiddleware, HttpStatus, Logger } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';

interface RateLimitData {
  count: number;
  resetTime: number;
}

@Injectable()
export class SecurityAndRateLimitMiddleware implements NestMiddleware {
  private readonly logger = new Logger(SecurityAndRateLimitMiddleware.name);
  
  // Lightweight In-Memory IP Registry for Rate Limiting
  private static ipRegistry = new Map<string, RateLimitData>();
  private static readonly LIMIT = 150; // 150 requests per minute
  private static readonly WINDOW_MS = 60 * 1000; // 1 minute window

  use(req: Request, res: Response, next: NextFunction) {
    const ip = req.ip || req.connection.remoteAddress || '127.0.0.1';
    const now = Date.now();

    // 1. Apply Security Headers (Helmet-inspired secure defaults)
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.setHeader(
      'Content-Security-Policy',
      "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    );
    res.setHeader('Strict-Transport-Security', 'max-age=15552000; includeSubDomains');

    // Generate Request Correlation ID if not present
    if (!req.headers['x-correlation-id']) {
      req.headers['x-correlation-id'] = `req_${Math.random().toString(36).substring(4)}`;
    }
    res.setHeader('x-correlation-id', String(req.headers['x-correlation-id']));

    // 2. Evaluate Rate Limiting
    let limitData = SecurityAndRateLimitMiddleware.ipRegistry.get(ip);
    if (!limitData || now >= limitData.resetTime) {
      limitData = {
        count: 1,
        resetTime: now + SecurityAndRateLimitMiddleware.WINDOW_MS,
      };
      SecurityAndRateLimitMiddleware.ipRegistry.set(ip, limitData);
    } else {
      limitData.count++;
    }

    if (limitData.count > SecurityAndRateLimitMiddleware.LIMIT) {
      this.logger.warn(`Rate Limit Exceeded: Client ${ip} locked out. Request count: ${limitData.count}`);
      
      res.setHeader('Retry-After', Math.round((limitData.resetTime - now) / 1000));
      return res.status(HttpStatus.TOO_MANY_REQUESTS).json({
        statusCode: 429,
        timestamp: new Date().toISOString(),
        path: req.url,
        message: 'Too Many Requests: Rate limit exceeded. Please try again later.',
        correlationId: req.headers['x-correlation-id'],
      });
    }

    next();
  }
}
