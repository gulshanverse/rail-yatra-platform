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

@Controller('api/conversations')
@UseGuards(JwtAuthGuard)
export class ConversationsController {
  constructor(private readonly prisma: PrismaService) {}

  @Get()
  async getConversations(@Req() req: AuthenticatedRequest) {
    return this.prisma.conversation.findMany({
      where: { userId: req.user.id },
      orderBy: { updatedAt: 'desc' },
      select: {
        id: true,
        summary: true,
        createdAt: true,
        updatedAt: true,
      },
    });
  }

  @Post()
  async createConversation(
    @Req() req: AuthenticatedRequest,
    @Body() body: { summary?: string },
  ) {
    return this.prisma.conversation.create({
      data: {
        userId: req.user.id,
        summary: body.summary || 'New Chat',
      },
    });
  }

  @Get(':id')
  async getConversationDetail(
    @Param('id') id: string,
    @Req() req: AuthenticatedRequest,
  ) {
    const conversation = await this.prisma.conversation.findUnique({
      where: { id },
      include: {
        messages: {
          orderBy: { timestamp: 'asc' },
        },
      },
    });

    if (!conversation) {
      throw new NotFoundException('Conversation not found');
    }

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
    const conversation = await this.prisma.conversation.findUnique({
      where: { id },
    });

    if (!conversation) {
      throw new NotFoundException('Conversation not found');
    }

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
    const conversation = await this.prisma.conversation.findUnique({
      where: { id },
    });

    if (!conversation) {
      throw new NotFoundException('Conversation not found');
    }

    if (conversation.userId !== req.user.id) {
      throw new UnauthorizedException('Access denied for this conversation');
    }

    await this.prisma.conversation.delete({
      where: { id },
    });

    return { success: true, message: 'Conversation deleted successfully.' };
  }

  @Post(':id/chat')
  async streamChat(
    @Param('id') id: string,
    @Req() req: AuthenticatedRequest,
    @Body() body: { message: string; context?: Record<string, unknown> },
    @Res() res: express.Response,
  ) {
    const conversation = await this.prisma.conversation.findUnique({
      where: { id },
    });

    if (!conversation) {
      throw new NotFoundException('Conversation not found');
    }

    if (conversation.userId !== req.user.id) {
      throw new UnauthorizedException('Access denied for this conversation');
    }

    // 1. Save user message to database
    await this.prisma.chatMessage.create({
      data: {
        conversationId: id,
        role: 'user',
        content: body.message,
      },
    });

    // 2. Call FastAPI streaming endpoint
    let fastapiResponse: Response;
    try {
      fastapiResponse = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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

    if (!fastapiResponse.body) {
      throw new InternalServerErrorException('AI stream body not returned');
    }

    // 3. Set headers for SSE stream proxying
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const reader = fastapiResponse.body.getReader();
    const decoder = new TextDecoder();
    let assistantReply = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        res.write(chunk);

        // Extract assistant reply from data chunks
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6)) as {
                type?: string;
                value?: string;
              };
              if (data.type === 'token' && typeof data.value === 'string') {
                assistantReply += data.value;
              }
            } catch {
              // Ignore partial JSON parsing failures
            }
          }
        }
      }
    } catch (streamError) {
      console.error('Error during streaming read:', streamError);
    }

    // 4. Save final full assistant response to the SQLite database
    if (assistantReply.trim()) {
      await this.prisma.chatMessage.create({
        data: {
          conversationId: id,
          role: 'assistant',
          content: assistantReply,
        },
      });

      // Update updatedAt timestamp of the conversation
      await this.prisma.conversation.update({
        where: { id },
        data: { updatedAt: new Date() },
      });
    }

    res.end();
  }
}
