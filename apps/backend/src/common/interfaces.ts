import { Request } from 'express';

export interface UserPayload {
  id: string;
  email: string;
  fullName: string;
  role: string;
}

export interface AuthenticatedRequest extends Request {
  user: UserPayload;
}

export interface WebhookPayload {
  event?: string;
  type?: string;
  orderId?: string;
  id?: string;
  data?: {
    object?: {
      id?: string;
    };
  };
}
