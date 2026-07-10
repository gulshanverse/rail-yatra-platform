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
    return request(app.getHttpServer())
      .get('/api/health/live')
      .expect(200)
      .expect((res) => {
        expect(res.body.status).toBe('up');
        expect(res.body).toHaveProperty('timestamp');
      });
  });

  it('should return correlation-id in response headers', () => {
    return request(app.getHttpServer())
      .get('/api/health/live')
      .expect(200)
      .expect((res) => {
        expect(res.headers).toHaveProperty('x-correlation-id');
        expect(res.headers['x-correlation-id']).toContain('req_');
      });
  });

  it('should block requests exceeding client rate limits (429)', async () => {
    const server = app.getHttpServer();
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
