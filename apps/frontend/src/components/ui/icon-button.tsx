'use client';

import * as React from 'react';
import { cn } from '@/lib/cn';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  variant?: 'default' | 'ghost';
}

const sizes = {
  sm: 'h-9 w-9 rounded-md',
  md: 'h-11 w-11 rounded-md',
  lg: 'h-12 w-12 rounded-lg',
} as const;

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, size = 'md', type = 'button', label, variant = 'default', ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      aria-label={props['aria-label'] ?? label}
      className={cn(
        'inline-flex shrink-0 items-center justify-center text-foreground',
        'border border-transparent transition-[background-color,border-color,color,transform,opacity] duration-180 ease-out',
        'hover:border-border hover:bg-interactive',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        'disabled:pointer-events-none disabled:opacity-50 active:translate-y-px',
        variant === 'ghost' && 'bg-transparent',
        sizes[size],
        className,
      )}
      {...props}
    />
  ),
);
IconButton.displayName = 'IconButton';
