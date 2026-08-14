'use client';

import { Check, Info, Sparkles } from 'lucide-react';
import { DecisionBadge } from './DecisionBadge';

export type RecommendationVerification = {
  status?: 'verified' | 'estimated' | 'unavailable' | 'stale';
  updatedAt?: string;
};

type Props = {
  reasons?: string[];
  confidence?: number;
  verification?: RecommendationVerification;
};

const verificationCopy = {
  verified: 'Verified journey data',
  estimated: 'AI estimate — verify before booking',
  unavailable: 'Live availability unavailable',
  stale: 'Data may be outdated',
} as const;

const verificationTone = {
  verified: 'positive',
  estimated: 'ai',
  unavailable: 'warning',
  stale: 'stale',
} as const;

function formatConfidence(value?: number) {
  if (value === undefined || !Number.isFinite(value)) return null;
  const percentage = Math.round(value <= 1 ? value * 100 : value);
  if (percentage < 0 || percentage > 100) return null;
  return `${percentage}% confidence`;
}

export function AIReasoningPanel({ reasons = [], confidence, verification }: Props) {
  const status = verification?.status ?? 'estimated';
  const confidenceLabel = formatConfidence(confidence);
  const visibleReasons = reasons.filter(Boolean).slice(0, 4);

  return (
    <section className="mt-6 overflow-hidden rounded-2xl border border-white/10 bg-black/15" aria-label="Recommendation reasoning">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-4 py-3.5 sm:px-5">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-xl bg-violet-400/10 text-violet-300">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-white">Why RailYatra recommends this</p>
            <p className="text-[11px] text-slate-500">Based only on the journey data available to the decision engine</p>
          </div>
        </div>
        {confidenceLabel ? <DecisionBadge label={confidenceLabel} tone="ai" /> : null}
      </div>

      <div className="grid gap-4 p-4 sm:p-5 lg:grid-cols-[1fr_auto] lg:items-start">
        <div>
          {visibleReasons.length > 0 ? (
            <ul className="grid gap-2 sm:grid-cols-2">
              {visibleReasons.map((reason) => (
                <li key={reason} className="flex items-start gap-2.5 rounded-xl border border-white/8 bg-white/[0.025] px-3 py-2.5 text-sm leading-5 text-slate-300">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" aria-hidden="true" />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex items-start gap-2.5 rounded-xl border border-white/8 bg-white/[0.025] px-3 py-3 text-sm leading-5 text-slate-400">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
              <span>No structured reasoning was returned for this recommendation.</span>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3.5 lg:min-w-64">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Data trust</p>
          <div className="mt-2">
            <DecisionBadge label={verificationCopy[status]} tone={verificationTone[status]} />
          </div>
          {verification?.updatedAt ? <p className="mt-2 text-[11px] leading-4 text-slate-500">Updated {verification.updatedAt}</p> : null}
        </div>
      </div>
    </section>
  );
}
