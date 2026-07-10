import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { AppModule } from '../src/app.module';

describe('Production Hardening Module (e2e)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('/api/health/live (GET) should report server status up', () => {
    return request(app.getHttpServer() as import('http').Server)
      .get('/api/health/live')
      .expect(200)
      .expect((res: request.Response) => {
        const body = res.body as { status: string; timestamp: string };
        expect(body.status).toBe('up');
        expect(body).toHaveProperty('timestamp');
      });
  });

  it('should return correlation-id in response headers', () => {
    return request(app.getHttpServer() as import('http').Server)
      .get('/api/health/live')
      .expect(200)
      .expect((res: request.Response) => {
        expect(res.headers).toHaveProperty('x-correlation-id');
        const headers = res.headers as Record<string, string>;
        expect(headers['x-correlation-id']).toContain('req_');
      });
  });

  it('should block requests exceeding client rate limits (429)', async () => {
    const server = app.getHttpServer() as import('http').Server;
    let limitBreached = false;

    for (let i = 0; i < 165; i++) {
      const res = await request(server).get('/api/health/live');
      if (res.status === 429) {
        limitBreached = true;
        break;
      }
    }

    expect(limitBreached).toBe(true);
  });
});
