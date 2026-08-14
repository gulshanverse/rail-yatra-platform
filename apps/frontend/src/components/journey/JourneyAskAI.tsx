'use client';

import { MessageCircle, Sparkles } from 'lucide-react';
import type { JourneyWorkspaceOption } from './JourneyDecisionWorkspace';

const prompts = [
  'Why is this better for me?',
  'What is the main trade-off?',
  'Is there a safer option?',
];

type Props = {
  option: JourneyWorkspaceOption;
  onAsk: (question: string, option: JourneyWorkspaceOption) => void | Promise<void>;
  disabled?: boolean;
};

export function JourneyAskAI({ option, onAsk, disabled = false }: Props) {
  return (
    <div className="rounded-2xl border border-indigo-300/15 bg-indigo-400/[0.045] p-4" aria-label="Ask RailYatra about this journey">
      <div className="flex items-start gap-3">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-indigo-400/10 text-indigo-200">
          <MessageCircle className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-white">Ask RailYatra about this journey</p>
            <span className="inline-flex items-center gap-1 rounded-full border border-indigo-300/15 bg-indigo-300/10 px-2 py-0.5 text-[10px] font-medium text-indigo-200"><Sparkles className="h-3 w-3" aria-hidden="true" />Context-aware</span>
          </div>
          <p className="mt-1 text-xs leading-5 text-slate-500">Your question continues the existing conversation instead of starting a new chat.</p>
          <div className="mt-3 flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {prompts.map((prompt) => (
              <button key={prompt} type="button" disabled={disabled} onClick={() => void onAsk(prompt, option)} className="min-h-10 shrink-0 rounded-xl border border-white/10 bg-white/[0.035] px-3 text-xs font-medium text-slate-300 transition hover:border-indigo-300/30 hover:bg-indigo-400/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/70">
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
