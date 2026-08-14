'use client';

import { useState } from 'react';
import { ArrowRight, Check, ChevronRight, Clock3, Sparkles } from 'lucide-react';
import { DecisionBadge } from './DecisionBadge';
import { JourneyComparison } from './JourneyComparison';

export type JourneyWorkspaceOption = {
  id: string;
  trainNumber?: string;
  trainName?: string;
  departure?: { station?: string; time?: string };
  arrival?: { station?: string; time?: string };
  duration?: string;
  fare?: string;
  className?: string;
  changes?: number;
  availability?: string;
  confidence?: number;
  badges?: Array<{ label: string; tone?: 'positive' | 'warning' | 'neutral' | 'ai' | 'stale' }>;
  risk?: 'low' | 'medium' | 'high';
};

export type JourneyDecisionWorkspaceData = {
  origin?: string;
  destination?: string;
  date?: string;
  passengers?: number;
  travelClass?: string;
  analysis?: string;
  recommendation?: { optionId?: string; reason?: string[]; confidence?: number };
  options?: JourneyWorkspaceOption[];
  verification?: { status?: 'verified' | 'estimated' | 'unavailable' | 'stale'; updatedAt?: string };
};

type Props = {
  data?: JourneyDecisionWorkspaceData | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onSelectOption?: (option: JourneyWorkspaceOption) => void;
};

const verificationCopy = { verified: 'Verified', estimated: 'AI estimate', unavailable: 'Availability unavailable', stale: 'May be outdated' } as const;
const verificationTone = { verified: 'positive', estimated: 'ai', unavailable: 'warning', stale: 'stale' } as const;

function formatConfidence(value?: number) {
  if (value === undefined) return null;
  return `${Math.round(value <= 1 ? value * 100 : value)}% confidence`;
}

function availabilityTone(value?: string): 'positive' | 'warning' | 'neutral' {
  if (!value) return 'neutral';
  const normalized = value.toLowerCase();
  if (normalized.includes('wl') || normalized.includes('wait')) return 'warning';
  if (normalized.includes('rac') || normalized.includes('confirm') || normalized.includes('available')) return 'positive';
  return 'neutral';
}

