import {
  Controller,
  Get,
  Post,
  Body,
  UseGuards,
  Req,
  Headers,
  Query,
} from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PermissionsGuard, RequirePermission } from './permissions.guard';
import { AdminService } from './admin.service';
import { PrismaService } from '../prisma.service';

interface AuthenticatedRequest extends Request {
  user: {
    id: string;
    email: string;
    fullName: string;
    role: string;
  };
}

@Controller('api/admin')
@UseGuards(JwtAuthGuard, PermissionsGuard)
export class AdminController {
  constructor(
    private readonly adminService: AdminService,
    private readonly prisma: PrismaService
  ) {}

  @Get('dashboard')
  @RequirePermission('admin:dashboard:view')
  async getDashboard() {
    return this.adminService.getAnalyticsOverview();
  }

  @Get('health')
  @RequirePermission('admin:dashboard:view')
  async getHealth() {
    return this.adminService.getSystemMetrics();
  }

  @Get('audit-logs')
  @RequirePermission('admin:audit:view')
  async getAuditLogs(
    @Query('search') search?: string,
    @Query('action') action?: string
  ) {
    const where: any = {};
    if (search) {
      where.OR = [
        { actorEmail: { contains: search } },
        { action: { contains: search } },
        { details: { contains: search } },
      ];
    }
    if (action) {
      where.action = action;
    }

    return this.prisma.auditLog.findMany({
      where,
      orderBy: { timestamp: 'desc' },
      take: 50,
    });
  }

  @Get('configs')
  @RequirePermission('admin:system:configuration')
  async getConfigs() {
    const flags = await this.adminService.getFeatureFlags();
    const configs = await this.adminService.getSystemConfigurations();
    return { flags, configs };
  }

  @Post('configs')
  @RequirePermission('admin:system:configuration')
  async updateConfig(
    @Req() req: AuthenticatedRequest,
    @Body() body: { key: string; value: string },
    @Headers('x-forwarded-for') ip: string,
    @Headers('user-agent') ua: string
  ) {
    return this.adminService.setSystemConfiguration(body.key, body.value, {
      id: req.user.id,
      email: req.user.email,
      ip: ip || '127.0.0.1',
      ua: ua || 'NestJS runtime',
    });
  }

  @Post('feature-flags')
  @RequirePermission('admin:featureflags:update')
  async toggleFlag(
    @Req() req: AuthenticatedRequest,
    @Body() body: { name: string; enabled: boolean },
    @Headers('x-forwarded-for') ip: string,
    @Headers('user-agent') ua: string
  ) {
    return this.adminService.setFeatureFlag(body.name, body.enabled, {
      id: req.user.id,
      email: req.user.email,
      ip: ip || '127.0.0.1',
      ua: ua || 'NestJS runtime',
    });
  }
}
