'use client';

import { Check, GitCompareArrows, X } from 'lucide-react';
import type { JourneyWorkspaceOption } from './JourneyDecisionWorkspace';
import { DecisionBadge } from './DecisionBadge';

export function JourneyComparison({ options, onRemove }: { options: JourneyWorkspaceOption[]; onRemove: (id: string) => void }) {
  if (options.length < 2) return null;

  const rows: Array<{ label: string; value: (option: JourneyWorkspaceOption) => string | undefined }> = [
    { label: 'Departure', value: (option) => option.departure?.time },
    { label: 'Arrival', value: (option) => option.arrival?.time },
    { label: 'Duration', value: (option) => option.duration },
    { label: 'Class', value: (option) => option.className },
    { label: 'Fare', value: (option) => option.fare },
    { label: 'Changes', value: (option) => option.changes === undefined ? undefined : option.changes === 0 ? 'Direct' : `${option.changes}` },
    { label: 'Availability', value: (option) => option.availability },
  ];

  return (
    <section className="overflow-hidden rounded-3xl border border-violet-400/20 bg-violet-400/[0.035]" aria-label="Journey comparison">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4 sm:px-6">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-xl bg-violet-400/10 text-violet-200"><GitCompareArrows className="h-4 w-4" /></span>
          <div><h3 className="text-sm font-semibold text-white">Compare journeys</h3><p className="text-[11px] text-slate-500">Only fields supplied by the journey service are shown.</p></div>
        </div>
        <DecisionBadge label={`${options.length} selected`} tone="ai" />
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[620px] p-4 sm:p-5">
          <div className="grid gap-3" style={{ gridTemplateColumns: `minmax(110px, .7fr) repeat(${options.length}, minmax(180px, 1fr))` }}>
            <div />
            {options.map((option) => (
              <div key={option.id} className="rounded-2xl border border-white/10 bg-white/[0.035] p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0"><p className="truncate text-sm font-semibold text-white">{option.trainNumber || 'Journey option'}</p><p className="truncate text-xs text-slate-500">{option.trainName || 'Structured option'}</p></div>
                  <button type="button" onClick={() => onRemove(option.id)} className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-500 hover:bg-white/5 hover:text-white" aria-label={`Remove ${option.trainNumber || 'journey'} from comparison`}><X className="h-4 w-4" /></button>
                </div>
              </div>
            ))}
            {rows.flatMap(({ label, value }) => [
              <div key={`${label}-label`} className="flex min-h-11 items-center px-2 text-xs font-medium text-slate-500">{label}</div>,
              ...options.map((option) => {
                const field = value(option);
                return <div key={`${label}-${option.id}`} className="flex min-h-11 items-center rounded-xl bg-black/10 px-3 text-sm text-slate-200">{field || <span className="text-slate-600">Not available</span>}</div>;
              }),
            ])}
          </div>
          <div className="mt-4 flex items-center gap-2 text-xs text-slate-500"><Check className="h-3.5 w-3.5 text-emerald-400" />RailYatra never fills missing railway facts with guesses.</div>
        </div>
      </div>
    </section>
  );
}
