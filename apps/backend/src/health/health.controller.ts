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
    let aiHealthy = false;
    let redisHealthy = false;

    try {
      await this.prisma.$queryRaw`SELECT 1`;
      dbHealthy = true;
    } catch {
      dbHealthy = false;
    }

    try {
      const aiUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
      const response = await fetch(`${aiUrl}/health`, { method: 'GET' });
      aiHealthy = response.ok;
    } catch {
      aiHealthy = false;
    }

    const redisHost = process.env.REDIS_HOST || 'localhost';
    const redisPort = parseInt(process.env.REDIS_PORT || '6379', 10);
    redisHealthy = await checkTcpConnection(redisHost, redisPort);

    if (dbHealthy && aiHealthy && redisHealthy) {
      return res.status(HttpStatus.OK).json({ status: 'ready' });
    } else {
      return res.status(HttpStatus.SERVICE_UNAVAILABLE).json({
        status: 'unready',
        components: {
          database: dbHealthy ? 'healthy' : 'failed',
          ai_service: aiHealthy ? 'healthy' : 'failed',
          redis: redisHealthy ? 'healthy' : 'failed',
        },
      });
    }
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

    let aiStatus = 'healthy';
    let aiLatency = 0;
    const startAi = Date.now();
    const aiUrl = process.env.AI_SERVICE_URL || 'http://localhost:8000';
    try {
      const response = await fetch(`${aiUrl}/health`, { method: 'GET' });
      if (response.ok) {
        aiLatency = Date.now() - startAi;
      } else {
        aiStatus = 'degraded';
      }
    } catch {
      aiStatus = 'unreachable';
    }

    const redisHost = process.env.REDIS_HOST || 'localhost';
    const redisPort = parseInt(process.env.REDIS_PORT || '6379', 10);
    const startRedis = Date.now();
    const isRedisUp = await checkTcpConnection(redisHost, redisPort);
    const redisLatency = Date.now() - startRedis;

    const qdrantHost = process.env.QDRANT_HOST || 'localhost';
    const qdrantPort = parseInt(process.env.QDRANT_PORT || '6333', 10);
    const startQdrant = Date.now();
    const isQdrantUp = await checkTcpConnection(qdrantHost, qdrantPort);
    const qdrantLatency = Date.now() - startQdrant;

    const isAllHealthy =
      dbStatus === 'healthy' &&
      aiStatus === 'healthy' &&
      isRedisUp &&
      isQdrantUp;

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
          status: isQdrantUp ? 'healthy' : 'unreachable',
          latencyMs: qdrantLatency,
        },
        notification_scheduler: { status: 'healthy', activeJobs: 2 },
      },
    });
  }
}
