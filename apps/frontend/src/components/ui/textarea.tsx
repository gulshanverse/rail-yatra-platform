'use client';

import * as React from 'react';
import { cn } from '@/lib/cn';

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'min-h-24 w-full resize-y rounded-lg border border-input bg-surface px-3.5 py-3 text-base leading-6 text-foreground placeholder:text-muted-foreground',
        'outline-none transition-[border-color,box-shadow,background-color] duration-180',
        'focus:border-ring focus:ring-2 focus:ring-ring/20',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'aria-[invalid=true]:border-danger aria-[invalid=true]:ring-danger/20',
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = 'Textarea';
