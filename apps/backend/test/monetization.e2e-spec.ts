import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { AppModule } from '../src/app.module';
import { PrismaService } from '../src/prisma.service';

describe('Monetization Module (e2e)', () => {
  let app: INestApplication;
  let prisma: PrismaService;
  let mockUser: any;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();

    prisma = moduleFixture.get<PrismaService>(PrismaService);

    // Create a mock user for testing billing integration
    const randomSuffix = Math.random().toString(36).substring(4);
    mockUser = await prisma.user.create({
      data: {
        email: `billing_${randomSuffix}@test.com`,
        fullName: 'Billing Test User',
        passwordHash: 'hashed_password_123',
        role: 'USER',
      },
    });
  });

  afterAll(async () => {
    if (mockUser) {
      await prisma.user.delete({ where: { id: mockUser.id } }).catch(() => {});
    }
    await app.close();
  });

  it('/api/monetization/plans (GET) should retrieve plan definitions', () => {
    return request(app.getHttpServer())
      .get('/api/monetization/plans')
      .expect(200)
      .expect((res) => {
        expect(res.body).toHaveProperty('FREE');
        expect(res.body).toHaveProperty('PREMIUM');
        expect(res.body.PREMIUM.price).toBe(299);
      });
  });

  it('/api/monetization/webhooks/stripe (POST) should process webhooks with signature checks', async () => {
    // Generate a payment order record first to map webhook
    await prisma.payment.delete({ where: { orderId: 'cs_test_webhook_order_123' } }).catch(() => {});
    const payment = await prisma.payment.create({
      data: {
        orderId: 'cs_test_webhook_order_123',
        userId: mockUser.id,
        gateway: 'stripe',
        amount: 299,
        status: 'pending',
      },
    });

    const webhookBody = {
      event: 'checkout.session.completed',
      id: 'cs_test_webhook_order_123',
    };

    await request(app.getHttpServer())
      .post('/api/monetization/webhooks/stripe')
      .set('x-webhook-signature', 'stripe_test_sig')
      .send(webhookBody)
      .expect(200);

    // Verify payment was marked completed and subscription was created
    const updatedPayment = await prisma.payment.findUnique({
      where: { id: payment.id },
    });
    expect(updatedPayment.status).toBe('completed');

    const sub = await prisma.subscription.findFirst({
      where: { userId: mockUser.id, tier: 'PREMIUM' },
    });
    expect(sub).toBeDefined();
    expect(sub.status).toBe('active');
    
    // Clean up payment and subscription
    await prisma.payment.delete({ where: { id: payment.id } }).catch(() => {});
    await prisma.subscription.deleteMany({ where: { userId: mockUser.id } }).catch(() => {});
  });
});
