'use client';

import { ArrowRight, GitCompare, MessageCircleQuestion } from 'lucide-react';
import MarkdownMessage from '../MarkdownMessage';

interface RichAIMessageProps {
  content: string;
  contextLabel?: string;
  streaming?: boolean;
  onFollowUp?: (question: string) => void;
}

export function RichAIMessage({ content, contextLabel, streaming, onFollowUp }: RichAIMessageProps) {
  return (
    <div className="space-y-3">
      {contextLabel ? (
        <div className="flex items-center gap-2 rounded-xl border border-indigo-300/10 bg-indigo-300/[0.045] px-3 py-2 text-[11px] text-slate-400">
          <ArrowRight className="h-3.5 w-3.5 text-indigo-300" aria-hidden="true" />
          <span>Answering for <strong className="font-semibold text-slate-200">{contextLabel}</strong></span>
        </div>
      ) : null}

      <div className="rounded-2xl rounded-tl-md border border-white/8 bg-white/[0.025] px-4 py-3 text-sm leading-6 text-slate-200">
        <MarkdownMessage content={content} />
        {streaming ? <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded-full bg-indigo-300 align-middle" aria-label="Response streaming" /> : null}
      </div>

      {!streaming && onFollowUp ? (
        <div className="flex flex-wrap gap-2" aria-label="Suggested follow-up questions">
          <button type="button" onClick={() => onFollowUp('What is the main trade-off for this journey?')} className="inline-flex min-h-10 items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.025] px-3 text-xs font-medium text-slate-300 transition hover:bg-white/[0.07] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60">
            <GitCompare className="h-3.5 w-3.5" aria-hidden="true" /> Main trade-off
          </button>
          <button type="button" onClick={() => onFollowUp('Can you explain the recommendation for this journey?')} className="inline-flex min-h-10 items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.025] px-3 text-xs font-medium text-slate-300 transition hover:bg-white/[0.07] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60">
            <MessageCircleQuestion className="h-3.5 w-3.5" aria-hidden="true" /> Explain recommendation
          </button>
        </div>
      ) : null}
    </div>
  );
}
