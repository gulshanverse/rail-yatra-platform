import { Injectable, Logger, BadRequestException, NotFoundException, InternalServerErrorException } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { StripeProviderService } from './providers/stripe-provider.service';
import { RazorpayProviderService } from './providers/razorpay-provider.service';
import { SUBSCRIPTION_PLANS } from './plans.config';
import { PaymentOrderResponse } from './providers/payment-provider.interface';

@Injectable()
export class MonetizationService {
  private readonly logger = new Logger(MonetizationService.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly stripe: StripeProviderService,
    private readonly razorpay: RazorpayProviderService
  ) {}

  private _getProvider(gateway: string) {
    const gw = gateway.toLowerCase();
    if (gw === 'stripe') return this.stripe;
    if (gw === 'razorpay') return this.razorpay;
    throw new BadRequestException(`Unsupported payment provider gateway: ${gateway}`);
  }

  async getActiveSubscription(userId: string) {
    let sub = await this.prisma.subscription.findFirst({
      where: { userId, status: 'active' },
    });
    
    if (!sub) {
      // Default auto initialization
      sub = await this.prisma.subscription.create({
        data: {
          userId,
          tier: 'FREE',
          credits: SUBSCRIPTION_PLANS.FREE.monthlyCredits,
        },
      });
    }
    
    return sub;
  }

  async checkout(userId: string, planName: string, gateway: string): Promise<PaymentOrderResponse> {
    this.logger.log(`Initiating checkout. User: ${userId}, Plan: ${planName}, Gateway: ${gateway}`);

    const plan = SUBSCRIPTION_PLANS[planName.toUpperCase()];
    if (!plan) {
      throw new BadRequestException(`Invalid subscription plan tier requested: ${planName}`);
    }

    if (plan.price === 0) {
      throw new BadRequestException(`Cannot checkout Free tier subscriptions via payment gateway.`);
    }

    const provider = this._getProvider(gateway);
    const order = await provider.createOrder(userId, planName.toUpperCase(), plan.price);

    // Save pending payment record in db
    await this.prisma.payment.create({
      data: {
        orderId: order.orderId,
        userId,
        gateway: provider.name,
        amount: plan.price,
        currency: plan.currency,
        status: 'pending',
      },
    });

    return order;
  }

