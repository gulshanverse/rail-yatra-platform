import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import cookieParser from 'cookie-parser';
import * as fs from 'fs';
import * as path from 'path';
import { Server } from 'http';
import { Socket } from 'net';
import { AppModule } from './app.module';
import { GlobalExceptionFilter } from './common/http-exception.filter';
import { LoggingInterceptor } from './common/logging.interceptor';
import { PrismaService } from './prisma.service';

// Load .env manually if process.env is missing key variables
const envPath = path.resolve(process.cwd(), '.env');
if (fs.existsSync(envPath)) {
  const envConfig = fs.readFileSync(envPath, 'utf8');
  for (const line of envConfig.split('\n')) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
      const idx = trimmed.indexOf('=');
      const key = trimmed.substring(0, idx).trim();
      let val = trimmed.substring(idx + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.substring(1, val.length - 1);
      }
      if (!process.env[key]) {
        process.env[key] = val;
      }
    }
  }
}

function checkTcpConnection(
  host: string,
  port: number,
  timeoutMs = 2000,
): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = new Socket();
    let resolved = false;
    socket.setTimeout(timeoutMs);
    socket.connect(port, host, () => {
      if (!resolved) {
        resolved = true;
        socket.destroy();
        resolve(true);
      }
    });
    const fail = () => {
      if (!resolved) {
        resolved = true;
        socket.destroy();
        resolve(false);
      }
    };
    socket.on('error', fail);
    socket.on('timeout', fail);
  });
}

async function bootstrap() {
  const logger = new Logger('Bootstrap');

  // 1. Validate environment configuration profiles on startup
  const requiredEnvVars = [
    'DATABASE_URL',
    'JWT_SECRET',
    'JWT_REFRESH_SECRET',
    'AI_SERVICE_URL',
  ];
  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      logger.error(
        `[FATAL CONFIGURATION ERROR] Missing critical environment variable: ${envVar}. Process aborting.`,
      );
      process.exit(1);
    }
  }

  // 2. Pre-flight Redis connection validation
  const redisUrl = process.env.REDIS_URL;
  let redisHost = process.env.REDIS_HOST || 'localhost';
  let redisPort = parseInt(process.env.REDIS_PORT || '6379', 10);
  if (redisUrl) {
    try {
      const parsed = new URL(redisUrl);
      redisHost = parsed.hostname;
      redisPort = parsed.port ? parseInt(parsed.port, 10) : 6379;
    } catch {
      const match = redisUrl.match(
        /rediss?:\/\/(?:[^:]*:(?:[^@]*)@)?([^:/\s]+)(?::(\d+))?/,
      );
      if (match) {
        redisHost = match[1];
        if (match[2]) {
          redisPort = parseInt(match[2], 10);
        }
      }
    }
  }

  logger.log(`Validating Redis connectivity to ${redisHost}:${redisPort}...`);
  const isRedisUp = await checkTcpConnection(redisHost, redisPort);
  if (!isRedisUp) {
    if (process.env.NODE_ENV === 'production') {
      logger.error(
        `[FATAL CONNECTION ERROR] Cannot connect to Redis at ${redisHost}:${redisPort}. Startup aborted.`,
      );
      process.exit(1);
    } else {
      logger.warn(
        `[WARNING] Cannot connect to Redis at ${redisHost}:${redisPort}. Continuing in development mode.`,
      );
    }
  } else {
    logger.log('Redis connectivity verified successfully.');
  }
  logger.log('Redis connectivity verified successfully.');

  const app = await NestFactory.create(AppModule);

  // Enable shutdown hooks for NestJS lifecycle mapping
  app.enableShutdownHooks();

  // Enable CORS with proper credential-compatible origin reflection
  const configuredOrigins = process.env.CORS_ORIGIN
    ? process.env.CORS_ORIGIN.split(',').map((s) => s.trim())
    : ['*'];

  app.enableCors({
    origin: (
      requestOrigin: string | undefined,
      callback: (err: Error | null, origin?: boolean | string) => void,
    ) => {
      // Allow requests with no origin (e.g. mobile apps, curl, same-origin)
      if (!requestOrigin) {
        return callback(null, true);
      }
      // If configured for wildcard or contains requested origin, reflect the requesting origin
      if (
        configuredOrigins.includes('*') ||
        configuredOrigins.includes(requestOrigin) ||
        requestOrigin.endsWith('.vercel.app') ||
        requestOrigin.endsWith('.onrender.com')
      ) {
        return callback(null, requestOrigin);
      }
      return callback(null, false);
    },
    optionsSuccessStatus: 204,
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
    credentials: true,
  });

  app.use(cookieParser());

  // Register global HTTP Filters & Interceptors
  app.useGlobalFilters(new GlobalExceptionFilter());
  app.useGlobalInterceptors(new LoggingInterceptor());

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
    }),
  );

  // 3. Pre-flight PostgreSQL validation
  const prisma = app.get(PrismaService);
  try {
    logger.log('Validating PostgreSQL connectivity...');
    await prisma.$queryRaw`SELECT 1`;
    logger.log('PostgreSQL connectivity verified successfully.');
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    logger.error(
      `[FATAL CONNECTION ERROR] PostgreSQL check failed: ${errorMsg}. Startup aborted.`,
    );
    process.exit(1);
  }

  const port = Number(process.env.PORT ?? 5000);
  const server = (await app.listen(port, '0.0.0.0')) as Server;
  logger.log(`Backend Service running on port ${port}`);

  // 4. Handle Graceful Shutdown Signal Interrupts
  const gracefulShutdown = (signal: string) => {
    logger.warn(
      `Received signal ${signal}. Starting graceful shutdown procedure...`,
    );

    server.close(() => {
      logger.log('Draining active HTTP connection pools completed.');

      const closeDb = async () => {
        try {
          // Disconnect DB client pool
          await prisma.$disconnect();
          logger.log('Database pool connection closed.');
        } catch (err) {
          logger.error(`Error closing database pool connection: ${err}`);
        }

        logger.log('Process terminating successfully.');
        process.exit(0);
      };

      void closeDb();
    });

    // Enforce hard exit timeout after 10 seconds if connections fail to drain
    setTimeout(() => {
      logger.error('Shutdown timeout reached. Force exiting.');
      process.exit(1);
    }, 10000);
  };

  process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
  process.on('SIGINT', () => gracefulShutdown('SIGINT'));
}
void bootstrap();
