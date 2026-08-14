'use client';

import { MapPin, Pencil, Users, X } from 'lucide-react';
import { useState } from 'react';

export interface JourneyContext {
  origin?: string | null;
  destination?: string | null;
  date?: string | null;
  passengers?: number | null;
  travelClass?: string | null;
}

interface JourneyContextCardProps {
  context: JourneyContext;
  onSave?: (context: JourneyContext) => void;
}

const valueOrUnknown = (value?: string | number | null) => value ?? 'Not specified';

export function JourneyContextCard({ context, onSave }: JourneyContextCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<JourneyContext>(context);

  const save = () => {
    onSave?.(draft);
    setEditing(false);
    setExpanded(true);
  };

  return (
    <section className="rounded-2xl border border-border/70 bg-card/70 p-3 shadow-sm" aria-label="Journey context">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 text-left"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
      >
        <span className="flex min-w-0 items-center gap-2">
          <span className="grid size-8 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary" aria-hidden="true">
            <MapPin className="size-4" />
          </span>
          <span className="min-w-0">
            <span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">Journey context</span>
            <span className="block truncate text-sm font-semibold">
              {valueOrUnknown(context.origin)} → {valueOrUnknown(context.destination)}
            </span>
          </span>
        </span>
        <span className="text-xs text-muted-foreground">{expanded ? 'Hide' : 'Details'}</span>
      </button>

      {expanded && !editing && (
        <div className="mt-3 grid gap-2 border-t border-border/60 pt-3 sm:grid-cols-2">
          <ContextValue label="Date" value={context.date} />
          <ContextValue label="Passengers" value={context.passengers} icon={<Users className="size-3.5" />} />
          <ContextValue label="Class" value={context.travelClass} />
          <button
            type="button"
            onClick={() => {
              setDraft(context);
              setEditing(true);
            }}
            className="flex min-h-11 items-center justify-center gap-2 rounded-xl border border-border/70 px-3 text-sm font-medium transition hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Pencil className="size-3.5" /> Edit context
          </button>
        </div>
      )}

      {expanded && editing && (
        <div className="mt-3 space-y-3 border-t border-border/60 pt-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <ContextInput label="Origin" value={draft.origin ?? ''} onChange={(value) => setDraft({ ...draft, origin: value || null })} />
            <ContextInput label="Destination" value={draft.destination ?? ''} onChange={(value) => setDraft({ ...draft, destination: value || null })} />
            <ContextInput label="Date" value={draft.date ?? ''} onChange={(value) => setDraft({ ...draft, date: value || null })} />
            <ContextInput label="Class" value={draft.travelClass ?? ''} onChange={(value) => setDraft({ ...draft, travelClass: value || null })} />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setEditing(false)} className="flex min-h-10 items-center gap-2 rounded-xl px-3 text-sm font-medium hover:bg-muted">
              <X className="size-3.5" /> Cancel
            </button>
            <button type="button" onClick={save} className="min-h-10 rounded-xl bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
              Save changes
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function ContextValue({ label, value, icon }: { label: string; value?: string | number | null; icon?: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-muted/50 px-3 py-2">
      <div className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{icon}{label}</div>
      <div className="mt-0.5 text-sm font-medium">{valueOrUnknown(value)}</div>
    </div>
  );
}

function ContextInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-1 text-xs font-semibold text-muted-foreground">
      {label}
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder="Not specified" className="min-h-11 rounded-xl border border-border bg-background px-3 text-sm font-normal text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring" />
    </label>
  );
}
