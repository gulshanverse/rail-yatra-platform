'use client';

import { useMemo } from 'react';
import { Clock3, Heart, ShieldCheck, Sparkles, WalletCards } from 'lucide-react';
import type { JourneyWorkspaceOption } from './JourneyDecisionWorkspace';

export type DecisionMode = 'overall' | 'fastest' | 'cheapest' | 'comfortable' | 'lowest-risk';

type Props = {
  options: JourneyWorkspaceOption[];
  value: DecisionMode;
  onChange: (mode: DecisionMode) => void;
  disabled?: boolean;
};

const modes: Array<{ id: DecisionMode; label: string; description: string; icon: typeof Sparkles }> = [
  { id: 'overall', label: 'Best overall', description: 'Balanced choice', icon: Sparkles },
  { id: 'fastest', label: 'Fastest', description: 'Shortest duration', icon: Clock3 },
  { id: 'cheapest', label: 'Cheapest', description: 'Lowest known fare', icon: WalletCards },
  { id: 'comfortable', label: 'Most comfortable', description: 'Comfort-first', icon: Heart },
  { id: 'lowest-risk', label: 'Lowest risk', description: 'Fewer changes', icon: ShieldCheck },
];

function durationMinutes(value?: string) {
  if (!value) return null;
  const hour = value.match(/(\d+(?:\.\d+)?)\s*h/i);
  const minute = value.match(/(\d+)\s*m/i);
  if (!hour && !minute) return null;
  return Number(hour?.[1] ?? 0) * 60 + Number(minute?.[1] ?? 0);
}

function numericFare(value?: string) {
  if (!value) return null;
  const match = value.replace(/,/g, '').match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : null;
}

function scoreOption(option: JourneyWorkspaceOption, mode: DecisionMode) {
  const duration = durationMinutes(option.duration);
  const fare = numericFare(option.fare);
  const changes = option.changes ?? Number.POSITIVE_INFINITY;
  const risk = option.risk === 'low' ? 0 : option.risk === 'medium' ? 1 : option.risk === 'high' ? 2 : 1;
  const hasClass = Boolean(option.className);

  switch (mode) {
    case 'fastest': return duration === null ? Number.POSITIVE_INFINITY : duration;
    case 'cheapest': return fare === null ? Number.POSITIVE_INFINITY : fare;
    case 'lowest-risk': return risk * 1000 + changes;
    case 'comfortable': return (hasClass ? 0 : 1000) + changes * 10 + (duration ?? 10000) / 1000;
    case 'overall':
    default:
      return risk * 1000 + changes * 20 + (duration ?? 10000) / 100 + (fare ?? 100000) / 1000;
  }
}

export function rankOptions(options: JourneyWorkspaceOption[], mode: DecisionMode) {
  const candidates = options.filter((option) => {
    if (mode === 'cheapest') return numericFare(option.fare) !== null;
    if (mode === 'fastest') return durationMinutes(option.duration) !== null;
    return true;
  });

  return [...candidates].sort((a, b) => scoreOption(a, mode) - scoreOption(b, mode));
}

export function DecisionModeSelector({ options, value, onChange, disabled = false }: Props) {
  const availableModes = useMemo(() => modes.map((mode) => ({
    ...mode,
    enabled: mode.id === 'overall' || rankOptions(options, mode.id).length > 0,
  })), [options]);

  return (
    <section aria-label="Decision mode" className="rounded-3xl border border-white/10 bg-white/[0.025] p-4 sm:p-5">
      <div className="mb-3">
        <p className="text-sm font-semibold text-white">How should RailYatra optimize?</p>
        <p className="mt-1 text-xs text-slate-500">Choose a priority and the recommendation will use only available journey data.</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        {availableModes.map(({ id, label, description, icon: Icon, enabled }) => (
          <button
            key={id}
            type="button"
            disabled={disabled || !enabled}
            aria-pressed={value === id}
            onClick={() => onChange(id)}
            className={`min-h-16 rounded-2xl border px-3 py-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300/70 disabled:cursor-not-allowed disabled:opacity-40 ${value === id ? 'border-blue-300/35 bg-blue-400/10 shadow-lg shadow-blue-950/10' : 'border-white/8 bg-black/10 hover:border-white/15 hover:bg-white/[0.04]'}`}
          >
            <span className="flex items-center gap-2">
              <span className={`grid h-8 w-8 place-items-center rounded-xl ${value === id ? 'bg-blue-400/15 text-blue-200' : 'bg-white/5 text-slate-400'}`}><Icon className="h-4 w-4" aria-hidden="true" /></span>
              <span className="min-w-0">
                <span className="block text-xs font-semibold text-white">{label}</span>
                <span className="mt-0.5 block truncate text-[11px] text-slate-500">{description}</span>
              </span>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
