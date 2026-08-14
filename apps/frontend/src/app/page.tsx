'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { LogOut, Moon, Sun, Train } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { API_BASE_URL, authenticatedFetch } from '../lib/api';
import { parseSSEBuffer } from '../lib/sse';
import { JourneyAskAI, JourneyDecisionWorkspace } from '../components/journey';
import { ConversationShell, JourneyContextCard, type JourneyContext } from '../components/conversation';
import { HomeIntelligence, HomeTrustStatus, JourneyComposer, RecentJourneys } from '../components/home';

interface AIResponse { reply: string; parsed_intent: string; explanation: string; }
const DECISION_CONVERSATION_KEY = 'railyatra_decision_engine_conversation_id';

function extractRoute(query: string) {
  const match = query.match(/(.+?)\s+(?:to|→)\s+(.+?)(?=\s+(?:for|on|today|tomorrow|next)\b|$)/i);
  return { origin: match?.[1]?.trim(), destination: match?.[2]?.trim() };
}
function extractDate(query: string) {
  const match = query.match(/\b(today|tomorrow|next\s+\w+|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b/i);
  return match?.[1];
}

export default function Home() {
  const { user, theme, setTheme, clearAuth } = useAuthStore();
  const router = useRouter();
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState('');
  const [journeyContext, setJourneyContext] = useState<JourneyContext>({});
  const conversationStorageKey = `${DECISION_CONVERSATION_KEY}:${user?.id ?? 'anonymous'}`;

  const createDecisionConversation = async (initialQuery: string) => {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ summary: `Decision: ${initialQuery.slice(0, 32)}` }) });
    if (!response.ok) throw new Error(`Conversation creation failed (${response.status})`);
    const data = await response.json() as { id?: string };
    if (!data.id) throw new Error('Conversation ID missing');
    sessionStorage.setItem(conversationStorageKey, data.id);
    setConversationId(data.id);
    return data.id;
  };
  const sendDecisionMessage = async (id: string, message: string) => authenticatedFetch(`${API_BASE_URL}/api/conversations/${id}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, context: { current_page: '/', surface: 'home-journey-composer', journey: journeyContext } }) });

  const handleRunQuery = async (userQuery: string) => {
    const query = userQuery.trim();
    if (!query || aiLoading) return;
    setLastQuery(query);
    const route = extractRoute(query);
    setJourneyContext((current) => ({ ...current, origin: route.origin ?? current.origin, destination: route.destination ?? current.destination, date: extractDate(query) ?? current.date }));
    setAiLoading(true); setAiResponse(null);
    try {
      let activeConversationId = conversationId ?? sessionStorage.getItem(conversationStorageKey);
      let response: Response;
      if (activeConversationId) {
        response = await sendDecisionMessage(activeConversationId, query);
        if (response.status === 404) {
          sessionStorage.removeItem(conversationStorageKey); setConversationId(null);
          activeConversationId = await createDecisionConversation(query);
          response = await sendDecisionMessage(activeConversationId, query);
        }
      } else {
        activeConversationId = await createDecisionConversation(query);
        response = await sendDecisionMessage(activeConversationId, query);
      }
      if (!response.ok) throw new Error(`Decision Engine request failed (${response.status})`);
      if (!response.body) throw new Error('Readable stream not supported');
      const reader = response.body.getReader(); const decoder = new TextDecoder();
      let buffer = ''; let accumulated = ''; let intent = 'conversation'; let completed = false;
      const processEvent = (rawData: string) => {
        const data = JSON.parse(rawData) as { type?: string; value?: string; reply?: string; message?: string };
        if (data.type === 'intent' && typeof data.value === 'string') intent = data.value;
        if (data.type === 'token' && typeof data.value === 'string') { accumulated += data.value; setAiResponse({ reply: accumulated, parsed_intent: intent, explanation: 'Orchestrated by the RailYatra AI decision engine.' }); }
        if (data.type === 'done') { completed = true; if (typeof data.reply === 'string') accumulated = data.reply; setAiResponse({ reply: accumulated, parsed_intent: intent, explanation: 'Orchestrated by the RailYatra AI decision engine.' }); }
        if (data.type === 'error') throw new Error(data.message || 'AI stream failed');
      };
      while (true) { const { done, value } = await reader.read(); if (done) break; buffer += decoder.decode(value, { stream: true }); const [events, remainder] = parseSSEBuffer(buffer); buffer = remainder; for (const event of events) processEvent(event.data); }
      buffer += decoder.decode(); const [finalEvents] = parseSSEBuffer(buffer); for (const event of finalEvents) processEvent(event.data);
      if (!completed && !accumulated.trim()) throw new Error('Empty AI response');
    } catch (error) {
      console.error('Error fetching AI decision response:', error);
      setAiResponse({ reply: 'RailYatra AI is temporarily unavailable. Please try again in a moment.', parsed_intent: 'system_error', explanation: 'Your journey context was preserved. Retry to continue the same conversation.' });
    } finally { setAiLoading(false); }
  };

  const handleAskAboutJourney = async (question: string) => {
    if (!lastQuery || aiLoading) return;
    await handleRunQuery(`${question} My original journey request was: "${lastQuery}"`);
  };
  const handleContextSave = (nextContext: JourneyContext) => setJourneyContext(nextContext);
  const handleLogout = () => { clearAuth(); router.push('/login'); };
  const handleToggleTheme = () => { if (theme === 'light') setTheme('dark'); else if (theme === 'dark') setTheme('auto'); else setTheme('light'); };
  const conversationStatus = aiLoading ? 'streaming' : aiResponse?.parsed_intent === 'system_error' ? 'error' : aiResponse ? 'ready' : 'idle';

  return (
    <div className="min-h-screen bg-[#070A12] text-white">
      <header className="sticky top-0 z-50 border-b border-white/8 bg-[#070A12]/90 px-4 py-3 backdrop-blur-xl sm:px-6"><div className="mx-auto flex max-w-6xl items-center justify-between"><button type="button" onClick={() => router.push('/')} className="flex items-center gap-2.5 rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60"><span className="grid h-9 w-9 place-items-center rounded-xl bg-blue-500 text-white shadow-lg shadow-blue-500/20"><Train className="h-4 w-4" aria-hidden="true" /></span><span className="text-lg font-bold tracking-tight">RailYatra <span className="text-blue-400">AI</span></span></button><div className="flex items-center gap-2 sm:gap-3"><button type="button" onClick={handleToggleTheme} className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 text-slate-400 transition-colors hover:bg-white/5 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/60" aria-label="Change theme">{theme === 'light' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}</button>{user && <div className="flex items-center gap-2.5 border-l border-white/10 pl-2.5 sm:pl-3"><div className="hidden text-right sm:block"><p className="text-sm font-semibold text-white">{user.fullName}</p><p className="text-[11px] capitalize text-slate-500">{user.role.toLowerCase()} account</p></div><div className="grid h-9 w-9 place-items-center rounded-xl border border-indigo-300/20 bg-indigo-400/10 text-sm font-bold text-indigo-200">{user.fullName[0]?.toUpperCase()}</div><button type="button" onClick={handleLogout} className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 text-slate-400 transition-colors hover:bg-red-400/10 hover:text-red-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400/50" aria-label="Log out"><LogOut className="h-4 w-4" /></button></div>}</div></div></header>
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-7 sm:px-6 lg:py-12">
        <div className="flex items-center justify-between gap-4"><div><p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">{user ? `Welcome back, ${user.fullName.split(' ')[0]}` : 'Travel intelligence'}</p></div><HomeTrustStatus /></div>
        <JourneyComposer onSubmit={handleRunQuery} />
        {(aiResponse || aiLoading) && <ConversationShell userQuery={lastQuery} aiReply={aiResponse?.reply} status={conversationStatus} conversationId={conversationId} contextLabel={journeyContext.origin && journeyContext.destination ? `${journeyContext.origin} → ${journeyContext.destination}` : undefined} />}
        {(aiResponse || aiLoading) && <JourneyContextCard context={journeyContext} onSave={handleContextSave} />}
        {aiResponse && <><JourneyDecisionWorkspace data={{ origin: journeyContext.origin ?? undefined, destination: journeyContext.destination ?? undefined, analysis: aiResponse.reply, verification: { status: 'estimated' } }} /><JourneyAskAI contextLabel={journeyContext.origin && journeyContext.destination ? `${journeyContext.origin} → ${journeyContext.destination}` : 'this journey'} onAsk={handleAskAboutJourney} disabled={aiLoading} /></>}
        {aiLoading && !aiResponse ? <JourneyDecisionWorkspace data={null} loading /> : null}
        <RecentJourneys /><HomeIntelligence />
      </main>
      <footer className="border-t border-white/8 px-4 py-6 text-center text-xs text-slate-600"><p>© 2026 RailYatra AI · Travel decisions, made clearer.</p></footer>
    </div>
  );
}
