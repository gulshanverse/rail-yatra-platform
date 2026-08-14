import { FeatureGateService } from './feature-gate.service';

describe('FeatureGateService unlimited pro credits', () => {
  it('allows journey analysis forever for Premium Plus without decrementing credits', async () => {
    const prisma = {
      subscription: {
        findFirst: jest.fn().mockResolvedValue({
          id: 'sub-1',
          userId: 'user-1',
          tier: 'PREMIUM_PLUS',
          credits: 9999,
          status: 'active',
        }),
        update: jest.fn(),
      },
      usageLog: {
        create: jest.fn(),
      },
    } as never;

    const service = new FeatureGateService(prisma);

    await expect(
      service.enforceEntitlement('user-1', 'journey_analysis'),
    ).resolves.toBeUndefined();

    await service.logUsage('user-1', 'journey_analysis');

    expect(prisma.subscription.update).not.toHaveBeenCalled();
    expect(prisma.usageLog.create).toHaveBeenCalledWith({
      data: { userId: 'user-1', action: 'journey_analysis' },
    });
  });
});
