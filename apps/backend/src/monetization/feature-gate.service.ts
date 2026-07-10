import { Injectable, Logger, ForbiddenException } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { SUBSCRIPTION_PLANS } from './plans.config';

@Injectable()
export class FeatureGateService {
  private readonly logger = new Logger(FeatureGateService.name);

  constructor(private readonly prisma: PrismaService) {}

  async checkEntitlement(
    userId: string,
    action: 'ai_message' | 'journey_analysis' | 'pnr_check' | 'save_route'
  ): Promise<{ allowed: boolean; remaining: number; limit: number }> {
    this.logger.log(`Checking entitlements for user ${userId}, action: ${action}`);

    // 1. Fetch user subscription details (fallback to FREE default)
    let sub = await this.prisma.subscription.findFirst({
      where: { userId, status: 'active' },
    });

    if (!sub) {
      // Auto-initialize FREE subscription on first check
      sub = await this.prisma.subscription.create({
        data: {
          userId,
          tier: 'FREE',
          credits: SUBSCRIPTION_PLANS.FREE.monthlyCredits,
        },
      });
    }

    const plan = SUBSCRIPTION_PLANS[sub.tier] || SUBSCRIPTION_PLANS.FREE;

    // 2. Perform capacity evaluations based on active action type
    if (action === 'ai_message') {
      // Evaluate daily message limits
      const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
      const usedToday = await this.prisma.usageLog.count({
        where: { userId, action: 'ai_message', timestamp: { gte: yesterday } },
      });

      const limit = plan.dailyMessagesLimit;
      const remaining = Math.max(0, limit - usedToday);
      return { allowed: remaining > 0, remaining, limit };
    }

    if (action === 'journey_analysis') {
      // Monthly credits-based check
      const remaining = sub.credits;
      const limit = plan.monthlyCredits;
      return { allowed: remaining > 0, remaining, limit };
    }

    if (action === 'pnr_check') {
      // Limit of active monitoring histories
      const activePnrs = await this.prisma.pnrHistory.count({ where: { userId } });
      const limit = plan.pnrMonitorLimit;
      const remaining = Math.max(0, limit - activePnrs);
      return { allowed: remaining > 0, remaining, limit };
    }

    if (action === 'save_route') {
      // Limit of active saved junctions
      const savedRoutes = await this.prisma.savedRoute.count({ where: { userId } });
      const limit = plan.savedRoutesLimit;
      const remaining = Math.max(0, limit - savedRoutes);
      return { allowed: remaining > 0, remaining, limit };
    }

    return { allowed: true, remaining: 999, limit: 999 };
  }

  async logUsage(userId: string, action: string): Promise<void> {
    this.logger.log(`Logging usage: user ${userId}, action: ${action}`);
    
    // Write usage record
    await this.prisma.usageLog.create({
      data: { userId, action },
    });

    // If journey analysis is used, decrement subscription monthly credits
    if (action === 'journey_analysis') {
      const activeSub = await this.prisma.subscription.findFirst({
        where: { userId, status: 'active' },
      });
      
      if (activeSub && activeSub.credits > 0) {
        await this.prisma.subscription.update({
          where: { id: activeSub.id },
          data: { credits: activeSub.credits - 1 },
        });
      }
    }
  }

  async enforceEntitlement(
    userId: string,
    action: 'ai_message' | 'journey_analysis' | 'pnr_check' | 'save_route'
  ): Promise<void> {
    const result = await this.checkEntitlement(userId, action);
    if (!result.allowed) {
      throw new ForbiddenException(
        `Quota Exceeded: You have exhausted your plan limit for ${action}. (Limit: ${result.limit}). Please upgrade your RailYatra subscription.`
      );
    }
  }
}
