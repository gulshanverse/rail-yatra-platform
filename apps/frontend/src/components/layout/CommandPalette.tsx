'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Bot, Compass, Home, Map, Search, Ticket } from 'lucide-react';
import { cn } from '@/lib/cn';

const COMMANDS = [
  { href: '/', label: 'Home', description: 'Your RailYatra overview', icon: Home },
  { href: '/chat', label: 'AI Workspace', description: 'Talk to RailYatra AI', icon: Bot },
  { href: '/plan', label: 'Plan Journey', description: 'Build a new journey', icon: Compass },
  { href: '/journeys', label: 'My Journeys', description: 'Resume saved journeys', icon: Map },
  { href: '/status', label: 'PNR & Live Status', description: 'Check operational status', icon: Ticket },
];

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [selected, setSelected] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const results = React.useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return COMMANDS;
    return COMMANDS.filter((command) => `${command.label} ${command.description}`.toLowerCase().includes(normalized));
  }, [query]);

  const safeSelected = Math.min(selected, Math.max(results.length - 1, 0));

  React.useEffect(() => {
    const openPalette = () => {
      setQuery('');
      setSelected(0);
      setOpen(true);
      requestAnimationFrame(() => inputRef.current?.focus());
    };
    window.addEventListener('railyatra:command-palette', openPalette);
    return () => window.removeEventListener('railyatra:command-palette', openPalette);
  }, []);

  const navigate = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-start justify-center bg-black/45 px-4 pt-[12vh] backdrop-blur-sm" onMouseDown={() => setOpen(false)}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="RailYatra command palette"
        className="w-full max-w-xl overflow-hidden rounded-xl border border-border bg-surface shadow-elevated"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-border px-4">
          <Search className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          <input
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Escape') setOpen(false);
              if (event.key === 'ArrowDown') {
                event.preventDefault();
                setSelected((current) => Math.min(current + 1, Math.max(results.length - 1, 0)));
              }
              if (event.key === 'ArrowUp') {
                event.preventDefault();
                setSelected((current) => Math.max(current - 1, 0));
              }
              if (event.key === 'Enter' && results[safeSelected]) navigate(results[safeSelected].href);
            }}
            placeholder="Search RailYatra..."
            className="h-14 flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground"
          />
          <kbd className="hidden rounded border border-border bg-interactive px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:block">ESC</kbd>
        </div>

        <div className="max-h-[min(60vh,420px)] overflow-y-auto p-2">
          {results.length ? results.map(({ href, label, description, icon: Icon }, index) => (
            <button
              key={href}
              type="button"
              onClick={() => navigate(href)}
              onMouseEnter={() => setSelected(index)}
              className={cn(
                'flex min-h-14 w-full items-center gap-3 rounded-lg px-3 text-left',
                'transition-colors duration-120',
                safeSelected === index ? 'bg-interactive' : 'hover:bg-interactive',
              )}
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                <Icon className="h-[18px] w-[18px]" />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold">{label}</span>
                <span className="block truncate text-xs text-muted-foreground">{description}</span>
              </span>
            </button>
          )) : (
            <div className="px-4 py-10 text-center text-sm text-muted-foreground">No RailYatra destination found.</div>
          )}
        </div>

        <div className="hidden items-center gap-4 border-t border-border px-4 py-2 text-[10px] text-muted-foreground sm:flex">
          <span>↑↓ Navigate</span><span>↵ Open</span><span>Esc Close</span>
        </div>
      </div>
    </div>
  );
}
