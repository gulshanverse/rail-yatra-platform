'use client';

import * as React from 'react';
import { cn } from '@/lib/cn';

const variants = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/90 shadow-sm',
  outline: 'border border-border bg-transparent hover:bg-interactive text-foreground',
  ghost: 'bg-transparent hover:bg-interactive text-foreground',
  subtle: 'bg-surface text-foreground hover:bg-interactive border border-border/70',
  danger: 'bg-danger text-white hover:bg-danger/90 shadow-sm',
} as const;

const sizes = {
  sm: 'h-9 rounded-md px-3 text-sm',
  md: 'h-11 rounded-md px-4 text-sm',
  lg: 'h-12 rounded-lg px-5 text-[15px]',
  icon: 'h-11 w-11 rounded-md p-0',
} as const;

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', type = 'button', ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(
        'inline-flex min-h-11 items-center justify-center gap-2 whitespace-nowrap font-medium',
        'transition-[background-color,border-color,color,box-shadow,transform,opacity] duration-200 ease-out',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        'disabled:pointer-events-none disabled:opacity-50 active:translate-y-px',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = 'Button';
