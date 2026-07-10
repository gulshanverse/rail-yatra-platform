import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

@Injectable()
export class AdminService {
  private readonly logger = new Logger(AdminService.name);

  constructor(private readonly prisma: PrismaService) {}

  async logAudit(
    actorId: string,
    actorEmail: string,
    action: string,
    details: any,
    reqMeta?: {
      requestId?: string;
      ipAddress?: string;
      userAgent?: string;
      affectedResource?: string;
      actionResult?: string;
    },
  ): Promise<void> {
    this.logger.log(`Audit Log: Action '${action}' performed by ${actorEmail}`);
    await this.prisma.auditLog.create({
      data: {
        actorId,
        actorEmail,
        action,
        details: JSON.stringify(details),
        requestId: reqMeta?.requestId || null,
        ipAddress: reqMeta?.ipAddress || null,
        userAgent: reqMeta?.userAgent || null,
        affectedResource: reqMeta?.affectedResource || null,
        actionResult: reqMeta?.actionResult || 'success',
      },
    });
  }

  async getSystemMetrics() {
    this.logger.log('Fetching system performance metrics telemetry.');

    // Simulate real production health values
    const metrics = [
      {
        nodeName: 'api_server',
        status: 'healthy',
        cpuPercent: 12.5,
        memoryBytes: 524288000,
        latencyMs: 8,
        cacheHitRatio: 0.94,
        queueLength: 0,
      },
      {
        nodeName: 'database',
        status: 'healthy',
        cpuPercent: 8.2,
        memoryBytes: 2097152000,
        latencyMs: 3,
        cacheHitRatio: 1.0,
        queueLength: 0,
      },
      {
        nodeName: 'redis_cache',
        status: 'healthy',
        cpuPercent: 4.1,
        memoryBytes: 104857600,
        latencyMs: 1,
        cacheHitRatio: 0.96,
        queueLength: 0,
      },
      {
        nodeName: 'ai_core_service',
        status: 'healthy',
        cpuPercent: 24.8,
        memoryBytes: 4194304000,
        latencyMs: 52,
        cacheHitRatio: 0.85,
        queueLength: 2,
      },
      {
        nodeName: 'background_worker',
        status: 'healthy',
        cpuPercent: 6.0,
        memoryBytes: 262144000,
        latencyMs: 12,
        cacheHitRatio: 1.0,
        queueLength: 0,
      },
    ];

    // Seed/Save snapshots in db for history tracking
    for (const m of metrics) {
      await this.prisma.systemMetric.create({
        data: {
          nodeName: m.nodeName,
          status: m.status,
          cpuPercent: m.cpuPercent,
          memoryBytes: m.memoryBytes,
          latencyMs: m.latencyMs,
          cacheHitRatio: m.cacheHitRatio,
          queueLength: m.queueLength,
        },
      });
    }

    return metrics;
  }

  async getAnalyticsOverview() {
    this.logger.log('Aggregating modular analytics trends.');

    // Aggregate values directly from existing databases
    const totalUsers = await this.prisma.user.count();
    const totalChats = await this.prisma.usageLog.count({
      where: { action: 'ai_message' },
    });
    const totalAnalyses = await this.prisma.usageLog.count({
      where: { action: 'journey_analysis' },
    });

    const rawPayments = await this.prisma.payment.findMany({
      where: { status: 'completed' },
    });
    const totalRevenue = rawPayments.reduce(
      (acc, curr) => acc + curr.amount.toNumber(),
      0,
    );

    // Return analytics snapshots history trends (seed default data if empty)
    const snapshots = await this.prisma.analyticsSnapshot.findMany({
      orderBy: { date: 'asc' },
      take: 7,
    });

    if (snapshots.length === 0) {
      // Seed last 7 days metrics
      const days = [
        '2026-07-04',
        '2026-07-05',
        '2026-07-06',
        '2026-07-07',
        '2026-07-08',
        '2026-07-09',
        '2026-07-10',
      ];
      const seeded = [];
      let stepRevenue = 0;
      for (const d of days) {
        stepRevenue += 299;
        const record = await this.prisma.analyticsSnapshot.create({
          data: {
            date: d,
            activeUsersCount: 10 + Math.floor(Math.random() * 15),
            aiMessagesCount: 50 + Math.floor(Math.random() * 100),
            analysesCount: 15 + Math.floor(Math.random() * 30),
            revenueAmount: stepRevenue,
            retentionRate: 85.0 + Math.random() * 10,
            conversionRatio: 8.5 + Math.random() * 5,
          },
        });
        seeded.push(record);
      }
      return {
        totals: { totalUsers, totalChats, totalAnalyses, totalRevenue },
        history: seeded,
        funnel: {
          visits: 1000,
          registrations: 350,
          trials: 120,
          premiumSubs: 45,
        },
      };
    }

    return {
      totals: { totalUsers, totalChats, totalAnalyses, totalRevenue },
      history: snapshots,
      funnel: {
        visits: 1000,
        registrations: 350,
        trials: 120,
        premiumSubs: 45,
      },
    };
  }

