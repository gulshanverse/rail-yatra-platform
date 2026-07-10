import { Injectable, Logger } from '@nestjs/common';

export interface IDeliveryChannel {
  send(
    userId: string,
    target: string,
    title: string,
    message: string,
  ): Promise<boolean>;
}

@Injectable()
export class EmailChannelService implements IDeliveryChannel {
  private readonly logger = new Logger(EmailChannelService.name);

  send(
    userId: string,
    target: string,
    title: string,
    message: string,
  ): Promise<boolean> {
    this.logger.log(
      `[Email Dispatcher] Target: ${target} | Subject: ${title} | Body: ${message}`,
    );
    return Promise.resolve(true);
  }
}

@Injectable()
export class SmsChannelService implements IDeliveryChannel {
  private readonly logger = new Logger(SmsChannelService.name);

  send(
    userId: string,
    target: string,
    title: string,
    message: string,
  ): Promise<boolean> {
    this.logger.log(
      `[SMS Dispatcher] Target: ${target} | Text: ${title} - ${message}`,
    );
    return Promise.resolve(true);
  }
}

@Injectable()
export class PushChannelService implements IDeliveryChannel {
  private readonly logger = new Logger(PushChannelService.name);

  send(
    userId: string,
    target: string,
    title: string,
    message: string,
  ): Promise<boolean> {
    this.logger.log(
      `[Web Push Dispatcher] User: ${userId} | Notification: [${title}] ${message}`,
    );
    return Promise.resolve(true);
  }
}

@Injectable()
export class WhatsappChannelService implements IDeliveryChannel {
  private readonly logger = new Logger(WhatsappChannelService.name);

  send(
    userId: string,
    target: string,
    title: string,
    message: string,
  ): Promise<boolean> {
    this.logger.log(
      `[WhatsApp Dispatcher] Phone: ${target} | Message: ${title} - ${message}`,
    );
    return Promise.resolve(true);
  }
}
