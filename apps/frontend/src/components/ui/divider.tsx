import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export function Divider({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div role="separator" className={cn('h-px w-full bg-border', className)} {...props} />;
}
