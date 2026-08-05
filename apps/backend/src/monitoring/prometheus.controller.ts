import { Controller, Get, Res, HttpStatus } from '@nestjs/common';
import type { Response } from 'express';
import { MetricsService } from './metrics.service';

@Controller()
export class PrometheusController {
  constructor(private readonly metricsService: MetricsService) {}

  @Get('metrics')
  getMetrics(@Res() res: Response) {
    const metricsData = this.metricsService.getPrometheusMetrics();
    res.setHeader('Content-Type', 'text/plain; version=0.0.4; charset=utf-8');
    return res.status(HttpStatus.OK).send(metricsData);
  }

  @Get('api/metrics')
  getApiMetrics(@Res() res: Response) {
    const metricsData = this.metricsService.getPrometheusMetrics();
    res.setHeader('Content-Type', 'text/plain; version=0.0.4; charset=utf-8');
    return res.status(HttpStatus.OK).send(metricsData);
  }
}
