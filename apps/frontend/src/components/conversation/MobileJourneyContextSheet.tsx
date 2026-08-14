'use client';

import { X } from 'lucide-react';
import type { JourneyContext } from './JourneyContextCard';

interface MobileJourneyContextSheetProps {
  open: boolean;
  context: JourneyContext;
  onClose: () => void;
}

export function MobileJourneyContextSheet({ open, context, onClose }: MobileJourneyContextSheetProps) {
  if (!open) return null;

  const items = [
    ['Origin', context.origin],
    ['Destination', context.destination],
    ['Date', context.date],
    ['Passengers', context.passengers],
    ['Class', context.travelClass],
  ] as const;

  return (
    <div className="fixed inset-0 z-50 sm:hidden" role="dialog" aria-modal="true" aria-labelledby="mobile-context-title">
      <button type="button" aria-label="Close journey context" onClick={onClose} className="absolute inset-0 bg-black/65 backdrop-blur-[2px]" />
      <div className="absolute inset-x-0 bottom-0 rounded-t-[28px] border border-white/10 bg-slate-950 px-4 pb-[calc(env(safe-area-inset-bottom)+1rem)] pt-3 shadow-[0_-20px_70px_rgba(0,0,0,0.5)]">
        <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-white/15" aria-hidden="true" />
        <div className="flex items-center justify-between gap-4">
          <div><h2 id="mobile-context-title" className="text-base font-semibold text-white">Journey context</h2><p className="mt-0.5 text-xs text-slate-500">What RailYatra is using for this conversation.</p></div>
          <button type="button" onClick={onClose} aria-label="Close" className="grid size-10 place-items-center rounded-xl border border-white/10 text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60"><X className="size-4" aria-hidden="true" /></button>
        </div>
        <div className="mt-5 grid gap-2">
          {items.map(([label, value]) => <div key={label} className="flex items-center justify-between gap-4 rounded-2xl bg-white/[0.035] px-4 py-3"><span className="text-xs font-medium text-slate-500">{label}</span><span className="max-w-[65%] truncate text-right text-sm font-medium text-slate-100">{value ?? 'Not specified'}</span></div>)}
        </div>
      </div>
    </div>
  );
}
