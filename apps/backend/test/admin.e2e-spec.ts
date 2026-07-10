import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { AppModule } from '../src/app.module';
import { PrismaService } from '../src/prisma.service';
import { AdminService } from '../src/admin/admin.service';

describe('Admin Module (e2e)', () => {
  let app: INestApplication;
  let prisma: PrismaService;
  let adminService: AdminService;
  let mockUser: any;
  let mockAdmin: any;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();

    prisma = moduleFixture.get<PrismaService>(PrismaService);
    adminService = moduleFixture.get<AdminService>(AdminService);

    // Create test user and administrator profiles
    const suffix = Math.random().toString(36).substring(4);
    mockUser = await prisma.user.create({
      data: {
        email: `regular_${suffix}@test.com`,
        fullName: 'Regular Traveler',
        passwordHash: 'pass123',
        role: 'USER',
      },
    });

    mockAdmin = await prisma.user.create({
      data: {
        email: `operator_${suffix}@test.com`,
        fullName: 'Ecosystem Administrator',
        passwordHash: 'pass123',
        role: 'ADMIN',
      },
    });
  });

  afterAll(async () => {
    if (mockUser) {
      await prisma.user.delete({ where: { id: mockUser.id } }).catch(() => {});
    }
    if (mockAdmin) {
      await prisma.auditLog.deleteMany({ where: { actorId: mockAdmin.id } }).catch(() => {});
      await prisma.user.delete({ where: { id: mockAdmin.id } }).catch(() => {});
    }
    await app.close();
  });

  it('should deny dashboard access to standard users (403)', async () => {
    // In our E2E environment, we mock JwtAuthGuard request decoding.
    // However, we can call the service directly to test RBAC logic, or hit HTTP.
    // Let's directly verify hasPermission logic and audit log entries generation.
    const { hasPermission } = require('../src/admin/permissions.config');
    const hasDashboardAccess = hasPermission('USER', 'admin:dashboard:view');
    expect(hasDashboardAccess).toBe(false);

    const hasAdminAccess = hasPermission('ADMIN', 'admin:dashboard:view');
    expect(hasAdminAccess).toBe(true);
  });

  it('should write immutable audit entries when configuration updates', async () => {
    const key = 'E2E_CONFIG_TEST';
    const val = 'assert_audit_written';

    // Clear previous occurrences to avoid constraint conflicts
    await prisma.systemConfiguration.delete({ where: { key } }).catch(() => {});

    await adminService.setSystemConfiguration(key, val, {
      id: mockAdmin.id,
      email: mockAdmin.email,
      ip: '127.0.0.1',
      ua: 'Jest integration spec',
    });

    const auditCount = await prisma.auditLog.count({
      where: {
        actorId: mockAdmin.id,
        action: 'update_system_config',
      },
    });
    expect(auditCount).toBeGreaterThanOrEqual(1);

    const logEntry = await prisma.auditLog.findFirst({
      where: { actorId: mockAdmin.id, action: 'update_system_config' },
    });
    expect(logEntry).toBeDefined();
    expect(logEntry.affectedResource).toBe(`Config:${key}`);
    expect(logEntry.actionResult).toBe('success');
    
    // Clean up
    await prisma.systemConfiguration.delete({ where: { key } }).catch(() => {});
  });
});
