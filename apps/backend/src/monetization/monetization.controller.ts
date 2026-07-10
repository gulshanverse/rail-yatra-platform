import {
  Controller,
  Get,
  Post,
  Body,
  Param,
  Headers,
  UseGuards,
  Req,
  ForbiddenException,
  HttpCode,
} from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PrismaService } from '../prisma.service';
import { MonetizationService } from './monetization.service';
import { FeatureGateService } from './feature-gate.service';
import { SUBSCRIPTION_PLANS } from './plans.config';
import type {
  AuthenticatedRequest,
  WebhookPayload,
} from '../common/interfaces';

@Controller('api/monetization')
export class MonetizationController {
  constructor(
    private readonly monetizationService: MonetizationService,
    private readonly featureGateService: FeatureGateService,
    private readonly prisma: PrismaService,
  ) {}

  @Get('plans')
  getPlans() {
    return SUBSCRIPTION_PLANS;
  }

  @Get('subscription')
  @UseGuards(JwtAuthGuard)
  async getSubscriptionDetails(@Req() req: AuthenticatedRequest) {
    const sub = await this.monetizationService.getActiveSubscription(
      req.user.id,
    );
    const plan = SUBSCRIPTION_PLANS[sub.tier] || SUBSCRIPTION_PLANS.FREE;

    // Fetch active usage values to populate user quota dashboard
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const dailyChatsUsed = await this.prisma.usageLog.count({
      where: {
        userId: req.user.id,
        action: 'ai_message',
        timestamp: { gte: yesterday },
      },
    });

    const activePnrsCount = await this.prisma.pnrHistory.count({
      where: { userId: req.user.id },
    });

    const savedRoutesCount = await this.prisma.savedRoute.count({
      where: { userId: req.user.id },
    });

    return {
      tier: sub.tier,
      expiry: sub.expiry,
      status: sub.status,
      creditsRemaining: sub.credits,
      dailyChatsUsed,
      activePnrsCount,
      savedRoutesCount,
      entitlements: {
        tierName: plan.tierName,
        price: plan.price,
        currency: plan.currency,
        monthlyCreditsLimit: plan.monthlyCredits,
        dailyMessagesLimit: plan.dailyMessagesLimit,
        pnrMonitorLimit: plan.pnrMonitorLimit,
        savedRoutesLimit: plan.savedRoutesLimit,
        features: plan.features,
      },
    };
  }

  @Post('checkout')
  @UseGuards(JwtAuthGuard)
  async checkout(
    @Req() req: AuthenticatedRequest,
    @Body() body: { planName: string; gateway: string },
  ) {
    return this.monetizationService.checkout(
      req.user.id,
      body.planName,
      body.gateway,
    );
  }

  @Get('invoices')
  @UseGuards(JwtAuthGuard)
  async getInvoices(@Req() req: AuthenticatedRequest) {
    return this.prisma.invoice.findMany({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' },
    });
  }

  // Webhook handler is anonymous.
  @Post('webhooks/:gateway')
  @HttpCode(200)
  async handleWebhook(
    @Param('gateway') gateway: string,
    @Body() body: WebhookPayload,
    @Headers('x-webhook-signature') signature: string,
  ) {
    // Falls back to a default sandbox test signature if webhook verification headers are absent
    const sig = signature || 'default_test_sig';
    await this.monetizationService.handleWebhook(gateway, body, sig);
    return { received: true };
  }

  // Admin controls
  @Post('admin/adjust')
  @UseGuards(JwtAuthGuard)
  async manualAdjust(
    @Req() req: AuthenticatedRequest,
    @Body()
    body: {
      targetUserId: string;
      tier: string;
      credits: number;
      expiryDays: number;
    },
  ) {
    if (req.user.role !== 'ADMIN' && req.user.role !== 'SUPER_ADMIN') {
      throw new ForbiddenException(
        'Manual adjustments are restricted to system administrators.',
      );
    }
    return this.monetizationService.manualAdjustSubscription(
      body.targetUserId,
      body.tier,
      body.credits,
      body.expiryDays,
    );
  }

  @Post('admin/refund')
  @UseGuards(JwtAuthGuard)
  async processRefund(
    @Req() req: AuthenticatedRequest,
    @Body() body: { paymentId: string; amount: number },
  ) {
    if (req.user.role !== 'ADMIN' && req.user.role !== 'SUPER_ADMIN') {
      throw new ForbiddenException(
        'Refund triggers are restricted to system administrators.',
      );
    }
    const success = await this.monetizationService.processRefund(
      body.paymentId,
      body.amount,
    );
    return { success };
  }
}
