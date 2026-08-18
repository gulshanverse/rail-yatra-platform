import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  UseGuards,
  Req,
  Res,
  NotFoundException,
  UnauthorizedException,
  InternalServerErrorException,
} from '@nestjs/common';
import * as express from 'express';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { PrismaService } from '../prisma.service';
import type { AuthenticatedRequest } from '../common/interfaces';
import { formatSSEEvent, parseSSEBuffer } from '../common/sse';

@Controller('api/conversations')
@UseGuards(JwtAuthGuard)
export class ConversationsController {
  constructor(private readonly prisma: PrismaService) {}

  @Get()
  async getConversations(@Req() req: AuthenticatedRequest) {
    return this.prisma.conversation.findMany({
      where: { userId: req.user.id },
      orderBy: { updatedAt: 'desc' },
      select: { id: true, summary: true, createdAt: true, updatedAt: true },
    });
  }

  @Post()
  async createConversation(
    @Req() req: AuthenticatedRequest,
    @Body() body: { summary?: string },
  ) {
    return this.prisma.conversation.create({
      data: { userId: req.user.id, summary: body.summary || 'New Chat' },
    });
  }

  @Get(':id')
  async getConversationDetail(
    @Param('id') id: string,
    @Req() req: AuthenticatedRequest,
  ) {
    const conversation = await this.prisma.conversation.findUnique({
      where: { id },
      include: { messages: { orderBy: { timestamp: 'asc' } } },
    });

    if (!conversation) throw new NotFoundException('Conversation not found');
    if (conversation.userId !== req.user.id) {
      throw new UnauthorizedException('Access denied for this conversation');
    }
    return conversation;
  }

  @Patch(':id')
  async updateConversation(
    @Param('id') id: string,
    @Req() req: AuthenticatedRequest,
    @Body() body: { summary: string },
  ) {
    const conversation = await this.prisma.conversation.findUnique({ where: { id } });
    if (!conversation) throw new NotFoundException('Conversation not found');
    if (conversation.userId !== req.user.id) {
      throw new UnauthorizedException('Access denied for this conversation');
    }
    return this.prisma.conversation.update({
      where: { id },
      data: { summary: body.summary },
    });
  }

  @Delete(':id')
  async deleteConversation(
    @Param('id') id: string,
    @Req() req: AuthenticatedRequest,
  ) {
    const conversation = await this.prisma.conversation.findUnique({ where: { id } });
    if (!conversation) throw new NotFoundException('Conversation not found');
    if (conversation.userId !== req.user.id) {
      throw new UnauthorizedException('Access denied for this conversation');
    }
    await this.prisma.conversation.delete({ where: { id } });
    return { success: true, message: 'Conversation deleted successfully.' };
  }

