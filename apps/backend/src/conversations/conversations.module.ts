import { Module } from '@nestjs/common';
import { ConversationsController } from './conversations.controller';
import { PrismaService } from '../prisma.service';

@Module({
  controllers: [ConversationsController],
  providers: [PrismaService],
})
export class ConversationsModule {}
