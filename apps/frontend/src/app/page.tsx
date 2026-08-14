'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, LogOut, Moon, Sun, Train } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { API_BASE_URL, authenticatedFetch } from '../lib/api';
import { parseSSEBuffer } from '../lib/sse';
import MarkdownMessage from '../components/MarkdownMessage';
import { HomeIntelligence, HomeTrustStatus, JourneyComposer, RecentJourneys } from '../components/home';

interface AIResponse {
  reply: string;
  parsed_intent: string;
  explanation: string;
}

const DECISION_CONVERSATION_KEY = 'railyatra_decision_engine_conversation_id';

export default function Home() {
  const { user, theme, setTheme, clearAuth } = useAuthStore();
  const router = useRouter();
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const conversationStorageKey = `${DECISION_CONVERSATION_KEY}:${user?.id ?? 'anonymous'}`;

  const createDecisionConversation = async (initialQuery: string) => {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary: `Decision: ${initialQuery.slice(0, 32)}` }),
    });
    if (!response.ok) throw new Error(`Conversation creation failed (${response.status})`);
    const data = await response.json() as { id?: string };
    if (!data.id) throw new Error('Conversation ID missing');
    sessionStorage.setItem(conversationStorageKey, data.id);
    setConversationId(data.id);
    return data.id;
  };

  const sendDecisionMessage = async (id: string, message: string) => authenticatedFetch(
    `${API_BASE_URL}/api/conversations/${id}/chat`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, context: { current_page: '/', surface: 'home-journey-composer' } }),
    },
  );

  const handleRunQuery = async (userQuery: string) => {
    const query = userQuery.trim();
    if (!query || aiLoading) return;

    setAiLoading(true);
    setAiResponse(null);

    try {
      let activeConversationId = conversationId ?? sessionStorage.getItem(conversationStorageKey);
      let response: Response;

      if (activeConversationId) {
        response = await sendDecisionMessage(activeConversationId, query);
        if (response.status === 404) {
          sessionStorage.removeItem(conversationStorageKey);
          setConversationId(null);
          activeConversationId = await createDecisionConversation(query);
          response = await sendDecisionMessage(activeConversationId, query);
        }
      } else {
        activeConversationId = await createDecisionConversation(query);
        response = await sendDecisionMessage(activeConversationId, query);
      }

      if (!response.ok) throw new Error(`Decision Engine request failed (${response.status})`);
      if (!response.body) throw new Error('Readable stream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';
      let intent = 'conversation';
      let completed = false;

      const processEvent = (rawData: string) => {
        const data = JSON.parse(rawData) as {
          type?: string;
          value?: string;
          reply?: string;
          message?: string;
        };

        if (data.type === 'intent' && typeof data.value === 'string') intent = data.value;
        if (data.type === 'token' && typeof data.value === 'string') {
          accumulated += data.value;
          setAiResponse({
            reply: accumulated,
            parsed_intent: intent,
            explanation: 'Orchestrated by the RailYatra AI decision engine.',
          });
        }
        if (data.type === 'done') {
          completed = true;
          if (typeof data.reply === 'string') accumulated = data.reply;
          setAiResponse({
            reply: accumulated,
            parsed_intent: intent,
            explanation: 'Orchestrated by the RailYatra AI decision engine.',
          });
        }
        if (data.type === 'error') throw new Error(data.message || 'AI stream failed');
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const [events, remainder] = parseSSEBuffer(buffer);
        buffer = remainder;
        for (const event of events) processEvent(event.data);
      }

      buffer += decoder.decode();
      const [finalEvents] = parseSSEBuffer(buffer);
      for (const event of finalEvents) processEvent(event.data);

      if (!completed && !accumulated.trim()) throw new Error('Empty AI response');
    } catch (error) {
      console.error('Error fetching AI decision response:', error);
      setAiResponse({
        reply: 'RailYatra AI is temporarily unavailable. Please try again in a moment.',
        parsed_intent: 'system_error',
        explanation: 'Your journey context was preserved. Retry to continue the same conversation.',
      });
    } finally {
      setAiLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
  };

  const handleToggleTheme = () => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('auto');
    else setTheme('light');
  };

  return (
    <div className="min-h-screen bg-[#070A12] text-white">
      <header className="sticky top-0 z-50 border-b border-white/8 bg-[#070A12]/90 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <button type="button" onClick={() => router.push('/')} className="flex items-center gap-2.5 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500 text-white shadow-lg shadow-blue-500/20"><Train className="h-4.5 w-4.5" aria-hidden="true" /></span>
            <span className="text-lg font-bold tracking-tight">RailYatra <span className="text-blue-400">AI</span></span>
          </button>
          <div className="flex items-center gap-2 sm:gap-3">
            <button type="button" onClick={handleToggleTheme} className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 text-slate-400 transition-colors hover:bg-white/5 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60" aria-label="Change theme">
              {theme === 'light' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            {user && (
              <div className="flex items-center gap-2.5 border-l border-white/10 pl-2.5 sm:pl-3">
                <div className="hidden text-right sm:block"><p className="text-sm font-semibold text-white">{user.fullName}</p><p className="text-[11px] capitalize text-slate-500">{user.role.toLowerCase()} account</p></div>
                <div className="grid h-9 w-9 place-items-center rounded-xl border border-indigo-300/20 bg-indigo-400/10 text-sm font-bold text-indigo-200">{user.fullName[0]?.toUpperCase()}</div>
                <button type="button" onClick={handleLogout} className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 text-slate-400 transition-colors hover:bg-red-400/10 hover:text-red-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400/50" aria-label="Log out"><LogOut className="h-4 w-4" /></button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-7 sm:px-6 lg:py-12">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">{user ? `Welcome back, ${user.fullName.split(' ')[0]}` : 'Travel intelligence'}</p>
          </div>
          <HomeTrustStatus />
        </div>

        <JourneyComposer onSubmit={handleRunQuery} />

        {aiResponse && (
          <section className="overflow-hidden rounded-[24px] border border-white/10 bg-slate-900/70 shadow-[0_20px_70px_rgba(0,0,0,0.2)]" aria-live="polite">
            <div className="flex items-center justify-between border-b border-white/8 px-5 py-4 sm:px-6">
              <div className="flex items-center gap-2.5"><span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-400/10 text-indigo-300"><CheckCircle2 className="h-4 w-4" /></span><div><p className="text-sm font-semibold">RailYatra recommendation</p><p className="text-[11px] text-slate-500">Conversation context preserved</p></div></div>
              <span className="rounded-full border border-emerald-400/15 bg-emerald-400/5 px-2.5 py-1 text-[11px] font-medium text-emerald-300">{aiResponse.parsed_intent}</span>
            </div>
            <div className="px-5 py-5 sm:px-6"><div className="prose prose-invert max-w-none text-sm leading-6 text-slate-200"><MarkdownMessage content={aiResponse.reply} /></div><p className="mt-5 text-xs text-slate-500">{aiResponse.explanation}</p></div>
          </section>
        )}

        {aiLoading && !aiResponse && (
          <section className="rounded-[24px] border border-indigo-300/10 bg-slate-900/60 p-5 sm:p-6" aria-live="polite" aria-label="RailYatra is thinking">
            <div className="flex items-center gap-3"><span className="grid h-9 w-9 animate-pulse place-items-center rounded-xl bg-indigo-400/10 text-indigo-300"><Train className="h-4 w-4" /></span><div className="flex-1 space-y-2"><div className="h-3 w-40 animate-pulse rounded bg-white/10" /><div className="h-2.5 w-64 max-w-full animate-pulse rounded bg-white/5" /></div></div>
          </section>
        )}

        <RecentJourneys />
        <HomeIntelligence />
      </main>

      <footer className="border-t border-white/8 px-4 py-6 text-center text-xs text-slate-600"><p>© 2026 RailYatra AI · Travel decisions, made clearer.</p></footer>
    </div>
  );
}
