'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bot, ChevronLeft, ChevronRight, Compass, Home, Map, Menu, Search, Settings, Ticket, X } from 'lucide-react';
import { cn } from '@/lib/cn';
import { IconButton } from '@/components/ui/icon-button';
import { Avatar } from '@/components/ui/avatar';
import { useAuthStore } from '@/store/authStore';

const NAV_ITEMS = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/chat', label: 'AI Workspace', icon: Bot },
  { href: '/plan', label: 'Plan Journey', icon: Compass },
  { href: '/journeys', label: 'My Journeys', icon: Map },
  { href: '/status', label: 'PNR & Live Status', icon: Ticket },
];

const SECONDARY_ITEMS = [
  { href: '/settings', label: 'Settings', icon: Settings },
];

function isActive(pathname: string, href: string) {
  if (href === '/') return pathname === '/';
  return pathname === href || pathname.startsWith(`${href}/`);
}

export interface AppShellProps {
  children: React.ReactNode;
  title?: string;
  showSidebar?: boolean;
}

export function AppShell({ children, title, showSidebar = true }: AppShellProps) {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);

  React.useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  React.useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        window.dispatchEvent(new CustomEvent('railyatra:command-palette'));
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  if (!showSidebar) return <>{children}</>;

  const renderNav = (items: typeof NAV_ITEMS) => (
    <nav className="space-y-1" aria-label="Primary navigation">
      {items.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? 'page' : undefined}
            title={collapsed ? label : undefined}
            className={cn(
              'group flex min-h-11 items-center gap-3 rounded-md px-3 text-sm font-medium',
              'transition-[background-color,color,transform] duration-180',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30',
              active
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-interactive hover:text-foreground',
              collapsed && 'justify-center px-0',
            )}
          >
            <Icon className={cn('h-[18px] w-[18px] shrink-0', active && 'stroke-[2.2]')} aria-hidden="true" />
            {!collapsed && <span className="truncate">{label}</span>}
          </Link>
        );
      })}
    </nav>
  );

  const sidebar = (
    <aside
      className={cn(
        'flex h-full flex-col border-r border-border bg-surface',
        'transition-[width,transform] duration-240 ease-premium',
        collapsed ? 'w-[76px]' : 'w-[248px]',
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-border px-4">
        <Link href="/" className={cn('flex min-w-0 items-center gap-2.5', collapsed && 'justify-center w-full')} aria-label="RailYatra home">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-card">
            <span className="text-sm font-bold">R</span>
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="truncate text-sm font-bold tracking-tight">RailYatra</div>
              <div className="truncate text-[10px] text-muted-foreground">AI travel intelligence</div>
            </div>
          )}
        </Link>
        {!collapsed && (
          <IconButton label="Collapse navigation" size="sm" variant="ghost" onClick={() => setCollapsed(true)}>
            <ChevronLeft className="h-4 w-4" />
          </IconButton>
        )}
      </div>

      {collapsed && (
        <div className="flex justify-center py-3">
          <IconButton label="Expand navigation" size="sm" variant="ghost" onClick={() => setCollapsed(false)}>
            <ChevronRight className="h-4 w-4" />
          </IconButton>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-3 py-5">
        {!collapsed && <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">Workspace</p>}
        {renderNav(NAV_ITEMS)}
        <div className="my-5 h-px bg-border" />
        {!collapsed && <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-muted-foreground">Account</p>}
        {renderNav(SECONDARY_ITEMS)}
      </div>

      <div className="border-t border-border p-3">
        <Link href="/settings" className={cn('flex min-h-11 items-center gap-3 rounded-md p-2 hover:bg-interactive', collapsed && 'justify-center')}>
          <Avatar fallback={user?.fullName || user?.email || 'RY'} className="h-8 w-8" />
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold">{user?.fullName || 'RailYatra user'}</p>
              <p className="truncate text-[11px] text-muted-foreground">{user?.email || 'Account'}</p>
            </div>
          )}
        </Link>
      </div>
    </aside>
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="fixed inset-y-0 left-0 z-40 hidden md:block">{sidebar}</div>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button className="absolute inset-0 bg-black/50" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />
          <div className="relative h-full w-[min(86vw,320px)] shadow-elevated">{sidebar}</div>
        </div>
      )}

      <div className={cn('min-h-screen transition-[padding-left] duration-240 ease-premium', collapsed ? 'md:pl-[76px]' : 'md:pl-[248px]')}>
        <header className="sticky top-0 z-30 flex h-16 items-center border-b border-border bg-background/90 px-4 backdrop-blur-md md:px-6">
          <IconButton className="mr-3 md:hidden" label="Open navigation" variant="ghost" onClick={() => setMobileOpen(true)}>
            <Menu className="h-5 w-5" />
          </IconButton>
          <div className="min-w-0 flex-1">
            {title ? <h1 className="truncate text-sm font-semibold md:text-base">{title}</h1> : <span className="sr-only">RailYatra</span>}
          </div>
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('railyatra:command-palette'))}
            className="hidden h-9 items-center gap-2 rounded-md border border-border bg-surface px-3 text-xs text-muted-foreground hover:text-foreground sm:flex"
          >
            <Search className="h-3.5 w-3.5" />
            <span>Search</span>
            <kbd className="rounded border border-border bg-interactive px-1.5 py-0.5 font-mono text-[10px]">⌘K</kbd>
          </button>
          <div className="ml-3 md:hidden">
            <IconButton label="Close navigation" variant="ghost" onClick={() => setMobileOpen(false)} className="hidden">
              <X className="h-5 w-5" />
            </IconButton>
          </div>
        </header>

        <main className="mx-auto min-h-[calc(100vh-4rem)] w-full max-w-[1600px] px-4 py-5 md:px-6 md:py-7 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
