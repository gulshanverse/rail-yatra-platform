'use client';

import { CheckCircle2, CircleAlert, CircleDashed, Clock3, Sparkles } from 'lucide-react';

export type DecisionBadgeTone = 'positive' | 'warning' | 'neutral' | 'ai' | 'stale';

const toneStyles: Record<DecisionBadgeTone, string> = {
  positive: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300',
  warning: 'border-amber-400/20 bg-amber-400/10 text-amber-200',
  neutral: 'border-white/10 bg-white/[0.05] text-slate-300',
  ai: 'border-violet-400/20 bg-violet-400/10 text-violet-200',
  stale: 'border-orange-400/20 bg-orange-400/10 text-orange-200',
};

const icons = {
  positive: CheckCircle2,
  warning: CircleAlert,
  neutral: CircleDashed,
  ai: Sparkles,
  stale: Clock3,
};

export function DecisionBadge({ label, tone = 'neutral' }: { label: string; tone?: DecisionBadgeTone }) {
  const Icon = icons[tone];
  return (
    <span className={`inline-flex min-h-7 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${toneStyles[tone]}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {label}
    </span>
  );
}
