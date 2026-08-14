'use client';

import { ArrowUp, ChevronDown, Loader2, Paperclip, Square } from 'lucide-react';
import { useState } from 'react';

interface MobileCopilotBarProps {
  disabled?: boolean;
  streaming?: boolean;
  contextLabel?: string;
  onSend?: (message: string) => void;
  onStop?: () => void;
  onOpenContext?: () => void;
}

export function MobileCopilotBar({ disabled, streaming, contextLabel, onSend, onStop, onOpenContext }: MobileCopilotBarProps) {
  const [draft, setDraft] = useState('');

  const submit = () => {
    const message = draft.trim();
    if (!message || disabled || streaming) return;
    onSend?.(message);
    setDraft('');
  };

  return (
    <div className="sticky bottom-0 z-30 border-t border-white/10 bg-slate-950/95 px-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] pt-2 backdrop-blur-xl sm:px-4">
      {contextLabel && onOpenContext ? (
        <button type="button" onClick={onOpenContext} className="mb-2 inline-flex min-h-8 max-w-full items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.035] px-3 text-[11px] font-medium text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60">
          <span className="truncate">{contextLabel}</span><ChevronDown className="size-3 shrink-0" aria-hidden="true" />
        </button>
      ) : null}
      <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/[0.045] p-2 shadow-[0_-8px_30px_rgba(0,0,0,0.16)] focus-within:border-indigo-300/30">
        <button type="button" aria-label="Attach file" disabled className="grid size-10 shrink-0 place-items-center rounded-xl text-slate-600" title="Attachments coming soon"><Paperclip className="size-4" aria-hidden="true" /></button>
        <label className="sr-only" htmlFor="mobile-copilot-input">Ask RailYatra</label>
        <textarea id="mobile-copilot-input" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit(); } }} disabled={disabled || streaming} rows={1} placeholder="Ask RailYatra anything..." className="max-h-28 min-h-10 flex-1 resize-none bg-transparent px-1 py-2 text-sm leading-6 text-white outline-none placeholder:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50" />
        {streaming ? <button type="button" onClick={onStop} aria-label="Stop response" className="grid size-10 shrink-0 place-items-center rounded-xl bg-white/[0.07] text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60"><Square className="size-3.5 fill-current" aria-hidden="true" /></button> : <button type="button" onClick={submit} disabled={!draft.trim() || disabled} aria-label="Send message" className="grid size-10 shrink-0 place-items-center rounded-xl bg-indigo-400 text-slate-950 transition hover:bg-indigo-300 disabled:cursor-not-allowed disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-200/70">{disabled ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <ArrowUp className="size-4" aria-hidden="true" />}</button>}
      </div>
      <p className="mt-1 text-center text-[10px] text-slate-700">Enter to send · Shift + Enter for a new line</p>
    </div>
  );
}
