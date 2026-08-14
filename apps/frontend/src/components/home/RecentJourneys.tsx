import { History } from 'lucide-react';
import { RecentJourney, RecentJourneyCard } from './RecentJourneyCard';

interface RecentJourneysProps {
  journeys?: RecentJourney[];
  onSelect?: (journey: RecentJourney) => void;
}

export function RecentJourneys({ journeys = [], onSelect }: RecentJourneysProps) {
  return (
    <section aria-labelledby="recent-journeys-heading">
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
            <History className="h-3.5 w-3.5" aria-hidden="true" />
            Your journeys
          </p>
          <h2 id="recent-journeys-heading" className="mt-1 text-xl font-semibold tracking-tight text-white">Pick up where you left off</h2>
        </div>
      </div>

      {journeys.length > 0 ? (
        <div className="flex gap-3 overflow-x-auto pb-2 lg:grid lg:grid-cols-3 lg:overflow-visible">
          {journeys.map((journey) => (
            <RecentJourneyCard key={journey.id} journey={journey} onSelect={onSelect} />
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] px-5 py-7 text-center">
          <p className="text-sm font-medium text-slate-300">Your recent journeys will appear here.</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">Start by telling RailYatra where you want to go.</p>
        </div>
      )}
    </section>
  );
}
