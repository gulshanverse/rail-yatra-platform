'use client';

import { Check, GitCompareArrows, ShieldCheck, Timer, WalletCards, X } from 'lucide-react';
import type { JourneyWorkspaceOption } from './JourneyDecisionWorkspace';
import { DecisionBadge } from './DecisionBadge';

type TradeoffMetric = 'duration' | 'fare' | 'changes' | 'risk';

type TradeoffResult = {
  metric: TradeoffMetric;
  label: string;
  winnerId?: string;
  winnerLabel?: string;
  value?: string;
  icon: typeof Timer;
};

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

function riskScore(value?: JourneyWorkspaceOption['risk']) {
  if (value === 'low') return 0;
  if (value === 'medium') return 1;
  if (value === 'high') return 2;
  return null;
}

function displayName(option: JourneyWorkspaceOption) {
  return option.trainNumber || option.trainName || 'Selected journey';
}

export function getTradeoffLeaders(options: JourneyWorkspaceOption[]): TradeoffResult[] {
  const metrics: TradeoffResult[] = [
    { metric: 'duration', label: 'Fastest', icon: Timer },
    { metric: 'fare', label: 'Lowest known fare', icon: WalletCards },
    { metric: 'changes', label: 'Fewest changes', icon: GitCompareArrows },
    { metric: 'risk', label: 'Lowest risk', icon: ShieldCheck },
  ];

  return metrics.map((metric) => {
    const candidates = options
      .map((option) => {
        const value = metric.metric === 'duration'
          ? durationMinutes(option.duration)
          : metric.metric === 'fare'
            ? numericFare(option.fare)
            : metric.metric === 'changes'
              ? option.changes ?? null
              : riskScore(option.risk);
        return { option, value };
      })
      .filter((item): item is { option: JourneyWorkspaceOption; value: number } => item.value !== null && Number.isFinite(item.value));

    if (candidates.length === 0) return metric;

    const winner = candidates.reduce((best, current) => current.value < best.value ? current : best);
    const value = metric.metric === 'duration'
      ? options.find((option) => option.id === winner.option.id)?.duration
      : metric.metric === 'fare'
        ? winner.option.fare
        : metric.metric === 'changes'
          ? winner.value === 0 ? 'Direct' : `${winner.value} change${winner.value === 1 ? '' : 's'}`
          : winner.option.risk ? `${winner.option.risk[0].toUpperCase()}${winner.option.risk.slice(1)}` : undefined;

    return { ...metric, winnerId: winner.option.id, winnerLabel: displayName(winner.option), value };
  });
}

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
    { label: 'Risk', value: (option) => option.risk ? `${option.risk[0].toUpperCase()}${option.risk.slice(1)}` : undefined },
  ];
  const tradeoffs = getTradeoffLeaders(options);

  return (
    <section className="overflow-hidden rounded-3xl border border-violet-400/20 bg-violet-400/[0.035]" aria-label="Journey comparison">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4 sm:px-6">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-xl bg-violet-400/10 text-violet-200"><GitCompareArrows className="h-4 w-4" aria-hidden="true" /></span>
          <div><h3 className="text-sm font-semibold text-white">Compare journeys</h3><p className="text-[11px] text-slate-500">See the trade-offs before choosing. Only supplied journey data is used.</p></div>
        </div>
        <DecisionBadge label={`${options.length} selected`} tone="ai" />
      </div>

      <div className="border-b border-white/10 px-5 py-4 sm:px-6">
        <div className="mb-3 flex items-end justify-between gap-3">
          <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-200">Decision trade-offs</p><p className="mt-1 text-xs text-slate-500">Different journeys can win on different priorities.</p></div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {tradeoffs.map(({ metric, label, winnerLabel, value, icon: Icon }) => (
            <div key={metric} className="rounded-2xl border border-white/8 bg-black/10 p-3">
              <div className="flex items-center gap-2 text-[11px] font-medium text-slate-500"><Icon className="h-3.5 w-3.5 text-violet-300" aria-hidden="true" />{label}</div>
              {winnerLabel ? <><p className="mt-2 truncate text-sm font-semibold text-white" title={winnerLabel}>{winnerLabel}</p><p className="mt-0.5 text-xs text-slate-400">{value}</p></> : <p className="mt-2 text-xs text-slate-600">Not enough data</p>}
            </div>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[620px] p-4 sm:p-5">
          <div className="grid gap-3" style={{ gridTemplateColumns: `minmax(110px, .7fr) repeat(${options.length}, minmax(180px, 1fr))` }}>
            <div />
            {options.map((option) => (
              <div key={option.id} className="rounded-2xl border border-white/10 bg-white/[0.035] p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0"><p className="truncate text-sm font-semibold text-white">{option.trainNumber || 'Journey option'}</p><p className="truncate text-xs text-slate-500">{option.trainName || 'Structured option'}</p></div>
                  <button type="button" onClick={() => onRemove(option.id)} className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-500 hover:bg-white/5 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/70" aria-label={`Remove ${option.trainNumber || 'journey'} from comparison`}><X className="h-4 w-4" aria-hidden="true" /></button>
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
          <div className="mt-4 flex items-center gap-2 text-xs text-slate-500"><Check className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />RailYatra never fills missing railway facts with guesses.</div>
        </div>
      </div>
    </section>
  );
}
