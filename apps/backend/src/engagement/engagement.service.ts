import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { ReminderSchedulerService } from './scheduler.service';
import {
  EmailChannelService,
  SmsChannelService,
  PushChannelService,
  WhatsappChannelService,
} from './channels';
import { renderTemplate } from './templates';

@Injectable()
export class EngagementService {
  private readonly logger = new Logger(EngagementService.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly scheduler: ReminderSchedulerService,
    private readonly emailChannel: EmailChannelService,
    private readonly smsChannel: SmsChannelService,
    private readonly pushChannel: PushChannelService,
    private readonly whatsappChannel: WhatsappChannelService,
  ) {
    // Bind scheduler trigger to our local notification dispatch pipeline
    this.scheduler.registerNotificationCallback(
      async (userId, title, msg, category, priority) => {
        await this.dispatchNotification(userId, title, msg, category, priority);
      },
    );
  }

  async getPreferences(userId: string) {
    let prefs = await this.prisma.notificationPreference.findUnique({
      where: { userId },
    });

    if (!prefs) {
      prefs = await this.prisma.notificationPreference.create({
        data: { userId },
      });
    }

    return prefs;
  }

  async isDuplicate(
    userId: string,
    category: string,
    title: string,
    windowMins = 5,
  ): Promise<boolean> {
    const timeLimit = new Date(Date.now() - windowMins * 60 * 1000);
    const count = await this.prisma.notification.count({
      where: {
        userId,
        category,
        title,
        timestamp: { gte: timeLimit },
      },
    });
    return count > 0;
  }

  private _isWithinQuietHours(startStr: string, endStr: string): boolean {
    const now = new Date();
    const currentMin = now.getHours() * 60 + now.getMinutes();

    const parseTime = (str: string) => {
      const parts = str.split(':');
      return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
    };

    const startMin = parseTime(startStr);
    const endMin = parseTime(endStr);

    if (startMin <= endMin) {
      return currentMin >= startMin && currentMin <= endMin;
    } else {
      // Overlap midnight (e.g. 22:00 to 06:00)
      return currentMin >= startMin || currentMin <= endMin;
    }
  }

  async incrementEngagementScore(
    userId: string,
    actionPoints: number,
  ): Promise<number> {
    const scoreRow = await this.prisma.engagementScore.findUnique({
      where: { userId },
    });

    if (scoreRow) {
      const updated = await this.prisma.engagementScore.update({
        where: { userId },
        data: {
          score: scoreRow.score + actionPoints,
          lastTriggered: new Date(),
        },
      });
      return updated.score;
    } else {
      const created = await this.prisma.engagementScore.create({
        data: {
          userId,
          score: actionPoints,
        },
      });
      return created.score;
    }
  }

  async dispatchNotification(
    userId: string,
    title: string,
    message: string,
    category: string,
    priority = 'medium',
  ): Promise<boolean> {
    this.logger.log(
      `Dispatching notification. User: ${userId}, Title: ${title}, Category: ${category}`,
    );

    // 1. Check Deduplication Layer
    const isDup = await this.isDuplicate(userId, category, title);
    if (isDup) {
      this.logger.warn(
        `Deduplication: Blocked repeat alert '${title}' for user ${userId}`,
      );
      return false;
    }

    // 2. Load preferences & evaluate channels
    const prefs = await this.getPreferences(userId);
    const userProfile = await this.prisma.user.findUnique({
      where: { id: userId },
    });

    if (!userProfile) {
      this.logger.error(`User profile ${userId} not found.`);
      return false;
    }

    // 3. Evaluate Quiet Hours Constraints
    let channelMutedByQuietHours = false;
    if (this._isWithinQuietHours(prefs.quietHoursStart, prefs.quietHoursEnd)) {
      if (priority !== 'critical' && priority !== 'high') {
        channelMutedByQuietHours = true;
        this.logger.log(
          `Quiet Hours: Active. Muting channels for notification: ${title}`,
        );
      }
    }

    // 4. Save to central notification inbox db table
    await this.prisma.notification.create({
      data: {
        userId,
        title,
        message,
        category,
        priority,
        channel: prefs.pushAlerts ? 'push' : 'email',
      },
    });

    // 5. Route dispatches based on preferences and quiet hours gating
    if (!channelMutedByQuietHours) {
      const dispatchPromises: Promise<void>[] = [];

      if (prefs.emailAlerts && userProfile.email) {
        dispatchPromises.push(
          this.emailChannel
            .send(userId, userProfile.email, title, message)
            .then((ok) => this.logDelivery(userId, 'email', ok)),
        );
      }
      if (prefs.smsAlerts && userProfile.phone) {
        dispatchPromises.push(
          this.smsChannel
            .send(userId, userProfile.phone, title, message)
            .then((ok) => this.logDelivery(userId, 'sms', ok)),
        );
      }
      if (prefs.pushAlerts) {
        dispatchPromises.push(
          this.pushChannel
            .send(userId, 'browser', title, message)
            .then((ok) => this.logDelivery(userId, 'push', ok)),
        );
      }
      if (prefs.whatsappAlerts && userProfile.phone) {
        dispatchPromises.push(
          this.whatsappChannel
            .send(userId, userProfile.phone, title, message)
            .then((ok) => this.logDelivery(userId, 'whatsapp', ok)),
        );
      }

      await Promise.all(dispatchPromises).catch((err) => {
        this.logger.error(`Error in delivery dispatches: ${err}`);
      });
    }

    return true;
  }

  async logDelivery(
    userId: string,
    channel: string,
    success: boolean,
    errorMsg?: string,
  ) {
    await this.prisma.deliveryLog.create({
      data: {
        userId,
        channel,
        status: success ? 'success' : 'failed',
        errorMsg: errorMsg || null,
      },
    });
  }

  async dispatchTemplateNotification(
    userId: string,
    templateKey: string,
    variables: Record<string, string | number>,
  ): Promise<boolean> {
    const rendered = renderTemplate(templateKey, variables);
    return this.dispatchNotification(
      userId,
      rendered.title,
      rendered.message,
      rendered.category,
      rendered.priority,
    );
  }
}