  @Post(':id/chat')
  async streamChat(
    @Param('id') id: string,
    @Req() req: AuthenticatedRequest,
    @Body() body: { message: string; context?: Record<string, unknown> },
    @Res() res: express.Response,
  ) {
    const conversation = await this.prisma.conversation.findUnique({ where: { id } });
    if (!conversation) throw new NotFoundException('Conversation not found');
    if (conversation.userId !== req.user.id) {
      throw new UnauthorizedException('Access denied for this conversation');
    }

    const message = body.message?.trim();
    if (!message) {
      return res.status(400).json({
        statusCode: 400,
        code: 'EMPTY_MESSAGE',
        message: 'Message cannot be empty.',
      });
    }

    const aiServiceUrl = process.env.AI_SERVICE_URL?.trim().replace(/\/$/, '');
    if (!aiServiceUrl) {
      throw new InternalServerErrorException({
        code: 'AI_SERVICE_NOT_CONFIGURED',
        message: 'AI Core service is not configured on the backend deployment.',
      });
    }

    // The AI workflow itself has a 45s timeout. Keep the upstream fetch alive
    // longer than that so the backend does not abort a valid SSE response while
    // the AI service is still executing the workflow (especially after a cold start).
    const configuredTimeout = Number.parseInt(process.env.AI_SERVICE_TIMEOUT_MS ?? '65000', 10);
    const aiServiceTimeoutMs = Number.isFinite(configuredTimeout)
      ? Math.min(Math.max(configuredTimeout, 10000), 120000)
      : 65000;

    // Do not persist a user message until the upstream AI service has accepted
    // the request. This prevents failed requests from polluting conversation history.
    let fastapiResponse: Response;
    try {
      fastapiResponse = await fetch(`${aiServiceUrl}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(aiServiceTimeoutMs),
        body: JSON.stringify({
          message,
          conversation_id: id,
          user_id: req.user.id,
          context: body.context,
        }),
      });
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : String(e);
      console.error(`AI Core connection failed for conversation ${id}: ${errMsg}`);
      return res.status(502).json({
        statusCode: 502,
        code: 'AI_SERVICE_UNREACHABLE',
        message: 'RailYatra AI Core is unreachable. Please try again shortly.',
      });
    }

    if (!fastapiResponse.ok) {
      const upstreamText = await fastapiResponse.text().catch(() => 'Unknown upstream error');
      console.error(`AI Service returned ${fastapiResponse.status}: ${upstreamText}`);
      const clientStatus = fastapiResponse.status >= 500 ? 502 : fastapiResponse.status;
      return res.status(clientStatus).json({
        statusCode: clientStatus,
        code: fastapiResponse.status >= 500 ? 'AI_SERVICE_UPSTREAM_ERROR' : 'AI_REQUEST_REJECTED',
        message:
          fastapiResponse.status >= 500
            ? 'RailYatra AI Core failed while processing the request.'
            : 'RailYatra AI Core rejected the request.',
        upstreamStatus: fastapiResponse.status,
      });
    }

    if (!fastapiResponse.body) {
      return res.status(502).json({
        statusCode: 502,
        code: 'AI_STREAM_UNAVAILABLE',
        message: 'RailYatra AI Core did not return a stream.',
      });
    }

    await this.prisma.chatMessage.create({
      data: { conversationId: id, role: 'user', content: message },
    });

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache, no-transform');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no');

    const reader = fastapiResponse.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let assistantReply = '';
    let streamClosed = false;
    let sawError = false;

    const closeOnDisconnect = () => {
      if (!streamClosed) {
        streamClosed = true;
        void reader.cancel().catch(() => undefined);
      }
    };
    res.once('close', closeOnDisconnect);

    try {
      while (!streamClosed) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const [events, remainder] = parseSSEBuffer(buffer);
        buffer = remainder;

        for (const sseEvent of events) {
          try {
            const data = JSON.parse(sseEvent.data) as {
              type?: string;
              value?: string;
              reply?: string;
              message?: string;
              code?: string;
            };
            if (data.type === 'error') {
              sawError = true;
              console.error(
                `AI stream error conversation=${id} code=${data.code ?? 'UNKNOWN'} message=${data.message ?? 'unknown'}`,
              );
            } else if (data.type === 'token' && typeof data.value === 'string') {
              assistantReply += data.value;
            } else if (
              data.type === 'done' &&
              typeof data.reply === 'string' &&
              !assistantReply.trim()
            ) {
              assistantReply = data.reply;
            }
          } catch {
            console.warn('Ignoring malformed upstream SSE event');
          }
          res.write(formatSSEEvent(sseEvent));
        }
      }

      buffer += decoder.decode();
      const [finalEvents] = parseSSEBuffer(buffer);
      for (const sseEvent of finalEvents) {
        res.write(`data: ${sseEvent.data}\n\n`);
      }
    } catch (streamError) {
      if (!streamClosed) {
        sawError = true;
        console.error('Error during AI stream:', streamError);
        res.write(
          formatSSEEvent({
            event: 'error',
            data: JSON.stringify({
              type: 'error',
              code: 'AI_STREAM_READ_ERROR',
              message: 'The AI response stream ended unexpectedly.',
            }),
          }),
        );
      }
    } finally {
      res.off('close', closeOnDisconnect);
    }

    if (!streamClosed && !sawError && assistantReply.trim()) {
      await this.prisma.chatMessage.create({
        data: { conversationId: id, role: 'assistant', content: assistantReply },
      });
      await this.prisma.conversation.update({
        where: { id },
        data: { updatedAt: new Date() },
      });
    }

    if (!res.writableEnded) res.end();
  }
}
