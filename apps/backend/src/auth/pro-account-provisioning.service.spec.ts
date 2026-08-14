import * as bcrypt from 'bcrypt';
import { ProAccountProvisioningService } from './pro-account-provisioning.service';

describe('ProAccountProvisioningService', () => {
  const prisma = {
    user: {
      findUnique: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
    },
    subscription: {
      update: jest.fn(),
      create: jest.fn(),
    },
  } as never;

  const service = new ProAccountProvisioningService(prisma);

  const originalEnv = process.env;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env = { ...originalEnv };
    process.env.ADMIN_PRO_UNLIMITED = 'true';
    process.env.ADMIN_EMAIL = 'admin@example.com';
    process.env.ADMIN_PASSWORD = 'a-strong-production-password';
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('creates an admin Premium Plus account when missing', async () => {
    (prisma.user.findUnique as jest.Mock).mockResolvedValue(null);
    (prisma.user.create as jest.Mock).mockResolvedValue({ id: 'admin-1' });

    await service.provisionFromEnvironment();

    expect(prisma.user.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
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
      }),
    );

    const passwordHash = (prisma.user.create as jest.Mock).mock.calls[0][0].data
      .passwordHash as string;
    await expect(bcrypt.compare('a-strong-production-password', passwordHash)).resolves.toBe(true);
  });

  it('is idempotent for an existing account and restores pro entitlements', async () => {
    (prisma.user.findUnique as jest.Mock).mockResolvedValue({
      id: 'admin-1',
      subscriptions: [{ id: 'sub-1' }],
    });

    await service.provisionFromEnvironment();

    expect(prisma.user.update).toHaveBeenCalledWith({
      where: { id: 'admin-1' },
      data: { role: 'ADMIN' },
    });
    expect(prisma.subscription.update).toHaveBeenCalledWith({
      where: { id: 'sub-1' },
      data: {
        tier: 'PREMIUM_PLUS',
        credits: 9999,
        status: 'active',
        expiry: null,
      },
    });
  });

  it('does nothing when provisioning is disabled', async () => {
    process.env.ADMIN_PRO_UNLIMITED = 'false';

    await service.provisionFromEnvironment();

    expect(prisma.user.findUnique).not.toHaveBeenCalled();
    expect(prisma.user.create).not.toHaveBeenCalled();
  });
});
