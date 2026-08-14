'use client';

import * as React from 'react';
import { AppShell } from './AppShell';

export interface AuthenticatedShellProps {
  children: React.ReactNode;
  title?: string;
}

export function AuthenticatedShell({ children, title }: AuthenticatedShellProps) {
  return <AppShell title={title}>{children}</AppShell>;
}
