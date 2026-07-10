export type PlatformPermission =
  | 'admin:dashboard:view'
  | 'admin:analytics:view'
  | 'admin:reports:export'
  | 'admin:audit:view'
  | 'admin:featureflags:update'
  | 'admin:system:configuration'
  | 'admin:users:manage'
  | 'admin:subscriptions:manage';

export const ROLE_PERMISSIONS: Record<string, PlatformPermission[]> = {
  SUPER_ADMIN: [
    'admin:dashboard:view',
    'admin:analytics:view',
    'admin:reports:export',
    'admin:audit:view',
    'admin:featureflags:update',
    'admin:system:configuration',
    'admin:users:manage',
    'admin:subscriptions:manage',
  ],
  ADMIN: [
    'admin:dashboard:view',
    'admin:analytics:view',
    'admin:reports:export',
    'admin:audit:view',
    'admin:featureflags:update',
    'admin:system:configuration',
    'admin:subscriptions:manage',
  ],
  OPERATIONS_MANAGER: [
    'admin:dashboard:view',
    'admin:system:configuration',
    'admin:subscriptions:manage',
  ],
  SUPPORT_MANAGER: ['admin:dashboard:view', 'admin:audit:view'],
  ANALYTICS_VIEWER: ['admin:dashboard:view', 'admin:analytics:view'],
};

export function hasPermission(
  role: string,
  permission: PlatformPermission,
): boolean {
  const normalizedRole = (role || '').toUpperCase();
  const permissions = ROLE_PERMISSIONS[normalizedRole];
  if (!permissions) return false;
  return permissions.includes(permission);
}
