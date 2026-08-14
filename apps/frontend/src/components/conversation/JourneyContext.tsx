'use client';

import * as React from 'react';
import { ChevronDown, MapPin, Users, CalendarDays, Armchair } from 'lucide-react';

export interface JourneyContextData {
  origin?: string | null;
  destination?: string | null;
  date?: string | null;
  passengers?: number | null;
  className?: string | null;
}

interface JourneyContextProps {
  context: JourneyContextData;
  defaultOpen?: boolean;
}

const Field = ({ label, value, icon: Icon }: { label: string; value?: string | null; icon: React.ElementType }) => (
  <div className="flex min-w-0 items-start gap-2.5 rounded-lg border border-border/60 bg-background/60 p-2.5">
    <Icon aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
    <div className="min-w-0">
      <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="truncate text-xs font-medium text-foreground">{value || 'Not specified'}</p>
    </div>
  </div>
);

export function JourneyContext({ context, defaultOpen = false }: JourneyContextProps) {
  const [open, setOpen] = React.useState(defaultOpen);
  const routeKnown = Boolean(context.origin || context.destination);
  const routeLabel = context.origin && context.destination
    ? `${context.origin} → ${context.destination}`
    : context.origin || context.destination || 'Journey details not specified';

  return (
    <section className="border-b border-border/70 bg-background/70 px-4 py-2.5 backdrop-blur-sm" aria-label="Journey context">
      <button
        type="button"
        aria-expanded={open}
        aria-controls="journey-context-details"
        onClick={() => setOpen((value) => !value)}
        className="flex min-h-10 w-full items-center justify-between gap-3 rounded-lg px-1 text-left outline-none transition-colors hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring"
      >
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
            <MapPin aria-hidden="true" className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Journey context</p>
            <p className="truncate text-sm font-semibold text-foreground">{routeLabel}</p>
          </div>
        </div>
        <ChevronDown aria-hidden="true" className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div id="journey-context-details" className="grid gap-2 pb-1 pt-2 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Origin" value={context.origin} icon={MapPin} />
          <Field label="Destination" value={context.destination} icon={MapPin} />
          <Field label="Date" value={context.date} icon={CalendarDays} />
          <Field label="Passengers" value={context.passengers ? String(context.passengers) : null} icon={Users} />
          <Field label="Class" value={context.className} icon={Armchair} />
          {!routeKnown && (
            <p className="sm:col-span-2 lg:col-span-4 px-2 text-[11px] text-muted-foreground">
              Add journey details in your message to build a personalized travel context. RailYatra will not assume missing details.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
