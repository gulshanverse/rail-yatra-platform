'use client';

import { ArrowUp, Sparkles } from 'lucide-react';
import { FormEvent, useMemo, useState } from 'react';

const suggestions = [
  { label: 'Best confirmation', value: 'Find the option with the best confirmation chances' },
  { label: 'Cheapest', value: 'Find the cheapest comfortable option' },
  { label: 'Fastest', value: 'Find the fastest route' },
  { label: 'Most comfortable', value: 'Find the most comfortable option' },
];

interface JourneyComposerProps {
  initialValue?: string;
  onSubmit: (query: string) => void | Promise<void>;
}

export function JourneyComposer({ initialValue = '', onSubmit }: JourneyComposerProps) {
  const [query, setQuery] = useState(initialValue);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = useMemo(() => query.trim().length > 0 && !submitting, [query, submitting]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = query.trim();
    if (!value || submitting) return;

    setSubmitting(true);
    try {
      await onSubmit(value);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.16),transparent_38%),linear-gradient(145deg,rgba(15,23,42,0.96),rgba(9,14,27,0.98))] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.28)] sm:p-7 lg:p-9">
      <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />
      <div className="relative">
        <div className="mb-7 max-w-2xl">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-300/20 bg-indigo-400/10 px-3 py-1.5 text-xs font-medium text-indigo-200">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            AI travel intelligence
          </div>
          <h1 className="text-3xl font-semibold tracking-[-0.035em] text-white sm:text-4xl lg:text-5xl">
            Where are you going?
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400 sm:text-base">
            Tell RailYatra what you&apos;re planning. We&apos;ll compare routes, comfort, timing and confirmation signals for you.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="group rounded-2xl border border-white/12 bg-slate-950/70 p-2 transition-[border-color,box-shadow] duration-200 focus-within:border-indigo-400/60 focus-within:shadow-[0_0_0_4px_rgba(99,102,241,0.09)]">
          <label htmlFor="journey-query" className="sr-only">Tell RailYatra about your journey</label>
          <div className="flex items-end gap-2">
            <div className="flex min-h-14 flex-1 items-center px-3 sm:px-4">
              <Sparkles className="mr-3 hidden h-5 w-5 shrink-0 text-indigo-300 sm:block" aria-hidden="true" />
              <textarea
                id="journey-query"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Try: Bilaspur to Delhi next Friday"
                rows={2}
                className="max-h-36 min-h-12 w-full resize-none bg-transparent py-2.5 text-base leading-6 text-white outline-none placeholder:text-slate-500"
                disabled={submitting}
              />
            </div>
            <button
              type="submit"
              disabled={!canSubmit}
              aria-label={submitting ? 'Planning journey' : 'Plan journey'}
              className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-blue-500 text-white transition-all duration-200 hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ArrowUp className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
          <div className="flex items-center justify-between gap-3 px-3 pb-1 pt-2 text-[11px] text-slate-500 sm:px-4">
            <span>Natural language works best</span>
            <span className="hidden sm:inline">Enter to plan · Shift + Enter for a new line</span>
          </div>
        </form>

        <div className="mt-5">
          <p className="mb-2.5 text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Try asking</p>
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion.label}
                type="button"
                onClick={() => setQuery(suggestion.value)}
                className="shrink-0 rounded-full border border-white/10 bg-white/[0.035] px-3.5 py-2 text-xs font-medium text-slate-300 transition-colors duration-150 hover:border-indigo-300/30 hover:bg-indigo-400/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/60"
              >
                {suggestion.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
