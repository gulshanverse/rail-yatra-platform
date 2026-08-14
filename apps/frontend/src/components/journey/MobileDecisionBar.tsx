'use client';

import { ArrowRight, Sparkles } from 'lucide-react';
import type { JourneyWorkspaceOption } from './JourneyDecisionWorkspace';

type Props = {
  option?: JourneyWorkspaceOption;
  modeLabel: string;
  onSelect?: (option: JourneyWorkspaceOption) => void;
};

export function MobileDecisionBar({ option, modeLabel, onSelect }: Props) {
  if (!option) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-40 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:hidden">
      <div className="pointer-events-auto mx-auto flex max-w-lg items-center gap-3 rounded-2xl border border-blue-300/20 bg-[#0b1020]/95 p-3 shadow-[0_-12px_40px_rgba(0,0,0,0.35)] backdrop-blur-xl">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-blue-200">
            <Sparkles className="h-3 w-3" aria-hidden="true" /> {modeLabel}
          </div>
          <p className="mt-1 truncate text-sm font-semibold text-white">{option.trainNumber || option.trainName || 'Recommended journey'}</p>
          <p className="truncate text-[11px] text-slate-400">
            {[option.departure?.time, option.arrival?.time, option.duration].filter(Boolean).join(' · ') || 'Review your recommendation'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onSelect?.(option)}
          className="inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-xl bg-white px-3.5 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-black/20 transition active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300/80"
        >
          View <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
