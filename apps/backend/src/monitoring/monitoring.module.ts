import { Module, Global } from '@nestjs/common';
import { MetricsService } from './metrics.service';
import { SentryService } from './sentry.service';
import { PrometheusController } from './prometheus.controller';

@Global()
@Module({
  controllers: [PrometheusController],
  providers: [MetricsService, SentryService],
  exports: [MetricsService, SentryService],
})
export class MonitoringModule {}
