import { ArrowUpRight, Clock3, TrainFront } from 'lucide-react';

export interface RecentJourney {
  id: string;
  origin: string;
  destination: string;
  meta: string;
  updated: string;
}

interface RecentJourneyCardProps {
  journey: RecentJourney;
  onSelect?: (journey: RecentJourney) => void;
}

export function RecentJourneyCard({ journey, onSelect }: RecentJourneyCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect?.(journey)}
      className="group min-w-[250px] flex-1 rounded-2xl border border-white/8 bg-slate-900/60 p-4 text-left transition-[transform,border-color,background-color] duration-200 hover:-translate-y-0.5 hover:border-blue-400/25 hover:bg-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60"
    >
      <div className="flex items-start justify-between gap-4">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500/10 text-blue-300">
          <TrainFront className="h-4 w-4" aria-hidden="true" />
        </span>
        <ArrowUpRight className="h-4 w-4 text-slate-600 transition-colors group-hover:text-blue-300" aria-hidden="true" />
      </div>
      <p className="mt-4 text-sm font-semibold text-white">{journey.origin} <span className="text-slate-500">→</span> {journey.destination}</p>
      <p className="mt-1 text-xs text-slate-400">{journey.meta}</p>
      <p className="mt-4 flex items-center gap-1.5 text-[11px] text-slate-500">
        <Clock3 className="h-3 w-3" aria-hidden="true" />
        {journey.updated}
      </p>
    </button>
  );
}
