import * as React from 'react';
import { cn } from '@/lib/cn';

const variants = {
  neutral: 'border-border bg-muted text-muted-foreground',
  brand: 'border-primary/20 bg-primary/10 text-primary',
  ai: 'border-ai/20 bg-ai/10 text-ai',
  success: 'border-success/20 bg-success/10 text-success',
  warning: 'border-warning/20 bg-warning/10 text-warning',
  danger: 'border-danger/20 bg-danger/10 text-danger',
} as const;

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: keyof typeof variants;
}

export function Badge({ className, variant = 'neutral', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex min-h-7 items-center gap-1.5 rounded-full border px-2.5 text-xs font-medium leading-none',
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