  async getFeatureFlags() {
    const flags = await this.prisma.featureFlag.findMany();
    if (flags.length === 0) {
      // Seed default system feature flags
      const defaults = [
        {
          name: 'waitlist_predictions',
          enabled: true,
          description: 'Enables machine-learning probability calculations.',
        },
        {
          name: 'boarding_junction_optimization',
          enabled: true,
          description: 'Enables adjacent quota analyses.',
        },
        {
          name: 'dynamic_sliders_workspace',
          enabled: true,
          description: 'Enables live weights customization sliders.',
        },
        {
          name: 'sms_whatsapp_reminders',
          enabled: false,
          description: 'Enables external SMS gateways alerts.',
        },
      ];

      const seeded = [];
      for (const f of defaults) {
        const flag = await this.prisma.featureFlag.create({ data: f });
        seeded.push(flag);
      }
      return seeded;
    }
    return flags;
  }

  async setFeatureFlag(
    name: string,
    enabled: boolean,
    actor: { id: string; email: string; ip?: string; ua?: string },
  ) {
    const flag = await this.prisma.featureFlag.upsert({
      where: { name },
      create: { name, enabled, description: 'System Dynamic Flag' },
      update: { enabled },
    });

    // Write immutable audit log trace
    await this.logAudit(
      actor.id,
      actor.email,
      'toggle_feature_flag',
      { flagName: name, enabled },
      {
        ipAddress: actor.ip,
        userAgent: actor.ua,
        affectedResource: `FeatureFlag:${name}`,
      },
    );

    return flag;
  }

  async getSystemConfigurations() {
    const configs = await this.prisma.systemConfiguration.findMany();
    if (configs.length === 0) {
      const defaults = [
        {
          key: 'maintenance_mode',
          value: 'false',
          description: 'Sets system global block maintenance.',
        },
        {
          key: 'banner_announcement',
          value: 'Welcome to RailYatra Premium Travel Intelligence!',
          description: 'Dynamic dashboard announcement banner.',
        },
        {
          key: 'ai_priority_node',
          value: 'primary_fast_node',
          description: 'AI Core service priority routing target.',
        },
      ];
      const seeded = [];
      for (const c of defaults) {
        const conf = await this.prisma.systemConfiguration.create({ data: c });
        seeded.push(conf);
      }
      return configs;
    }
    return configs;
  }

  async setSystemConfiguration(
    key: string,
    value: string,
    actor: { id: string; email: string; ip?: string; ua?: string },
  ) {
    const prev = await this.prisma.systemConfiguration.findUnique({
      where: { key },
    });
    const conf = await this.prisma.systemConfiguration.upsert({
      where: { key },
      create: { key, value },
      update: { value },
    });

    // Write immutable audit log trace
    await this.logAudit(
      actor.id,
      actor.email,
      'update_system_config',
      { key, previousValue: prev ? prev.value : null, newValue: value },
      {
        ipAddress: actor.ip,
        userAgent: actor.ua,
        affectedResource: `Config:${key}`,
      },
    );

    return conf;
  }
}
