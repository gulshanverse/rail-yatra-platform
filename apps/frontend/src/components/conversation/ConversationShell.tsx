'use client';

import { Bot, Check, Circle, Loader2, MessageCircle, RefreshCw, Square, User } from 'lucide-react';
import MarkdownMessage from '../MarkdownMessage';

type ConversationShellProps = {
  userQuery?: string;
  aiReply?: string;
  status?: 'idle' | 'streaming' | 'ready' | 'error' | 'stopped';
  conversationId?: string | null;
  contextLabel?: string;
  onRetry?: () => void;
  onStop?: () => void;
};

const statusCopy = {
  idle: 'Ready',
  streaming: 'Thinking',
  ready: 'Ready',
  error: 'Connection issue',
  stopped: 'Response stopped',
} as const;

export function ConversationShell({
  userQuery,
  aiReply,
  status = 'idle',
  conversationId,
  contextLabel,
  onRetry,
  onStop,
}: ConversationShellProps) {
  const hasMessages = Boolean(userQuery || aiReply);

  return (
    <section
      aria-label="RailYatra AI conversation"
      className="overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/70 shadow-[0_24px_90px_rgba(0,0,0,0.22)]"
    >
      <header className="border-b border-white/8 bg-white/[0.025] px-4 py-4 sm:px-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-indigo-400/10 text-indigo-200">
              <MessageCircle className="h-4 w-4" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h2 className="truncate text-sm font-semibold text-white">RailYatra AI</h2>
                <span className="hidden text-[11px] text-slate-600 sm:inline">Travel Copilot</span>
              </div>
              <div className="mt-1 flex items-center gap-1.5 text-[11px] text-slate-500" aria-live="polite">
                {status === 'streaming' ? <Loader2 className="h-3 w-3 animate-spin text-blue-300" aria-hidden="true" /> : <Circle className={`h-2 w-2 fill-current ${status === 'error' ? 'text-amber-300' : status === 'stopped' ? 'text-slate-400' : 'text-emerald-400'}`} aria-hidden="true" />}
                {statusCopy[status]}
              </div>
            </div>
          </div>
          {contextLabel ? <span className="max-w-[48%] truncate rounded-full border border-white/10 bg-white/[0.025] px-3 py-1.5 text-[11px] font-medium text-slate-400" title={contextLabel}>{contextLabel}</span> : null}
        </div>
        {conversationId ? (
          <div className="mt-3 flex items-center gap-1.5 text-[10px] text-slate-600">
            <Check className="h-3 w-3 text-emerald-500" aria-hidden="true" />
            Conversation context active
          </div>
        ) : null}
      </header>

      <div className="max-h-[620px] overflow-y-auto px-4 py-5 sm:px-6 sm:py-6" aria-live="polite" aria-relevant="additions text">
        {!hasMessages ? (
          <div className="flex min-h-[180px] flex-col items-center justify-center px-6 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-2xl border border-indigo-300/10 bg-indigo-300/[0.06] text-indigo-200">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </span>
            <p className="mt-4 text-sm font-semibold text-white">Your RailYatra conversation starts here</p>
            <p className="mt-1 max-w-sm text-xs leading-5 text-slate-500">Ask about a journey, compare options, or follow up on an earlier decision.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {userQuery ? (
              <div className="flex items-start justify-end gap-3">
                <div className="max-w-[88%] rounded-2xl rounded-tr-md border border-blue-400/15 bg-blue-500/[0.10] px-4 py-3 sm:max-w-[76%]">
                  <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-blue-300">You</p>
                  <p className="whitespace-pre-wrap text-sm leading-6 text-slate-100">{userQuery}</p>
                </div>
                <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.035] text-slate-400" aria-hidden="true"><User className="h-4 w-4" /></span>
              </div>
            ) : null}

            {aiReply ? (
              <div className="flex items-start gap-3">
                <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-xl border border-indigo-300/10 bg-indigo-300/[0.06] text-indigo-200" aria-hidden="true"><Bot className="h-4 w-4" /></span>
                <div className="min-w-0 max-w-[92%] sm:max-w-[82%]">
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-indigo-300">RailYatra AI</p>
                  <div className="rounded-2xl rounded-tl-md border border-white/8 bg-white/[0.025] px-4 py-3 text-sm leading-6 text-slate-200">
                    <MarkdownMessage content={aiReply} />
                    {status === 'streaming' ? <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded-full bg-indigo-300 align-middle" aria-label="Response streaming" /> : null}
                  </div>
                  {status === 'error' && onRetry ? (
                    <div className="mt-3 rounded-2xl border border-amber-300/10 bg-amber-300/[0.05] p-3">
                      <p className="text-xs leading-5 text-amber-100/80">RailYatra could not finish this response. Your conversation is preserved.</p>
                      <button type="button" onClick={onRetry} className="mt-2 inline-flex min-h-10 items-center gap-2 rounded-xl border border-amber-200/15 bg-amber-200/10 px-3 text-xs font-semibold text-amber-100 transition hover:bg-amber-200/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300/60">
                        <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Retry in this conversation
                      </button>
                    </div>
                  ) : null}
                  {status === 'stopped' && onRetry ? (
                    <button type="button" onClick={onRetry} className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 text-xs font-semibold text-slate-200 transition hover:bg-white/[0.07] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60">
                      <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Continue response
                    </button>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {status === 'streaming' && onStop ? (
        <div className="flex justify-center border-t border-white/8 bg-white/[0.015] px-4 py-3">
          <button type="button" onClick={onStop} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3.5 text-xs font-semibold text-slate-300 transition hover:bg-white/[0.07] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60">
            <Square className="h-3 w-3 fill-current" aria-hidden="true" /> Stop response
          </button>
        </div>
      ) : null}
    </section>
  );
}
