import {
  Controller,
  Get,
  Post,
  Patch,
  Body,
  Param,
  Query,
  UseGuards,
  Req,
  NotFoundException,
} from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PrismaService } from '../prisma.service';
import { EngagementService } from './engagement.service';
import { ReminderSchedulerService } from './scheduler.service';

interface AuthenticatedRequest extends Request {
  user: {
    id: string;
    email: string;
    fullName: string;
    role: string;
  };
}

@Controller('api/engagement')
@UseGuards(JwtAuthGuard)
export class EngagementController {
  constructor(
    private readonly engagementService: EngagementService,
    private readonly scheduler: ReminderSchedulerService,
    private readonly prisma: PrismaService
  ) {}

  @Get('notifications')
  async getNotifications(
    @Req() req: AuthenticatedRequest,
    @Query('filter') filter?: 'unread' | 'read' | 'all',
    @Query('category') category?: string
  ) {
    const where: any = { userId: req.user.id };
    
    if (filter === 'unread') where.read = false;
    else if (filter === 'read') where.read = true;
    
    if (category) where.category = category;

    return this.prisma.notification.findMany({
      where,
      orderBy: { timestamp: 'desc' },
    });
  }

  @Post('notifications/:id/read')
  async markAsRead(@Req() req: AuthenticatedRequest, @Param('id') id: string) {
    const notif = await this.prisma.notification.findFirst({
      where: { id, userId: req.user.id },
    });

    if (!notif) {
      throw new NotFoundException(`Notification with ID ${id} not found.`);
    }

    const updated = await this.prisma.notification.update({
      where: { id },
      data: { read: true },
    });

    // Award user +5 points for opening/reading notification
    const totalScore = await this.engagementService.incrementEngagementScore(req.user.id, 5);

    return { success: true, updated, engagementScore: totalScore };
  }

  @Post('notifications/read-all')
  async markAllAsRead(@Req() req: AuthenticatedRequest) {
    await this.prisma.notification.updateMany({
      where: { userId: req.user.id, read: false },
      data: { read: true },
    });
    return { success: true };
  }

  @Get('preferences')
  async getPreferences(@Req() req: AuthenticatedRequest) {
    return this.engagementService.getPreferences(req.user.id);
  }

  @Patch('preferences')
  async updatePreferences(
    @Req() req: AuthenticatedRequest,
    @Body() body: {
      emailAlerts?: boolean;
      smsAlerts?: boolean;
      pushAlerts?: boolean;
      whatsappAlerts?: boolean;
      quietHoursStart?: string;
      quietHoursEnd?: string;
      marketingAlerts?: boolean;
      digestPreference?: string;
    }
  ) {
    return this.prisma.notificationPreference.update({
      where: { userId: req.user.id },
      data: body,
    });
  }

  @Get('insights')
  async getInsights(@Req() req: AuthenticatedRequest) {
    // Return AI insights (or seed a mock first if empty)
    const insights = await this.prisma.userInsight.findMany({
      where: { userId: req.user.id },
      orderBy: { timestamp: 'desc' },
    });

    if (insights.length === 0) {
      // Auto seed default recommendation on first access
      const defaultInsight = await this.prisma.userInsight.create({
        data: {
          userId: req.user.id,
          title: 'AI Smart Recommendation: Save on Bhopal Corridors',
          content: 'We noticed you check flights/trains to Bhopal frequently. Dynamic waiting times are lower on Thursdays. Booking the Shatabdi Express on Thursday can save you 1.5 hours in transit time.',
        },
      });
      return [defaultInsight];
    }

    return insights;
  }

  @Get('score')
  async getScore(@Req() req: AuthenticatedRequest) {
    const row = await this.prisma.engagementScore.findUnique({
      where: { userId: req.user.id },
    });
    return { score: row ? row.score : 0 };
  }

  @Post('reminders')
  async createReminder(
    @Req() req: AuthenticatedRequest,
    @Body() body: { title: string; description: string; triggerTime: string; type: string }
  ) {
    const time = new Date(body.triggerTime);
    const schedule = await this.scheduler.addReminder(
      req.user.id,
      body.title,
      body.description,
      time,
      body.type
    );
    return { success: true, schedule };
  }
}
