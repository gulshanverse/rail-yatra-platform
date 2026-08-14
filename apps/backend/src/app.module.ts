import { Module, NestModule, MiddlewareConsumer } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaService } from './prisma.service';
import { AuthModule } from './auth/auth.module';
import { ProAccountProvisioningService } from './auth/pro-account-provisioning.service';
import { ConversationsModule } from './conversations/conversations.module';
import { MonetizationModule } from './monetization/monetization.module';
import { EngagementModule } from './engagement/engagement.module';
import { AdminModule } from './admin/admin.module';
import { HealthModule } from './health/health.module';
import { MonitoringModule } from './monitoring/monitoring.module';
import { SecurityAndRateLimitMiddleware } from './common/security.middleware';
import { TraceMiddleware } from './monitoring/trace.middleware';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    MonitoringModule,
    AuthModule,
    ConversationsModule,
    MonetizationModule,
    EngagementModule,
    AdminModule,
    HealthModule,
  ],
  controllers: [AppController],
  providers: [AppService, PrismaService, ProAccountProvisioningService],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer
      .apply(TraceMiddleware, SecurityAndRateLimitMiddleware)
      .forRoutes('*');
  }
}
