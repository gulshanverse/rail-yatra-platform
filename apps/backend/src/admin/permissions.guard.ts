import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  SetMetadata,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { PlatformPermission, hasPermission } from './permissions.config';
import { AuthenticatedRequest } from '../common/interfaces';

export const PERMISSION_KEY = 'platform_permission';
export const RequirePermission = (permission: PlatformPermission) =>
  SetMetadata(PERMISSION_KEY, permission);

@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredPermission =
      this.reflector.getAllAndOverride<PlatformPermission>(PERMISSION_KEY, [
        context.getHandler(),
        context.getClass(),
      ]);

    if (!requiredPermission) {
      return true;
    }

    const request = context.switchToHttp().getRequest<AuthenticatedRequest>();
    const user = request.user;

    if (!user || !user.role) {
      throw new ForbiddenException('User session is missing or unauthorized.');
    }

    const isAuthorized = hasPermission(user.role, requiredPermission);
    if (!isAuthorized) {
      throw new ForbiddenException(
        `Access Denied: You do not possess the required permission: '${requiredPermission}'`,
      );
    }

    return true;
  }
}
