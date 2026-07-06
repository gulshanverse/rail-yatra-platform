import { Controller, Get, InternalServerErrorException } from '@nestjs/common';
import { AppService } from './app.service';
import { PrismaService } from './prisma.service';

@Controller()
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly prisma: PrismaService,
  ) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Get('health')
  async checkHealth() {
    try {
      // Test database connectivity
      await this.prisma.$queryRaw`SELECT 1`;
      return {
        status: 'healthy',
        service: 'backend-core',
        timestamp: new Date().toISOString(),
        database: 'connected',
      };
    } catch (error) {
      throw new InternalServerErrorException({
        status: 'unhealthy',
        service: 'backend-core',
        timestamp: new Date().toISOString(),
        database: 'disconnected',
        error: error.message || error,
      });
    }
  }
}