  async handleWebhook(gateway: string, payload: any, signature: string): Promise<void> {
    this.logger.log(`Received webhook from gateway: ${gateway}`);

    const provider = this._getProvider(gateway);
    const rawPayload = JSON.stringify(payload);
    
    // Webhook Signature verification safety check
    const isVerified = provider.verifyWebhookSignature(rawPayload, signature);
    if (!isVerified) {
      this.logger.error(`Webhook Signature verification FAILED for gateway ${gateway}`);
      throw new BadRequestException('Webhook signature validation failed.');
    }

    // Determine event action
    const eventType = payload.event || payload.type || 'payment.success';
    const orderId = payload.orderId || payload.id || (payload.data?.object?.id) || 'mock_order';
    
    // Look up pending payment record
    const payment = await this.prisma.payment.findUnique({
      where: { orderId },
    });

    if (!payment) {
      this.logger.warn(`No matching payment record found for order ${orderId}. Processing custom/duplicate event.`);
      // Mock payment for orphan webhook test events
      return;
    }

    // Log the billing event in db
    await this.prisma.billingEvent.create({
      data: {
        userId: payment.userId,
        eventType: `${gateway}.${eventType}`,
        payload: rawPayload,
      },
    });

    if (eventType.includes('success') || eventType === 'checkout.session.completed') {
      // 1. Mark payment completed
      await this.prisma.payment.update({
        where: { id: payment.id },
        data: { status: 'completed' },
      });

      // 2. Generate Invoice
      const invoiceNum = `INV-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.random().toString(36).substring(4).toUpperCase()}`;
      await this.prisma.invoice.create({
        data: {
          paymentId: payment.id,
          userId: payment.userId,
          invoiceNumber: invoiceNum,
          amount: payment.amount,
          currency: payment.currency,
          status: 'paid',
        },
      });

      // Determine new subscription tier
      // (Normally we decode metadata, but synthetically we match payment amount to plan)
      let tier = 'FREE';
      if (payment.amount.toNumber() === SUBSCRIPTION_PLANS.PREMIUM.price) {
        tier = 'PREMIUM';
      } else if (payment.amount.toNumber() === SUBSCRIPTION_PLANS.PREMIUM_PLUS.price) {
        tier = 'PREMIUM_PLUS';
      }

      const plan = SUBSCRIPTION_PLANS[tier];
      const expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() + 30); // 30-day lifecycle

      // 3. Update User Subscription
      const existingSub = await this.prisma.subscription.findFirst({
        where: { userId: payment.userId, status: 'active' },
      });

      if (existingSub) {
        await this.prisma.subscription.update({
          where: { id: existingSub.id },
          data: {
            tier,
            expiry: expiryDate,
            credits: plan.monthlyCredits,
          },
        });
      } else {
        await this.prisma.subscription.create({
          data: {
            userId: payment.userId,
            tier,
            expiry: expiryDate,
            status: 'active',
            credits: plan.monthlyCredits,
          },
        });
      }

      // 4. Update user role in main User profile schema
      await this.prisma.user.update({
        where: { id: payment.userId },
        data: { role: tier },
      });

      this.logger.log(`Successfully upgraded user ${payment.userId} subscription to ${tier}`);
    } else if (eventType.includes('failed') || eventType.includes('canceled')) {
      // Mark payment failed
      await this.prisma.payment.update({
        where: { id: payment.id },
        data: { status: 'failed' },
      });
    }
  }

  async processRefund(paymentId: string, amount: number): Promise<boolean> {
    this.logger.log(`Admin Refund: paymentId ${paymentId}, amount ${amount}`);

    const payment = await this.prisma.payment.findUnique({
      where: { id: paymentId },
    });

    if (!payment || payment.status !== 'completed') {
      throw new BadRequestException('Cannot refund a non-completed payment.');
    }

    const provider = this._getProvider(payment.gateway);
    const success = await provider.processRefund(payment.orderId, amount);

    if (success) {
      // Log event
      await this.prisma.billingEvent.create({
        data: {
          userId: payment.userId,
          eventType: 'admin.refund_processed',
          payload: JSON.stringify({ paymentId, amount }),
        },
      });

      // Update invoice status
      const invoice = await this.prisma.invoice.findFirst({
        where: { paymentId: payment.id },
      });
      if (invoice) {
        await this.prisma.invoice.update({
          where: { id: invoice.id },
          data: { status: 'refunded' },
        });
      }

      // Downgrade subscription
      const sub = await this.prisma.subscription.findFirst({
        where: { userId: payment.userId, status: 'active' },
      });
      if (sub) {
        await this.prisma.subscription.update({
          where: { id: sub.id },
          data: {
            tier: 'FREE',
            credits: SUBSCRIPTION_PLANS.FREE.monthlyCredits,
            expiry: null,
          },
        });
      }

      // Reset user role to USER
      await this.prisma.user.update({
        where: { id: payment.userId },
        data: { role: 'USER' },
      });

      return true;
    }
    return false;
  }

  async manualAdjustSubscription(
    userId: string,
    tier: string,
    credits: number,
    expiryDays: number
  ) {
    this.logger.log(`Admin override: Adjusting User ${userId} -> Tier: ${tier}, Credits: ${credits}`);

    const plan = SUBSCRIPTION_PLANS[tier.toUpperCase()];
    if (!plan) {
      throw new BadRequestException(`Plan tier ${tier} does not exist.`);
    }

    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + expiryDays);

    const existingSub = await this.prisma.subscription.findFirst({
      where: { userId, status: 'active' },
    });

    if (existingSub) {
      await this.prisma.subscription.update({
        where: { id: existingSub.id },
        data: {
          tier: tier.toUpperCase(),
          credits,
          expiry: expiryDate,
        },
      });
    } else {
      await this.prisma.subscription.create({
        data: {
          userId,
          tier: tier.toUpperCase(),
          credits,
          expiry: expiryDate,
          status: 'active',
        },
      });
    }

    await this.prisma.user.update({
      where: { id: userId },
      data: { role: tier.toUpperCase() },
    });

    return { success: true, tier, credits, expiryDate };
  }
}
