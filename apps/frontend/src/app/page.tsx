'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../store/authStore';
import { API_BASE_URL, authenticatedFetch } from '../lib/api';
import { parseSSEBuffer } from '../lib/sse';
import FloatingAI from '../components/FloatingAI';
import MarkdownMessage from '../components/MarkdownMessage';
import { Train, Sparkles, Moon, Sun, Compass, LogOut, Cpu, CheckCircle, TrendingUp, HelpCircle } from 'lucide-react';

interface AIResponse {
  reply: string;
  parsed_intent: string;
  confidence: number;
  explanation: string;
  credits_left: number;
}

const DECISION_CONVERSATION_KEY = 'railyatra_decision_engine_conversation_id';

export default function Home() {
  const { user, token, theme, setTheme, clearAuth, setAuth } = useAuthStore();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'agent' | 'billing' | 'features'>('agent');
  const [credits, setCredits] = useState(() => user?.subscriptions?.[0]?.credits ?? 3);
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

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
  };

  const handleSimulateQuery = (text: string) => setQuery(text);

  const handleRunQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    const userQuery = query.trim();
    if (!userQuery || aiLoading) return;

    setAiLoading(true);
    setAiResponse(null);
    if (credits > 0) setCredits(prev => prev - 1);

    try {
      // Resolve the conversation at submit time. This avoids effect-driven state
      // synchronization while still restoring the same conversation after refresh.
      const storedConversationId = sessionStorage.getItem(conversationStorageKey);
      const activeConversationId = conversationId ?? storedConversationId ?? await createDecisionConversation(userQuery);
      if (activeConversationId !== conversationId) setConversationId(activeConversationId);

      const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations/${activeConversationId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userQuery,
          context: { current_page: '/', surface: 'decision-engine' },
        }),
      });

      if (!response.ok) throw new Error(`Decision Engine request failed (${response.status})`);
      if (!response.body) throw new Error('Readable stream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';
      let intent = 'conversation';
      let completed = false;

      const processEvent = (rawData: string) => {
        const data = JSON.parse(rawData) as { type?: string; value?: string; reply?: string; message?: string };
        if (data.type === 'intent' && typeof data.value === 'string') intent = data.value;
        if (data.type === 'token' && typeof data.value === 'string') {
          accumulated += data.value;
          setAiResponse({ reply: accumulated, parsed_intent: intent, confidence: 0, explanation: 'Orchestrated by the RailYatra AI decision engine.', credits_left: credits });
        }
        if (data.type === 'done') {
          completed = true;
          if (typeof data.reply === 'string') accumulated = data.reply;
          setAiResponse({ reply: accumulated, parsed_intent: intent, confidence: 0, explanation: 'Orchestrated by the RailYatra AI decision engine.', credits_left: credits });
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
    } catch (err) {
      console.error('Error fetching AI decision response:', err);
      setAiResponse({
        reply: 'RailYatra AI is temporarily unavailable. Please try again in a moment.',
        parsed_intent: 'system_error',
        confidence: 0,
        explanation: 'The conversation was preserved. Retrying will continue the same conversation.',
        credits_left: credits,
      });
    } finally {
      setQuery('');
      setAiLoading(false);
    }
  };

  const handleToggleTheme = () => {
    if (theme === 'light') setTheme('dark');
    else if (theme === 'dark') setTheme('auto');
    else setTheme('light');
  };

  const handleSimulateUpgrade = () => {
    if (!user) return;
    const upgradedUser = { ...user, role: 'PREMIUM' as const, subscriptions: [{ tier: 'PREMIUM' as const, credits: 100, status: 'active' }] };
    setAuth(token || 'mock_token', upgradedUser);
    setCredits(100);
  };

  const handleSimulateDowngrade = () => {
    if (!user) return;
    const downgradedUser = { ...user, role: 'USER' as const, subscriptions: [{ tier: 'FREE' as const, credits: 3, status: 'active' }] };
    setAuth(token || 'mock_token', downgradedUser);
    setCredits(3);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground transition-colors duration-300">
      <header className="sticky top-0 z-50 glass border-b border-border shadow-sm px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-premium"><Train className="h-5 w-5" /></div><span className="text-xl font-bold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">RailYatra AI</span></div>
        <div className="flex items-center gap-4">
          <button onClick={handleToggleTheme} className="p-2.5 rounded-xl border border-border hover:bg-muted/50 cursor-pointer text-muted-foreground hover:text-foreground transition-colors" title={`Current theme: ${theme}. Click to switch.`}>{theme === 'light' ? <Sun className="h-5 w-5 text-warning" /> : <Moon className="h-5 w-5" />}</button>
          {user ? <div className="flex items-center gap-3 pl-4 border-l border-border"><div className="flex flex-col text-right hidden sm:flex"><span className="text-sm font-semibold">{user.fullName}</span><span className="text-xs text-muted-foreground capitalize">{user.role} Account</span></div><div className="h-10 w-10 rounded-xl bg-secondary/15 flex items-center justify-center text-secondary font-bold border border-secondary/25">{user.fullName[0].toUpperCase()}</div><button onClick={handleLogout} className="p-2.5 rounded-xl border border-border hover:bg-danger/10 hover:text-danger cursor-pointer transition-colors text-muted-foreground" title="Log Out"><LogOut className="h-5 w-5" /></button></div> : null}
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="rounded-2xl p-8 bg-gradient-to-br from-primary/10 via-secondary/5 to-transparent border border-primary/15 relative overflow-hidden"><div className="absolute right-0 bottom-0 opacity-10"><Compass className="h-64 w-64 rotate-12 text-primary" /></div><div className="relative z-10 space-y-4"><span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-accent/15 text-accent-foreground border border-accent/20"><Sparkles className="h-3.5 w-3.5" />Phase 2 Deployment Live</span><h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">The AI Operating System for Travel Decisions.</h1><p className="text-muted-foreground text-base max-w-xl">Avoid waitlist uncertainties, discover split-journey tickets, optimize departure boarding junctions, and predict delays using specialized agent logic.</p><button onClick={() => router.push('/chat')} className="mt-2 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:opacity-90 transition-all shadow-premium cursor-pointer"><Sparkles className="h-4.5 w-4.5" />Open AI Workspace</button></div></div>

          <div className="border-b border-border flex gap-6 text-sm"><button onClick={() => setActiveTab('agent')} className={`pb-3 font-semibold border-b-2 cursor-pointer ${activeTab === 'agent' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}>AI Travel Decision Engine</button><button onClick={() => setActiveTab('billing')} className={`pb-3 font-semibold border-b-2 cursor-pointer ${activeTab === 'billing' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}>Subscription & Premium Credits</button><button onClick={() => setActiveTab('features')} className={`pb-3 font-semibold border-b-2 cursor-pointer ${activeTab === 'features' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground'}`}>Agent Mesh Directory</button></div>

          {activeTab === 'agent' && <div className="space-y-6"><div className="rounded-2xl border border-border bg-card p-6 shadow-premium"><h3 className="text-lg font-bold mb-4 flex items-center gap-2"><Cpu className="h-5 w-5 text-primary" />Ask AI Decision Engine</h3><form onSubmit={handleRunQuery} className="space-y-4"><div className="relative"><input type="text" className="w-full pl-4 pr-12 py-3.5 rounded-xl border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm" placeholder="Enter natural language query (e.g. I need to travel to Delhi before 9 AM)..." value={query} onChange={(e) => setQuery(e.target.value)} disabled={aiLoading} /><button type="submit" disabled={aiLoading || !query.trim()} className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-primary text-primary-foreground disabled:opacity-50 cursor-pointer"><Sparkles className="h-4 w-4" /></button></div><div className="flex flex-wrap gap-2 pt-1"><span className="text-xs text-muted-foreground self-center mr-1">Simulate Query:</span><button type="button" onClick={() => handleSimulateQuery('I want to travel from Bilaspur to New Delhi next Friday')} className="text-xs bg-muted px-3 py-1.5 rounded-lg border border-border cursor-pointer">&quot;Bilaspur to Delhi next Friday&quot;</button><button type="button" onClick={() => handleSimulateQuery('My ticket waitlist is WL 23. What are my confirmation chances?')} className="text-xs bg-muted px-3 py-1.5 rounded-lg border border-border cursor-pointer">&quot;Waitlist WL 23 chances?&quot;</button></div></form></div>

            {(aiLoading || aiResponse) && <div className="rounded-2xl border border-border bg-card p-6 shadow-premium space-y-4"><div className="flex items-center justify-between border-b border-border pb-3"><div className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-accent animate-pulse" /><span className="font-bold text-sm">Orchestrated AI Response</span></div></div>{aiLoading && !aiResponse ? <div className="space-y-3 py-4"><div className="h-4 bg-muted rounded animate-pulse w-3/4" /><div className="h-4 bg-muted rounded animate-pulse w-1/2" /><div className="h-4 bg-muted rounded animate-pulse w-5/6" /></div> : aiResponse ? <div className="space-y-4"><div className="p-4 rounded-xl bg-muted/50 border border-border text-sm leading-relaxed"><MarkdownMessage content={aiResponse.reply} /></div>{aiResponse.explanation && <p className="text-muted-foreground text-xs">{aiResponse.explanation}</p>}<div className="flex items-center justify-between text-xs text-muted-foreground"><span className="flex items-center gap-1"><CheckCircle className="h-4 w-4 text-accent" />Parsed Intent: <strong className="font-semibold text-foreground uppercase">{aiResponse.parsed_intent}</strong></span><span>Conversation context: preserved</span></div></div> : null}</div>}
          </div>}

          {activeTab === 'billing' && <div className="rounded-2xl border border-border bg-card p-6 shadow-premium space-y-6"><div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-border pb-6"><div><h3 className="text-lg font-bold">Billing & Feature Gates</h3><p className="text-sm text-muted-foreground">Simulate payment checkouts and credit usage quotas</p></div><div className="flex gap-2"><button onClick={handleSimulateUpgrade} className="px-4 py-2 rounded-xl bg-accent text-accent-foreground font-semibold text-xs cursor-pointer">Simulate Premium Upgrade</button><button onClick={handleSimulateDowngrade} className="px-4 py-2 rounded-xl border border-border font-semibold text-xs cursor-pointer">Simulate Downgrade</button></div></div><div className="grid grid-cols-1 md:grid-cols-3 gap-6"><div className="p-5 rounded-xl border border-border bg-background"><span className="text-xs text-muted-foreground uppercase font-bold">Account Level</span><p className="text-2xl font-black text-primary">{user?.role || 'User'}</p></div><div className="p-5 rounded-xl border border-border bg-background"><span className="text-xs text-muted-foreground uppercase font-bold">Remaining AI Credits</span><p className="text-2xl font-black text-accent">{credits} Credits</p></div><div className="p-5 rounded-xl border border-border bg-background"><span className="text-xs text-muted-foreground uppercase font-bold">Usage Meter</span><p className="text-2xl font-black">{user?.role === 'PREMIUM' ? 'Unlimited' : `${credits} / 3`}</p></div></div></div>}

          {activeTab === 'features' && <div className="grid grid-cols-1 md:grid-cols-2 gap-6">{[['Travel Planner Agent','Plans end-to-end itineraries including multi-modal connectivity.'],['Boarding Optimizer','Recommends adjacent travel terminals to maximize availability.'],['Delay Prediction','Uses historical delay metadata to improve arrival estimates.'],['Fare Optimizer','Calculates split-ticketing opportunities to lower travel cost.']].map(([title, description]) => <div key={title} className="rounded-xl border border-border bg-card p-5 space-y-2"><h4 className="font-bold text-sm text-primary">{title}</h4><p className="text-xs text-muted-foreground leading-relaxed">{description}</p></div>)}</div>}
        </div>

        <div className="space-y-6"><div className="rounded-2xl border border-border bg-card p-6 shadow-premium space-y-5"><h3 className="text-base font-bold flex items-center gap-2"><TrendingUp className="h-5 w-5 text-primary" />Core Infrastructure Status</h3><div className="space-y-4 text-xs"><div className="flex justify-between py-2.5 border-b border-border"><span className="text-muted-foreground">Prisma Client</span><span className="font-semibold text-accent">● SQLite Connected</span></div><div className="flex justify-between py-2.5 border-b border-border"><span className="text-muted-foreground">Backend Core</span><span className="font-semibold text-accent">● NestJS Active</span></div><div className="flex justify-between py-2.5 border-b border-border"><span className="text-muted-foreground">AI Service</span><span className="font-semibold text-accent">● FastAPI Active</span></div><div className="flex justify-between py-2.5"><span className="text-muted-foreground">Conversation</span><span className="font-semibold text-accent">● Context Preserved</span></div></div></div><div className="rounded-2xl border border-border bg-card p-6 shadow-premium space-y-4"><h3 className="text-base font-bold flex items-center gap-2"><HelpCircle className="h-5 w-5 text-secondary" />Phase 2 Validation Steps</h3><ul className="space-y-3 text-xs text-muted-foreground list-disc pl-4 leading-relaxed"><li>Authenticate and verify the active session.</li><li>Open the Decision Engine and send a journey request.</li><li>Reply to follow-up questions without losing context.</li><li>Refresh and send another follow-up; the stored conversation is reused.</li><li>Verify subscription and credit behavior.</li></ul></div></div>
      </main>
      <FloatingAI />
      <footer className="mt-auto border-t border-border py-6 text-center text-xs text-muted-foreground bg-muted/20"><p>© 2026 RailYatra AI. All rights reserved. Under Venture Scaffolding.</p></footer>
    </div>
  );
}
