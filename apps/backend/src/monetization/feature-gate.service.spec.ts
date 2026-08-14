import { PrismaService } from '../prisma.service';
import { FeatureGateService } from './feature-gate.service';

describe('FeatureGateService unlimited pro credits', () => {
  it('allows journey analysis forever for Premium Plus without decrementing credits', async () => {
    let subscriptionUpdates = 0;
    let usageLogs = 0;

    const prisma = {
      subscription: {
        findFirst: () =>
          Promise.resolve({
            id: 'sub-1',
            userId: 'user-1',
            tier: 'PREMIUM_PLUS',
            credits: 9999,
            status: 'active',
          }),
        update: () => {
          subscriptionUpdates += 1;
          return Promise.resolve({});
        },
      },
      usageLog: {
        create: () => {
          usageLogs += 1;
          return Promise.resolve({});
        },
      },
    };

    const service = new FeatureGateService(
      prisma as unknown as PrismaService,
    );

    await expect(
      service.enforceEntitlement('user-1', 'journey_analysis'),
    ).resolves.toBeUndefined();

    await service.logUsage('user-1', 'journey_analysis');

    expect(subscriptionUpdates).toBe(0);
    expect(usageLogs).toBe(1);
  });
});
