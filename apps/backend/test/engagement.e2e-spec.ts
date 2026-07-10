import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import { AppModule } from '../src/app.module';
import { PrismaService } from '../src/prisma.service';
import { EngagementService } from '../src/engagement/engagement.service';
import { User } from '@prisma/client';

describe('Engagement Module (e2e)', () => {
  let app: INestApplication;
  let prisma: PrismaService;
  let engagementService: EngagementService;
  let mockUser: User;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();

    prisma = moduleFixture.get<PrismaService>(PrismaService);
    engagementService = moduleFixture.get<EngagementService>(EngagementService);

    // Seed test user
    const suffix = Math.random().toString(36).substring(4);
    mockUser = await prisma.user.create({
      data: {
        email: `engagement_${suffix}@test.com`,
        fullName: 'Engagement Test User',
        passwordHash: 'pass123',
        role: 'USER',
      },
    });
  });

  afterAll(async () => {
    if (mockUser) {
      await prisma.notification
        .deleteMany({ where: { userId: mockUser.id } })
        .catch(() => {});
      await prisma.notificationPreference
        .deleteMany({ where: { userId: mockUser.id } })
        .catch(() => {});
      await prisma.deliveryLog
        .deleteMany({ where: { userId: mockUser.id } })
        .catch(() => {});
      await prisma.engagementScore
        .deleteMany({ where: { userId: mockUser.id } })
        .catch(() => {});
      await prisma.user.delete({ where: { id: mockUser.id } }).catch(() => {});
    }
    await app.close();
  });

  it('should auto-initialize notification preferences with defaults', async () => {
    const prefs = await engagementService.getPreferences(mockUser.id);
    expect(prefs).toBeDefined();
    expect(prefs.emailAlerts).toBe(true);
    expect(prefs.smsAlerts).toBe(false);
    expect(prefs.pushAlerts).toBe(true);
  });

  it('should deduplicate repeat alerts triggered inside window', async () => {
    const title = 'Duplicate Test Alert';
    const msg = 'Checking spam prevention layer.';

    // Send first notification
    const res1 = await engagementService.dispatchNotification(
      mockUser.id,
      title,
      msg,
      'PNR',
      'high',
    );
    expect(res1).toBe(true);

    // Send second identical notification within the deduplication window
    const res2 = await engagementService.dispatchNotification(
      mockUser.id,
      title,
      msg,
      'PNR',
      'high',
    );
    expect(res2).toBe(false); // blocked by deduplication layer

    const dbCount = await prisma.notification.count({
      where: { userId: mockUser.id, title },
    });
    expect(dbCount).toBe(1); // Only the first one was saved
  });

  it('should increase user engagement score when reading alerts', async () => {
    await prisma.notification.create({
      data: {
        userId: mockUser.id,
        title: 'Score Booster Notif',
        message: 'Boost it.',
        category: 'System',
        priority: 'low',
        channel: 'push',
      },
    });

    const initScore = await prisma.engagementScore.findUnique({
      where: { userId: mockUser.id },
    });
    const startingScore = initScore ? initScore.score : 0;

    // Simulate reading via backend method
    const score = await engagementService.incrementEngagementScore(
      mockUser.id,
      5,
    );
    expect(score).toBe(startingScore + 5);
  });
});
