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
import { parseSSEBuffer } from '../common/sse';

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

    await this.prisma.chatMessage.create({
      data: { conversationId: id, role: 'user', content: body.message },
    });

    const aiServiceUrl = process.env.AI_SERVICE_URL?.trim();
    if (!aiServiceUrl) {
      throw new InternalServerErrorException(
        'AI Core service is not configured. Set AI_SERVICE_URL on the backend deployment.',
      );
    }

    let fastapiResponse: Response;
    try {
      fastapiResponse = await fetch(`${aiServiceUrl.replace(/\/$/, '')}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: body.message,
          conversation_id: id,
          user_id: req.user.id,
          context: body.context,
        }),
      });
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : String(e);
      throw new InternalServerErrorException(
        `AI Core service is currently offline or unreachable: ${errMsg}`,
      );
    }

    if (!fastapiResponse.ok) {
      const errorText = await fastapiResponse.text().catch(() => 'Unknown upstream error');
      console.error(`AI Service returned error ${fastapiResponse.status}: ${errorText}`);
      res.status(fastapiResponse.status).json({
        statusCode: fastapiResponse.status,
        message: `AI Service error (${fastapiResponse.status}): ${errorText}`,
        error: fastapiResponse.status >= 500 ? 'Bad Gateway' : 'Bad Request',
      });
      return;
    }

    if (!fastapiResponse.body) {
      throw new InternalServerErrorException('AI stream body not returned');
    }

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache, no-transform');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no');

    const reader = fastapiResponse.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let assistantReply = '';
    let streamClosed = false;

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
          res.write(`data: ${sseEvent.data}\n\n`);

          try {
            const data = JSON.parse(sseEvent.data) as {
              type?: string;
              value?: string;
              reply?: string;
            };
            if (data.type === 'token' && typeof data.value === 'string') {
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
        }
      }

      buffer += decoder.decode();
    } catch (streamError) {
      if (!streamClosed) console.error('Error during streaming read:', streamError);
    } finally {
      res.off('close', closeOnDisconnect);
    }

    if (!streamClosed && assistantReply.trim()) {
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