export function JourneyDecisionWorkspace({ data, loading = false, error = null, onRetry, onSelectOption }: Props) {
  const options = data?.options ?? [];
  const recommended = options.find((option) => option.id === data?.recommendation?.optionId) ?? options[0];
  const [comparisonIds, setComparisonIds] = useState<string[]>([]);

  const toggleComparison = (id: string) => {
    setComparisonIds((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length >= 3 ? current : [...current, id]);
  };

  const comparisonOptions = options.filter((option) => comparisonIds.includes(option.id));

  if (loading) {
    return <section aria-label="Planning journey" className="rounded-3xl border border-white/10 bg-white/[0.035] p-5 shadow-2xl sm:p-7"><div className="flex items-center gap-3 text-sm font-medium text-white"><span className="grid h-9 w-9 place-items-center rounded-2xl bg-blue-500/15 text-blue-300"><Sparkles className="h-4 w-4 animate-pulse" /></span>RailYatra is planning your journey</div><div className="mt-6 grid gap-3">{['Understanding your route', 'Comparing journey options', 'Building recommendations'].map((step, index) => <div key={step} className="flex items-center gap-3 rounded-2xl border border-white/8 bg-black/10 px-4 py-3 text-sm text-slate-300"><span className={`h-2 w-2 rounded-full ${index === 1 ? 'animate-pulse bg-blue-400' : 'bg-emerald-400'}`} />{step}</div>)}</div></section>;
  }

  if (error && !data) {
    return <section role="alert" className="rounded-3xl border border-rose-400/20 bg-rose-400/[0.05] p-6"><p className="text-base font-semibold text-white">We couldn’t finish your journey analysis.</p><p className="mt-2 text-sm text-slate-400">Your journey request is still safe. You can retry without starting over.</p>{onRetry ? <button type="button" onClick={onRetry} className="mt-5 min-h-11 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-slate-200">Try again</button> : null}</section>;
  }

  if (!data) return null;

  const confidence = formatConfidence(data.recommendation?.confidence ?? recommended?.confidence);
  const verification = data.verification?.status ?? 'estimated';

  return (
    <section className="space-y-5" aria-label="Journey decision workspace">
      <header className="rounded-3xl border border-white/10 bg-white/[0.035] p-5 sm:p-7"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-300">Journey decision</p><h2 className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">{data.origin || 'Your journey'} <span className="mx-1 text-slate-500">→</span> {data.destination || 'Destination'}</h2><div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">{data.date ? <span className="rounded-full border border-white/10 px-3 py-1.5">{data.date}</span> : null}{data.passengers ? <span className="rounded-full border border-white/10 px-3 py-1.5">{data.passengers} passenger{data.passengers > 1 ? 's' : ''}</span> : null}{data.travelClass ? <span className="rounded-full border border-white/10 px-3 py-1.5">{data.travelClass}</span> : null}</div></div><DecisionBadge label={verificationCopy[verification]} tone={verificationTone[verification]} /></div>{data.verification?.updatedAt ? <p className="mt-3 text-[11px] text-slate-500">Data timestamp: {data.verification.updatedAt}</p> : null}</header>

      {recommended ? <article className="overflow-hidden rounded-3xl border border-blue-400/20 bg-gradient-to-br from-blue-500/[0.12] via-white/[0.035] to-violet-500/[0.08] p-5 shadow-xl sm:p-7"><div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2 text-sm font-semibold text-blue-200"><Sparkles className="h-4 w-4" /> Best overall</div>{confidence ? <DecisionBadge label={confidence} tone="ai" /> : null}</div><div className="mt-6 grid gap-6 lg:grid-cols-[1fr_auto] lg:items-end"><div><p className="text-sm text-slate-400">{recommended.trainNumber ? `Train ${recommended.trainNumber}` : 'Recommended journey'}</p><h3 className="mt-1 text-xl font-bold text-white">{recommended.trainName || 'Best available option'}</h3><JourneyTimeline option={recommended} /></div><div className="lg:text-right">{recommended.fare ? <p className="text-2xl font-bold text-white">{recommended.fare}</p> : null}{recommended.className ? <p className="mt-1 text-sm text-slate-400">{recommended.className}</p> : null}<button type="button" onClick={() => onSelectOption?.(recommended)} className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-slate-200">View journey <ArrowRight className="h-4 w-4" /></button></div></div>{data.recommendation?.reason?.length ? <div className="mt-6 border-t border-white/10 pt-5"><p className="text-sm font-semibold text-white">Why this option?</p><div className="mt-3 grid gap-2 sm:grid-cols-2">{data.recommendation.reason.slice(0, 4).map((reason) => <div key={reason} className="flex items-start gap-2 rounded-xl bg-black/10 px-3 py-2.5 text-sm text-slate-300"><Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />{reason}</div>)}</div></div> : null}</article> : <article className="rounded-3xl border border-blue-400/15 bg-gradient-to-br from-blue-500/[0.09] via-white/[0.03] to-violet-500/[0.06] p-5 sm:p-7"><div className="flex items-center gap-2 text-sm font-semibold text-blue-200"><Sparkles className="h-4 w-4" /> AI analysis received</div><p className="mt-3 text-sm leading-6 text-slate-300">RailYatra has analyzed this journey. Structured train options will appear here when live journey data is available.</p>{data.analysis ? <p className="mt-4 line-clamp-4 rounded-2xl border border-white/8 bg-black/10 p-4 text-sm leading-6 text-slate-400">{data.analysis}</p> : null}</article>}

      {options.length > 0 ? <div><div className="mb-3 flex flex-wrap items-end justify-between gap-3"><div><h3 className="text-lg font-bold text-white">Journey options</h3><p className="mt-1 text-xs text-slate-500">Select up to 3 options to compare.</p></div>{comparisonIds.length ? <DecisionBadge label={`${comparisonIds.length} selected`} tone="ai" /> : null}</div><div className="grid gap-3">{options.filter((option) => option.id !== recommended?.id).map((option) => <JourneyOptionCard key={option.id} option={option} selectedForComparison={comparisonIds.includes(option.id)} onCompare={() => toggleComparison(option.id)} onSelect={() => onSelectOption?.(option)} />)}</div></div> : null}

      <JourneyComparison options={comparisonOptions} onRemove={(id) => toggleComparison(id)} />
      {error ? <div className="rounded-2xl border border-amber-400/20 bg-amber-400/[0.05] px-4 py-3 text-sm text-amber-200">We received part of the journey analysis. {onRetry ? <button type="button" onClick={onRetry} className="ml-1 min-h-11 font-semibold underline underline-offset-4">Retry the remaining analysis</button> : null}</div> : null}
    </section>
  );
}

function JourneyTimeline({ option }: { option: JourneyWorkspaceOption }) {
  return <div className="mt-5 grid grid-cols-[auto_1fr_auto] items-center gap-3 sm:gap-5"><div><p className="text-lg font-bold text-white">{option.departure?.time || '—'}</p><p className="max-w-[110px] truncate text-xs text-slate-400">{option.departure?.station || 'Departure'}</p></div><div className="relative flex items-center gap-2 text-slate-500" aria-label={`Journey duration ${option.duration || 'unknown'}`}><span className="h-2 w-2 rounded-full bg-blue-400" /><span className="h-px flex-1 bg-gradient-to-r from-blue-400/60 via-white/15 to-violet-400/60" /><Clock3 className="h-4 w-4 shrink-0" /><span className="h-px flex-1 bg-gradient-to-r from-violet-400/60 via-white/15 to-blue-400/60" /><span className="h-2 w-2 rounded-full bg-violet-400" /></div><div className="text-right"><p className="text-lg font-bold text-white">{option.arrival?.time || '—'}</p><p className="max-w-[110px] truncate text-xs text-slate-400">{option.arrival?.station || 'Arrival'}</p></div></div>;
}

function JourneyOptionCard({ option, selectedForComparison, onCompare, onSelect }: { option: JourneyWorkspaceOption; selectedForComparison: boolean; onCompare: () => void; onSelect: () => void }) {
  return <article className={`rounded-2xl border p-4 text-left transition duration-200 ${selectedForComparison ? 'border-violet-400/40 bg-violet-400/[0.06]' : 'border-white/10 bg-white/[0.025]'}`}><div className="flex items-start justify-between gap-4"><button type="button" onClick={onSelect} className="group min-w-0 flex-1 text-left focus:outline-none focus:ring-2 focus:ring-blue-400/60"><div className="flex items-start gap-3"><div className="min-w-0"><p className="text-sm font-semibold text-white">{option.trainNumber || 'Journey option'}{option.trainName ? ` · ${option.trainName}` : ''}</p><JourneyTimeline option={option} /></div><ChevronRight className="mt-1 h-5 w-5 shrink-0 text-slate-500 transition group-hover:translate-x-0.5 group-hover:text-blue-300" /></div></button><button type="button" onClick={onCompare} aria-pressed={selectedForComparison} className="min-h-11 rounded-xl border border-white/10 px-3 text-xs font-semibold text-slate-300 hover:bg-white/5 hover:text-white focus:outline-none focus:ring-2 focus:ring-violet-400/60">{selectedForComparison ? 'Selected' : 'Compare'}</button></div><div className="mt-4 flex flex-wrap items-center gap-2 text-xs">{option.badges?.map((badge) => <DecisionBadge key={badge.label} label={badge.label} tone={badge.tone} />)}{option.duration ? <DecisionBadge label={option.duration} /> : null}{option.className ? <DecisionBadge label={option.className} /> : null}{option.changes !== undefined ? <DecisionBadge label={option.changes === 0 ? 'Direct' : `${option.changes} change${option.changes > 1 ? 's' : ''}`} tone={option.changes === 0 ? 'positive' : 'neutral'} /> : null}{option.availability ? <DecisionBadge label={option.availability} tone={availabilityTone(option.availability)} /> : null}{option.risk ? <DecisionBadge label={`${option.risk[0].toUpperCase()}${option.risk.slice(1)} risk`} tone={option.risk === 'low' ? 'positive' : option.risk === 'high' ? 'warning' : 'neutral'} /> : null}{option.fare ? <span className="ml-auto font-semibold text-white">{option.fare}</span> : null}</div></article>;
}
