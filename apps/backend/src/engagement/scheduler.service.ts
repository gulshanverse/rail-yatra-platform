import { Injectable, Logger, OnApplicationBootstrap, OnApplicationShutdown } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

@Injectable()
export class ReminderSchedulerService implements OnApplicationBootstrap, OnApplicationShutdown {
  private readonly logger = new Logger(ReminderSchedulerService.name);
  private intervalId: NodeJS.Timeout | null = null;
  private isProcessing = false;

  // We expose a callback binder to avoid circular dependencies with EngagementService
  private notificationCallback: ((userId: string, title: string, message: string, category: string, priority: string) => Promise<void>) | null = null;

  constructor(private readonly prisma: PrismaService) {}

  registerNotificationCallback(callback: (userId: string, title: string, message: string, category: string, priority: string) => Promise<void>) {
    this.notificationCallback = callback;
  }

  onApplicationBootstrap() {
    this.logger.log('Bootstrapping engagement reminders scheduler loop...');
    // Scan pending schedules every 10 seconds for testing/development responsiveness
    this.intervalId = setInterval(() => this.processPendingSchedules(), 10000);
  }

  onApplicationShutdown() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.logger.log('Engagement reminders scheduler stopped.');
    }
  }

  async processPendingSchedules() {
    if (this.isProcessing) return;
    this.isProcessing = true;

    try {
      const now = new Date();
      const pendingSchedules = await this.prisma.reminderSchedule.findMany({
        where: {
          status: 'pending',
          triggerTime: { lte: now },
        },
      });

      if (pendingSchedules.length > 0) {
        this.logger.log(`Found ${pendingSchedules.length} pending reminders ready to trigger.`);
      }

      for (const schedule of pendingSchedules) {
        try {
          // Trigger the notification dispatch callback
          if (this.notificationCallback) {
            await this.notificationCallback(
              schedule.userId,
              schedule.title,
              schedule.description,
              'Journey',
              'high'
            );
          }

          // Mark schedule completed
          await this.prisma.reminderSchedule.update({
            where: { id: schedule.id },
            data: { status: 'sent' },
          });

          this.logger.log(`Reminder '${schedule.title}' dispatched to user ${schedule.userId}`);
        } catch (err) {
          this.logger.error(`Failed to trigger reminder ${schedule.id}: ${err}`);
          await this.prisma.reminderSchedule.update({
            where: { id: schedule.id },
            data: { status: 'failed' },
          });
        }
      }
    } catch (err) {
      this.logger.error(`Error in scheduler processing: ${err}`);
    } finally {
      this.isProcessing = false;
    }
  }

  async addReminder(
    userId: string,
    title: string,
    description: string,
    triggerTime: Date,
    reminderType: string,
    metadata?: Record<string, any>
  ) {
    this.logger.log(`Scheduling reminder: ${title} for user ${userId} at ${triggerTime.toISOString()}`);
    return this.prisma.reminderSchedule.create({
      data: {
        userId,
        title,
        description,
        triggerTime,
        reminderType,
        metadata: metadata ? JSON.stringify(metadata) : null,
      },
    });
  }
}
