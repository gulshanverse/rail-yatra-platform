import * as bcrypt from 'bcrypt';
import { PrismaService } from '../prisma.service';
import { ProAccountProvisioningService } from './pro-account-provisioning.service';

type ProvisioningPrismaMock = {
  user: {
    findUnique: (args: unknown) => Promise<unknown>;
    create: (args: unknown) => Promise<unknown>;
    update: (args: unknown) => Promise<unknown>;
  };
  subscription: {
    update: (args: unknown) => Promise<unknown>;
    create: (args: unknown) => Promise<unknown>;
  };
};

describe('ProAccountProvisioningService', () => {
  const originalEnv = process.env;
  let existingUser: unknown = null;
  let createdData: Record<string, unknown> | undefined;
  let userCreateCalls = 0;
  let userUpdateCalls = 0;
  let subscriptionUpdateCalls = 0;

  const prisma: ProvisioningPrismaMock = {
    user: {
      findUnique: async () => existingUser,
      create: async (args: unknown) => {
        userCreateCalls += 1;
        createdData = (args as { data: Record<string, unknown> }).data;
        return { id: 'admin-1' };
      },
      update: async () => {
        userUpdateCalls += 1;
        return { id: 'admin-1' };
      },
    },
    subscription: {
      update: async () => {
        subscriptionUpdateCalls += 1;
        return { id: 'sub-1' };
      },
      create: async () => ({ id: 'sub-1' }),
    },
  };

  const service = new ProAccountProvisioningService(
    prisma as unknown as PrismaService,
  );

  beforeEach(() => {
    process.env = { ...originalEnv };
    process.env.ADMIN_PRO_UNLIMITED = 'true';
    process.env.ADMIN_EMAIL = 'admin@example.com';
    process.env.ADMIN_PASSWORD = 'a-strong-production-password';
    existingUser = null;
    createdData = undefined;
    userCreateCalls = 0;
    userUpdateCalls = 0;
    subscriptionUpdateCalls = 0;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('creates an admin Premium Plus account when missing', async () => {
    await service.provisionFromEnvironment();

    expect(userCreateCalls).toBe(1);
    expect(createdData).toEqual(
      expect.objectContaining({
        email: 'admin@example.com',
        role: 'ADMIN',
        passwordHash: expect.any(String),
        subscriptions: {
          create: expect.objectContaining({
            tier: 'PREMIUM_PLUS',
            status: 'active',
            credits: 9999,
          }),
        },
      }),
    );

    const passwordHash = createdData?.passwordHash;
    expect(typeof passwordHash).toBe('string');
    if (typeof passwordHash !== 'string') return;

    await expect(
      bcrypt.compare('a-strong-production-password', passwordHash),
    ).resolves.toBe(true);
  });

  it('is idempotent for an existing account and restores pro entitlements', async () => {
    existingUser = {
      id: 'admin-1',
      subscriptions: [{ id: 'sub-1' }],
    };

    await service.provisionFromEnvironment();

    expect(userUpdateCalls).toBe(1);
    expect(subscriptionUpdateCalls).toBe(1);
    expect(userCreateCalls).toBe(0);
  });

  it('does nothing when provisioning is disabled', async () => {
    process.env.ADMIN_PRO_UNLIMITED = 'false';

    await service.provisionFromEnvironment();

    expect(userCreateCalls).toBe(0);
    expect(userUpdateCalls).toBe(0);
    expect(subscriptionUpdateCalls).toBe(0);
  });
});
