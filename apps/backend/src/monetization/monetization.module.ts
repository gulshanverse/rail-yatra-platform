import { Module } from '@nestjs/common';
import { MonetizationController } from './monetization.controller';
import { MonetizationService } from './monetization.service';
import { FeatureGateService } from './feature-gate.service';
import { StripeProviderService } from './providers/stripe-provider.service';
import { RazorpayProviderService } from './providers/razorpay-provider.service';
import { PrismaService } from '../prisma.service';

@Module({
  controllers: [MonetizationController],
  providers: [
    MonetizationService,
    FeatureGateService,
    StripeProviderService,
    RazorpayProviderService,
    PrismaService,
  ],
  exports: [FeatureGateService],
})
export class MonetizationModule {}
