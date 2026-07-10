import { Module } from '@nestjs/common';
import { EngagementController } from './engagement.controller';
import { EngagementService } from './engagement.service';
import { ReminderSchedulerService } from './scheduler.service';
import {
  EmailChannelService,
  SmsChannelService,
  PushChannelService,
  WhatsappChannelService,
} from './channels';
import { PrismaService } from '../prisma.service';

@Module({
  controllers: [EngagementController],
  providers: [
    EngagementService,
    ReminderSchedulerService,
    EmailChannelService,
    SmsChannelService,
    PushChannelService,
    WhatsappChannelService,
    PrismaService,
  ],
  exports: [EngagementService, ReminderSchedulerService],
})
export class EngagementModule {}
