'use client';

import * as React from 'react';
import { cn } from '@/lib/cn';

export interface TabItem {
  value: string;
  label: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  items: TabItem[];
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function Tabs({ items, value, onValueChange, className: rootClassName }: TabsProps) {
  const tabRefs = React.useRef<Array<HTMLButtonElement | null>>([]);

  const moveFocus = (direction: 1 | -1) => {
    const current = items.findIndex((item) => item.value === value);
    let next = current;
    for (let i = 0; i < items.length; i += 1) {
      next = (next + direction + items.length) % items.length;
      if (!items[next]?.disabled) break;
    }
    const nextItem = items[next];
    if (nextItem && !nextItem.disabled) {
      onValueChange(nextItem.value);
      tabRefs.current[next]?.focus();
    }
  };

  return (
    <div className={cn('flex min-w-0 overflow-x-auto border-b border-border', rootClassName)} role="tablist">
      {items.map((item, index) => {
        const active = item.value === value;
        return (
          <button
            key={item.value}
            ref={(node) => { tabRefs.current[index] = node; }}
            type="button"
            role="tab"
            aria-selected={active}
            tabIndex={active ? 0 : -1}
            disabled={item.disabled}
            onClick={() => onValueChange(item.value)}
            onKeyDown={(event) => {
              if (event.key === 'ArrowRight') {
                event.preventDefault();
                moveFocus(1);
              } else if (event.key === 'ArrowLeft') {
                event.preventDefault();
                moveFocus(-1);
              } else if (event.key === 'Home') {
                event.preventDefault();
                const first = items.findIndex((entry) => !entry.disabled);
                if (first >= 0) {
                  onValueChange(items[first].value);
                  tabRefs.current[first]?.focus();
                }
              } else if (event.key === 'End') {
                event.preventDefault();
                const last = items.reduce((result, entry, i) => (!entry.disabled ? i : result), -1);
                if (last >= 0) {
                  onValueChange(items[last].value);
                  tabRefs.current[last]?.focus();
                }
              }
            }}
            className={cn(
              'relative min-h-11 shrink-0 px-3.5 text-sm font-medium text-muted-foreground transition-colors duration-180',
              'hover:text-foreground disabled:pointer-events-none disabled:opacity-40',
              'focus-visible:outline-none focus-visible:ring-0',
              active && 'text-foreground',
            )}
          >
            {item.label}
            <span
              aria-hidden="true"
              className={cn(
                'absolute inset-x-3 bottom-0 h-0.5 origin-center rounded-full bg-primary transition-transform duration-180',
                active ? 'scale-x-100' : 'scale-x-0',
              )}
            />
          </button>
        );
      })}
    </div>
  );
}
