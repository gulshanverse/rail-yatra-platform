import { INestApplication, ExecutionContext } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';
import { ConversationsController } from '../src/conversations/conversations.controller';
import { JwtAuthGuard } from '../src/auth/jwt-auth.guard';
import { PrismaService } from '../src/prisma.service';
import { parseSSEBuffer, formatSSEEvent } from '../src/common/sse';

describe('ConversationsController SSE (e2e)', () => {
  let app: INestApplication;
  const originalFetch = global.fetch;
  const prisma = {
    conversation: {
      findUnique: jest.fn(),
      update: jest.fn(),
    },
    chatMessage: {
      create: jest.fn(),
    },
  };

  beforeEach(async () => {
    jest.clearAllMocks();
    process.env.AI_SERVICE_URL = 'http://ai-service.test';
    prisma.conversation.findUnique.mockResolvedValue({ id: 'conversation-1', userId: 'user-1' });
    prisma.conversation.update.mockResolvedValue({});
    prisma.chatMessage.create.mockResolvedValue({});

    const module = await Test.createTestingModule({
      controllers: [ConversationsController],
      providers: [{ provide: PrismaService, useValue: prisma }],
    })
      .overrideGuard(JwtAuthGuard)
      .useValue({
        canActivate: (context: ExecutionContext) => {
          context.switchToHttp().getRequest().user = { id: 'user-1' };
          return true;
        },
      })
      .compile();

    app = module.createNestApplication();
    await app.init();
  });

  afterEach(async () => {
    global.fetch = originalFetch;
    delete process.env.AI_SERVICE_URL;
    await app.close();
  });

  it('forwards structured events losslessly and persists the completed assistant reply', async () => {
    const upstream = [
      formatSSEEvent({
        event: 'thinking',
        id: 'correlation-1:1',
        retry: 2500,
        data: JSON.stringify({ type: 'thinking', stage: 'understanding', state: 'active' }),
      }),
      formatSSEEvent({
        event: 'token',
        id: 'correlation-1:2',
        data: JSON.stringify({ type: 'token', value: 'hello ' }),
      }),
      formatSSEEvent({
        event: 'token',
        data: JSON.stringify({ type: 'token', value: 'world' }),
      }),
      formatSSEEvent({
        event: 'done',
        id: 'correlation-1:4',
        data: JSON.stringify({ type: 'done', reply: 'hello world', status: 'complete' }),
      }),
    ];
    global.fetch = jest.fn().mockResolvedValue(new Response(new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(upstream[0].slice(0, 17)));
        controller.enqueue(new TextEncoder().encode(upstream[0].slice(17) + upstream[1] + upstream[2] + upstream[3]));
        controller.close();
      },
    }), { status: 200, headers: { 'content-type': 'text/event-stream' } }));

    const response = await request(app.getHttpServer())
      .post('/api/conversations/conversation-1/chat')
      .send({ message: 'Find me a reliable train.' })
      .expect(200);

    let buffer = response.text;
    const [events, remainder] = parseSSEBuffer(buffer);
    buffer = remainder;

    expect(buffer).toBe('');
    expect(events.map((event) => event.event)).toEqual(['thinking', 'token', 'token', 'done']);
    expect(events[0]).toMatchObject({ id: 'correlation-1:1', retry: 2500 });
    expect(JSON.parse(events[1].data)).toMatchObject({ type: 'token', value: 'hello ' });
    expect(JSON.parse(events[3].data)).toMatchObject({ type: 'done', reply: 'hello world' });
    expect(prisma.chatMessage.create).toHaveBeenCalledWith({ data: { conversationId: 'conversation-1', role: 'user', content: 'Find me a reliable train.' } });
    expect(prisma.chatMessage.create).toHaveBeenCalledWith({ data: { conversationId: 'conversation-1', role: 'assistant', content: 'hello world' } });
  });

  it('keeps structured upstream errors visible and does not persist an incomplete assistant reply', async () => {
    const upstream = [
      formatSSEEvent({
        event: 'error',
        id: 'correlation-2:1',
        data: JSON.stringify({ type: 'error', code: 'AI_PROVIDER_TIMEOUT', message: 'Provider timed out.' }),
      }),
      formatSSEEvent({
        event: 'done',
        id: 'correlation-2:2',
        data: JSON.stringify({ type: 'done', status: 'error' }),
      }),
    ].join('');
    global.fetch = jest.fn().mockResolvedValue(new Response(upstream, { status: 200, headers: { 'content-type': 'text/event-stream' } }));

    const response = await request(app.getHttpServer())
      .post('/api/conversations/conversation-1/chat')
      .send({ message: 'Check my PNR.' })
      .expect(200);

    const [events] = parseSSEBuffer(response.text);
    expect(events.map((event) => event.event)).toEqual(['error', 'done']);
    expect(JSON.parse(events[0].data)).toMatchObject({ type: 'error', code: 'AI_PROVIDER_TIMEOUT' });
    expect(prisma.chatMessage.create).toHaveBeenCalledTimes(1);
    expect(prisma.chatMessage.create).toHaveBeenCalledWith({ data: { conversationId: 'conversation-1', role: 'user', content: 'Check my PNR.' } });
  });
});
