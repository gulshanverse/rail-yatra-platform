import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import cookieParser from 'cookie-parser';
import { AppModule } from './app.module';
import { GlobalExceptionFilter } from './common/http-exception.filter';
import { LoggingInterceptor } from './common/logging.interceptor';
import { PrismaService } from './prisma.service';

async function bootstrap() {
  const logger = new Logger('Bootstrap');

  // 1. Validate environment configuration profiles on startup
  const requiredEnvVars = ['DATABASE_URL', 'JWT_SECRET'];
  for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
      logger.error(`[FATAL CONFIGURATION ERROR] Missing critical environment variable: ${envVar}. Process aborting.`);
      process.exit(1);
    }
  }

  const app = await NestFactory.create(AppModule);
  
  // Enable CORS
  const corsOrigin = process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : '*';
  app.enableCors({
    origin: corsOrigin,
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
    credentials: true,
  });

  app.use(cookieParser());

  // Register global HTTP Filters & Interceptors
  app.useGlobalFilters(new GlobalExceptionFilter());
  app.useGlobalInterceptors(new LoggingInterceptor());

  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    transform: true,
  }));

  const port = process.env.PORT ?? 5000;
  const server = await app.listen(port);
  logger.log(`[Backend Service] core api running on: http://localhost:${port}`);

  // 2. Handle Graceful Shutdown Signal Interrupts
  const gracefulShutdown = async (signal: string) => {
    logger.warn(`Received signal ${signal}. Starting graceful shutdown procedure...`);
    
    // Stop accepting new connections
    server.close(async () => {
      logger.log('Draining active HTTP connection pools completed.');
      
      try {
        // Disconnect DB client pool
        const prisma = app.get(PrismaService);
        await prisma.$disconnect();
        logger.log('Database pool connection closed.');
      } catch (err) {
        logger.error(`Error closing database pool connection: ${err}`);
      }

      logger.log('Process terminating successfully.');
      process.exit(0);
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
bootstrap();
