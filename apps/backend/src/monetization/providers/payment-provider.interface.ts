export interface PaymentOrderResponse {
  orderId: string;
  gateway: string;
  amount: number;
  currency: string;
}

export interface IPaymentProvider {
  name: string;
  createOrder(userId: string, planName: string, amount: number): Promise<PaymentOrderResponse>;
  verifyWebhookSignature(payload: string, signature: string): boolean;
  processRefund(paymentId: string, amount: number): Promise<boolean>;
}
