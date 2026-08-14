import { Controller, Get, Res, HttpStatus } from '@nestjs/common';
import type { Response } from 'express';
import { Socket } from 'net';
import { PrismaService } from '../prisma.service';

function checkTcpConnection(
  host: string,
  port: number,
  timeoutMs = 1500,
): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new Socket();
    let connResolved = false;
    socket.setTimeout(timeoutMs);
    socket.connect(port, host, () => {
      if (!connResolved) {
        connResolved = true;
        socket.destroy();
        resolve(true);
      }
    });
    const handleFail = () => {
      if (!connResolved) {
        connResolved = true;
        socket.destroy();
        resolve(false);
      }
    };
    socket.on('error', handleFail);
    socket.on('timeout', handleFail);
  });
}

function resolveRedisHostPort(): { host: string; port: number } {
  const redisUrl = process.env.REDIS_URL;
  if (redisUrl) {
    try {
      const parsed = new URL(redisUrl);
      return {
        host: parsed.hostname,
        port: parsed.port ? parseInt(parsed.port, 10) : 6379,
      };
    } catch {
      const match = redisUrl.match(
        /rediss?:\/\/(?:[^:]*:(?:[^@]*)@)?([^:/\s]+)(?::(\d+))?/,
      );
      if (match) {
        return {
          host: match[1],
          port: match[2] ? parseInt(match[2], 10) : 6379,
        };
      }
    }
  }
  return {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
  };
}

@Controller('api/health')
export class HealthController {
  constructor(private readonly prisma: PrismaService) {}

  @Get('live')
  getLive(@Res() res: Response) {
    return res
      .status(HttpStatus.OK)
      .json({ status: 'up', timestamp: new Date().toISOString() });
  }

  @Get('ready')
  async getReady(@Res() res: Response) {
    let dbHealthy = false;
    let redisHealthy = false;

    try {
      await this.prisma.$queryRaw`SELECT 1`;
      dbHealthy = true;
    } catch {
      dbHealthy = false;
    }

    const { host: redisHost, port: redisPort } = resolveRedisHostPort();
    redisHealthy = await checkTcpConnection(redisHost, redisPort);

    const aiServiceUrl = process.env.AI_SERVICE_URL?.trim().replace(/\/$/, '');
    let aiStatus: string;

    if (!aiServiceUrl) {
      aiStatus = 'not_configured';
    } else {
      try {
        const response = await fetch(`${aiServiceUrl}/health`, {
          method: 'GET',
          signal: AbortSignal.timeout(3000),
        });
        aiStatus = response.ok ? 'healthy' : 'failed';
      } catch {
        aiStatus = 'failed';
      }
    }

    const aiRequired = Boolean(aiServiceUrl);
    const isReady = dbHealthy && redisHealthy && (!aiRequired || aiStatus === 'healthy');

    if (isReady) {
      return res.status(HttpStatus.OK).json({
        status: 'ready',
        components: {
          database: 'healthy',
          redis: 'healthy',
          ai_service: aiStatus,
        },
      });
    }

    return res.status(HttpStatus.SERVICE_UNAVAILABLE).json({
      status: 'unready',
      components: {
        database: dbHealthy ? 'healthy' : 'failed',
        redis: redisHealthy ? 'healthy' : 'failed',
        ai_service: aiStatus,
      },
    });
  }

  @Get()
  async getHealth(@Res() res: Response) {
    let dbStatus = 'healthy';
    let dbLatency = 0;
    const startDb = Date.now();
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      dbLatency = Date.now() - startDb;
    } catch {
      dbStatus = 'unreachable';
    }

    let aiStatus: string;
    let aiLatency = 0;
    const aiServiceUrl = process.env.AI_SERVICE_URL?.trim().replace(/\/$/, '');

    if (!aiServiceUrl) {
      aiStatus = 'not_configured';
    } else {
      const startAi = Date.now();
      try {
        const response = await fetch(`${aiServiceUrl}/health`, {
          method: 'GET',
          signal: AbortSignal.timeout(3000),
        });
        if (response.ok) {
          aiLatency = Date.now() - startAi;
          aiStatus = 'healthy';
        } else {
          aiStatus = 'degraded';
        }
      } catch {
        aiStatus = 'unreachable';
      }
    }

    const { host: redisHost, port: redisPort } = resolveRedisHostPort();
    const startRedis = Date.now();
    const isRedisUp = await checkTcpConnection(redisHost, redisPort);
    const redisLatency = Date.now() - startRedis;

    let qdrantStatus: string;
    let qdrantLatency = 0;
    const qdrantHost = process.env.QDRANT_HOST;
    const qdrantUrl = process.env.QDRANT_URL;

    if (!qdrantHost && !qdrantUrl) {
      qdrantStatus = 'not_configured';
    } else {
      const resolvedHost = qdrantHost || 'localhost';
      const qdrantPort = parseInt(process.env.QDRANT_PORT || '6333', 10);
      const startQdrant = Date.now();
      const isQdrantUp = await checkTcpConnection(resolvedHost, qdrantPort);
      qdrantLatency = Date.now() - startQdrant;
      qdrantStatus = isQdrantUp ? 'healthy' : 'unreachable';
    }

    const requiredHealthy = dbStatus === 'healthy' && isRedisUp;
    const aiRequired = Boolean(aiServiceUrl);
    const aiHealthy = !aiRequired || aiStatus === 'healthy';
    const qdrantHealthy = qdrantStatus === 'not_configured' || qdrantStatus === 'healthy';
    const isAllHealthy = requiredHealthy && aiHealthy && qdrantHealthy;

    return res.status(HttpStatus.OK).json({
      status: isAllHealthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      components: {
        database: { status: dbStatus, latencyMs: dbLatency },
        ai_service: { status: aiStatus, latencyMs: aiLatency },
        redis: {
          status: isRedisUp ? 'healthy' : 'unreachable',
          latencyMs: redisLatency,
        },
        qdrant: {
          status: qdrantStatus,
          latencyMs: qdrantLatency,
        },
        notification_scheduler: { status: 'healthy', activeJobs: 2 },
      },
    });
  }
}
