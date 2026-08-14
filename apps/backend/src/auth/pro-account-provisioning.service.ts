import { Injectable, Logger } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import { PrismaService } from '../prisma.service';
import { SUBSCRIPTION_PLANS } from '../monetization/plans.config';

@Injectable()
export class ProAccountProvisioningService {
  private readonly logger = new Logger(ProAccountProvisioningService.name);

  constructor(private readonly prisma: PrismaService) {}

  async provisionFromEnvironment(): Promise<void> {
    const email = process.env.ADMIN_EMAIL?.trim().toLowerCase();
    const password = process.env.ADMIN_PASSWORD;
    const enabled = process.env.ADMIN_PRO_UNLIMITED === 'true';

    if (!enabled) {
      return;
    }

    if (!email || !password) {
      this.logger.warn(
        'ADMIN_PRO_UNLIMITED=true but ADMIN_EMAIL or ADMIN_PASSWORD is missing. Skipping pro account provisioning.',
      );
      return;
    }

    if (password.length < 12) {
      throw new Error('ADMIN_PASSWORD must be at least 12 characters long.');
    }

    const plan = SUBSCRIPTION_PLANS.PREMIUM_PLUS;
    const passwordHash = await bcrypt.hash(password, 12);

    const existingUser = await this.prisma.user.findUnique({
      where: { email },
      include: {
        settings: true,
        subscriptions: {
          where: { status: 'active' },
          orderBy: { createdAt: 'desc' },
          take: 1,
        },
      },
    });

    if (!existingUser) {
      await this.prisma.user.create({
        data: {
          email,
          fullName: 'RailYatra Admin',
          passwordHash,
          role: 'ADMIN',
          settings: {
            create: {
              theme: 'auto',
              notifications: true,
              language: 'en',
            },
          },
          subscriptions: {
            create: {
              tier: 'PREMIUM_PLUS',
              credits: plan.monthlyCredits,
              status: 'active',
            },
          },
        },
      });

      this.logger.log(`Provisioned production pro account for ${email}.`);
      return;
    }

    const activeSubscription = existingUser.subscriptions[0];

    await this.prisma.user.update({
      where: { id: existingUser.id },
      data: { role: 'ADMIN' },
    });

    if (activeSubscription) {
      await this.prisma.subscription.update({
        where: { id: activeSubscription.id },
        data: {
          tier: 'PREMIUM_PLUS',
          credits: plan.monthlyCredits,
          status: 'active',
          expiry: null,
        },
      });
    } else {
      await this.prisma.subscription.create({
        data: {
          userId: existingUser.id,
          tier: 'PREMIUM_PLUS',
          credits: plan.monthlyCredits,
          status: 'active',
        },
      });
    }

    this.logger.log(`Ensured production pro entitlements for ${email}.`);
  }
}
