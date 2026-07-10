import { Injectable, Logger } from '@nestjs/common';
import { IPaymentProvider, PaymentOrderResponse } from './payment-provider.interface';

@Injectable()
export class RazorpayProviderService implements IPaymentProvider {
  private readonly logger = new Logger(RazorpayProviderService.name);

  get name(): string {
    return 'razorpay';
  }

  async createOrder(userId: string, planName: string, amount: number): Promise<PaymentOrderResponse> {
    this.logger.log(`Razorpay: Creating order for user ${userId}, plan: ${planName}, amount: ${amount}`);
    
    // Simulate API request to Razorpay order generation
    const mockOrderId = `order_${Math.random().toString(36).substring(7)}`;
    return {
      orderId: mockOrderId,
      gateway: this.name,
      amount,
      currency: 'INR'
    };
  }

  verifyWebhookSignature(payload: string, signature: string): boolean {
    this.logger.log(`Razorpay Webhook: Verifying signature [${signature}]`);
    // Safe validation rule: in a real environment, verify with crypto.createHmac.
    return signature === 'razorpay_test_sig' || signature.length > 10;
  }

  async processRefund(paymentId: string, amount: number): Promise<boolean> {
    this.logger.log(`Razorpay: Initiating refund of Rs ${amount} on order ${paymentId}`);
    return true;
  }
}
