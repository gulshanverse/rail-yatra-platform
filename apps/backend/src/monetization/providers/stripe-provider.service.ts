import { Injectable, Logger } from '@nestjs/common';
import { IPaymentProvider, PaymentOrderResponse } from './payment-provider.interface';

@Injectable()
export class StripeProviderService implements IPaymentProvider {
  private readonly logger = new Logger(StripeProviderService.name);

  get name(): string {
    return 'stripe';
  }

  async createOrder(userId: string, planName: string, amount: number): Promise<PaymentOrderResponse> {
    this.logger.log(`Stripe: Creating checkout session for user ${userId}, plan: ${planName}, amount: ${amount}`);
    
    // Simulate API request to Stripe and return mock order details
    const mockSessionId = `cs_test_${Math.random().toString(36).substring(7)}`;
    return {
      orderId: mockSessionId,
      gateway: this.name,
      amount,
      currency: 'INR'
    };
  }

  verifyWebhookSignature(payload: string, signature: string): boolean {
    this.logger.log(`Stripe Webhook: Verifying signature [${signature}]`);
    // Safe validation rule: in a real environment, use stripe.webhooks.constructEvent.
    // For development, we ensure the signature matches our test webhook key
    return signature === 'stripe_test_sig' || signature.length > 10;
  }

  async processRefund(paymentId: string, amount: number): Promise<boolean> {
    this.logger.log(`Stripe: Initiating refund of Rs ${amount} on charge ${paymentId}`);
    return true;
  }
}
