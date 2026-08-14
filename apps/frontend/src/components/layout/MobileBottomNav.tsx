'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bot, Compass, Home, Map, Ticket } from 'lucide-react';
import { cn } from '@/lib/cn';

const ITEMS = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/chat', label: 'AI', icon: Bot },
  { href: '/plan', label: 'Plan', icon: Compass },
  { href: '/journeys', label: 'Journeys', icon: Map },
  { href: '/status', label: 'Status', icon: Ticket },
];

export function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-surface/95 px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur-xl md:hidden" aria-label="Mobile navigation">
      <div className="mx-auto flex max-w-md items-center justify-around">
        {ITEMS.map(({ href, label, icon: Icon }) => {
          const active = href === '/' ? pathname === '/' : pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'flex min-h-11 min-w-14 flex-col items-center justify-center gap-0.5 rounded-md px-2 text-[10px] font-medium',
                'transition-[color,background-color] duration-180',
                active ? 'text-primary' : 'text-muted-foreground hover:text-foreground',
              )}
            >
              <Icon className={cn('h-[18px] w-[18px]', active && 'stroke-[2.3]')} aria-hidden="true" />
              <span>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
