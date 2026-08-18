'use client';

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, Check, ChevronRight, Mic, Pause, Plus, RotateCcw, Search, Sparkles, Ticket, TrainFront, X } from 'lucide-react';
import { AIThinking, AIThinkingStage, PageFrame, TrainCard } from '@/components/railyatra/railyatra-ui';
import { API_BASE_URL, authenticatedFetch, readApiError } from '@/lib/api';
import { friendlyAIError, parseAIEvent, parseSSEBuffer, type AIEvent } from '@/lib/sse';
import { useAuthStore } from '@/store/authStore';

const QUICK_ACTIONS = [
  { label: 'Find trains', prompt: 'Find the most reliable train from Bilaspur to Delhi tomorrow.', icon: TrainFront },
  { label: 'Plan a trip', prompt: 'Plan a thoughtful three-day trip from Bilaspur to Goa next weekend.', icon: Search },
  { label: 'Check PNR', prompt: 'Check the status of my PNR and explain what the confirmation probability means.', icon: Ticket },
  { label: 'Track train', prompt: 'Track my train and tell me what is next at the station.', icon: ArrowRight },
  { label: 'Find cheaper alternatives', prompt: 'Find a cheaper alternative with a similar arrival time.', icon: Sparkles },
];

const BASE_THINKING_STAGES: AIThinkingStage[] = [
  { id: 'understanding', label: 'Understanding your request', state: 'pending' },
  { id: 'journey_intelligence', label: 'Running journey intelligence', state: 'pending' },
  { id: 'answering', label: 'Preparing your answer', state: 'pending' },
  { id: 'complete', label: 'Ready to act', state: 'pending' },
];

type ConversationSummary = {
  id: string;
  summary?: string | null;
  createdAt: string;
  updatedAt: string;
};

type ConversationMessage = {
  id: string;
  role: 'user' | 'assistant' | string;
  content: string;
  timestamp: string;
};

type ConversationDetail = ConversationSummary & { messages: ConversationMessage[] };
type SpeechRecognitionResultLike = { 0?: { transcript?: string } };
type SpeechRecognitionEventLike = Event & { results: ArrayLike<SpeechRecognitionResultLike> };
type BrowserSpeechRecognition = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
type SpeechRecognitionConstructor = new () => BrowserSpeechRecognition;
type SpeechRecognitionWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

type ApiPayload<T> = T | { data?: T };

function unwrapPayload<T>(payload: ApiPayload<T>): T {
  if (payload && typeof payload === 'object' && 'data' in payload && payload.data !== undefined) {
    return payload.data as T;
  }
  return payload as T;
}

function formatConversationDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Recently';
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short' }).format(date);
}

function mapMessages(messages: ConversationMessage[]) {
  return messages
    .filter((message) => message.role === 'user' || message.role === 'assistant')
    .map((message) => ({ ...message, role: message.role as 'user' | 'assistant' }));
}

function updateThinkingStage(stages: AIThinkingStage[], event: AIEvent) {
  if (event.type !== 'thinking' || typeof event.stage !== 'string' || typeof event.label !== 'string') return stages;
  const state: AIThinkingStage['state'] = event.state === 'complete' || event.state === 'error' || event.state === 'active' ? event.state : 'pending';
  const existing = stages.some((stage) => stage.id === event.stage);
  const next: AIThinkingStage[] = existing
    ? stages.map((stage): AIThinkingStage => stage.id === event.stage ? { ...stage, label: event.label as string, state } : stage)
    : [...stages, { id: event.stage, label: event.label as string, state }];
  if (state !== 'active') return next;
  return next.map((stage): AIThinkingStage => stage.id === event.stage ? stage : stage.state === 'active' ? { ...stage, state: 'complete' } : stage);
}

export default function YatriWorkspace() {
  const { token } = useAuthStore();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [events, setEvents] = useState<AIEvent[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState('');
  const [thinkingStages, setThinkingStages] = useState<AIThinkingStage[]>(BASE_THINKING_STAGES);
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'error'>('idle');
  const voiceSupported = typeof window !== 'undefined' && Boolean((window as SpeechRecognitionWindow).SpeechRecognition || (window as SpeechRecognitionWindow).webkitSpeechRecognition);
  const abortRef = useRef<AbortController | null>(null);
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const streamAssistantIdRef = useRef<string | null>(null);

  const latestAssistantReply = useMemo(
    () => [...messages].reverse().find((message) => message.role === 'assistant' && message.content.trim())?.content ?? '',
    [messages],
  );
  const hasTrainResults = events.some((event) => event.type === 'train_results' || event.type === 'recommendation');

  const loadConversations = useCallback(async () => {
    if (!token) return;
    setHistoryLoading(true);
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations`);
      if (!response.ok) throw await readApiError(response);
      const payload = unwrapPayload<ConversationSummary[]>(await response.json() as ApiPayload<ConversationSummary[]>);
      setConversations(Array.isArray(payload) ? payload : []);
    } catch (caught) {
      if (caught instanceof Error) setError(caught.message);
    } finally {
      setHistoryLoading(false);
    }
  }, [token]);

  useEffect(() => {
    const hydrationTimer = window.setTimeout(() => { void loadConversations(); }, 0);
    return () => {
      window.clearTimeout(hydrationTimer);
      abortRef.current?.abort();
      recognitionRef.current?.abort();
    };
  }, [loadConversations]);

  const loadConversation = useCallback(async (id: string) => {
    if (running) return;
    setHistoryLoading(true);
    setError('');
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations/${id}`);
      if (!response.ok) throw await readApiError(response);
      const detail = unwrapPayload<ConversationDetail>(await response.json() as ApiPayload<ConversationDetail>);
      setConversationId(detail.id);
      setMessages(mapMessages(detail.messages ?? []));
      setEvents([]);
      setThinkingStages(BASE_THINKING_STAGES);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load this conversation.');
    } finally {
      setHistoryLoading(false);
    }
  }, [running]);

  const createConversation = useCallback(async (message: string) => {
    const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary: `Yatri: ${message.slice(0, 42)}` }),
    });
    if (!response.ok) throw await readApiError(response);
    const payload = unwrapPayload<{ id?: string }>(await response.json() as ApiPayload<{ id?: string }>);
    if (!payload.id) throw new Error('Conversation ID missing.');
    setConversationId(payload.id);
    return payload.id;
  }, []);

  const startNewConversation = () => {
    if (running) return;
    setConversationId(null);
    setMessages([]);
    setEvents([]);
    setError('');
    setThinkingStages(BASE_THINKING_STAGES);
  };

  const updateAssistantMessage = useCallback((content: string) => {
    const messageId = streamAssistantIdRef.current;
    if (!messageId) return;
    setMessages((current) => current.map((message) => message.id === messageId ? { ...message, content } : message));
  }, []);

  const sendMessage = useCallback(async (message: string) => {
    const trimmed = message.trim();
    if (!trimmed || running) return;
    setInput('');
    setError('');
    setEvents([]);
    setThinkingStages(BASE_THINKING_STAGES.map((stage, index) => ({ ...stage, state: index === 0 ? 'active' : 'pending' })));
    setRunning(true);
    const controller = new AbortController();
    abortRef.current = controller;
    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;
    streamAssistantIdRef.current = assistantMessageId;
    setMessages((current) => [...current, { id: userMessageId, role: 'user', content: trimmed, timestamp: new Date().toISOString() }, { id: assistantMessageId, role: 'assistant', content: '', timestamp: new Date().toISOString() }]);
    const timeout = window.setTimeout(() => controller.abort(), 70000);
    let streamedText = '';
    let receivedDone = false;

    try {
      const id = conversationId ?? await createConversation(trimmed);
      const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations/${id}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, context: { current_page: '/chat', surface: 'yatri-command-center' } }),
        signal: controller.signal,
      });
      if (!response.ok) throw await readApiError(response);
      if (!response.body) throw new Error('Yatri returned no stream.');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processFrame = (raw: string) => {
        const event = parseAIEvent(raw);
        if (!event) {
          setError('Yatri returned an unreadable event. Please try again.');
          return;
        }
        setEvents((current) => [...current.slice(-30), event]);
        if (event.type === 'thinking') {
          setThinkingStages((current) => updateThinkingStage(current, event));
        } else if (event.type === 'token' && typeof event.value === 'string') {
          streamedText += event.value;
          updateAssistantMessage(streamedText);
        } else if (event.type === 'message' && typeof event.message === 'string' && !streamedText) {
          streamedText = event.message;
          updateAssistantMessage(streamedText);
        } else if (event.type === 'done') {
          receivedDone = true;
          if (typeof event.reply === 'string') {
            streamedText = event.reply;
            updateAssistantMessage(event.reply);
          }
          if (event.status === 'error') setError('Yatri could not complete that request. Please try again.');
        } else if (event.type === 'error') {
          setThinkingStages((current) => current.map((stage) => stage.state === 'active' ? { ...stage, state: 'error' } : stage));
          setError(friendlyAIError(event));
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const [frames, remainder] = parseSSEBuffer(buffer);
        buffer = remainder;
        frames.forEach((frame) => processFrame(frame.data));
      }
      buffer += decoder.decode();
      const [finalFrames] = parseSSEBuffer(buffer);
      finalFrames.forEach((frame) => processFrame(frame.data));
      if (!receivedDone && !controller.signal.aborted) throw new Error('Yatri ended the stream before completing the response.');
      await loadConversations();
    } catch (caught) {
      if (!controller.signal.aborted) {
        const messageText = caught instanceof Error ? caught.message : 'Yatri could not complete that request.';
        setError(messageText);
        updateAssistantMessage('Yatri could not complete that request. Please try again.');
      }
    } finally {
      window.clearTimeout(timeout);
      abortRef.current = null;
      streamAssistantIdRef.current = null;
      setRunning(false);
    }
  }, [conversationId, createConversation, loadConversations, running, updateAssistantMessage]);

  const toggleVoice = () => {
    if (!voiceSupported) {
      setVoiceState('error');
      setError('Voice capture is not available in this browser. You can still type to Yatri.');
      return;
    }
    if (voiceState === 'listening') {
      recognitionRef.current?.stop();
      return;
    }
    const Recognition = (window as SpeechRecognitionWindow).SpeechRecognition || (window as SpeechRecognitionWindow).webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceState('error');
      setError('Voice capture is not available in this browser. You can still type to Yatri.');
      return;
    }
    const recognition = new Recognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onstart = () => setVoiceState('listening');
    recognition.onresult = (event: SpeechRecognitionEventLike) => {
      const transcript = Array.from(event.results).map((result) => result[0]?.transcript ?? '').join('');
      setInput(transcript);
    };
    recognition.onerror = () => {
      setVoiceState('error');
      setError('Voice capture could not start. Check microphone permission or type instead.');
    };
    recognition.onend = () => setVoiceState('idle');
    recognitionRef.current = recognition;
    setError('');
    recognition.start();
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void sendMessage(input);
  };
  const stop = () => abortRef.current?.abort();

  return <PageFrame><main className="mx-auto min-h-[calc(100vh-72px)] max-w-[1440px] px-5 py-8 sm:px-8 lg:px-12 lg:py-12"><div className="grid gap-8 lg:grid-cols-[1fr_360px]"><section className="min-w-0"><div className="mb-8 flex items-center justify-between"><div><p className="eyebrow text-[#9a6b28]">AI travel command center</p><p className="mt-2 text-sm text-[#718094]">A calm place to turn an intention into a journey.</p></div><span className="hidden items-center gap-2 rounded-full border border-[#d7e9de] bg-[#f0f8f2] px-3 py-2 text-xs font-medium text-[#28714b] sm:flex"><span className="h-2 w-2 animate-pulse rounded-full bg-[#5ea77b]" />Yatri online</span></div><div className="relative overflow-hidden rounded-[30px] bg-[#0f2b43] px-6 py-12 text-white sm:px-12 sm:py-16"><div className="absolute -right-16 -top-20 h-72 w-72 rounded-full border-[35px] border-[#e7b75e]/10" /><div className="relative max-w-2xl"><div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#e7b75e] text-[#07111f]"><Sparkles className="h-6 w-6" /></div><h1 className="font-serif text-5xl font-semibold leading-[.98] tracking-[-.055em] sm:text-6xl">{running ? 'Let’s make sense of it.' : latestAssistantReply ? 'Here is what I found.' : 'Good evening. What are we planning?'}</h1><p className="mt-6 max-w-xl text-base leading-7 text-white/65">{running ? 'Yatri is checking the signals that make a journey feel predictable.' : latestAssistantReply ? 'You can act on the result directly, or ask Yatri to look at it from another angle.' : 'Tell Yatri anything about the journey you have in mind. You do not need to know the station codes.'}</p></div></div>{running && <div className="mt-5"><AIThinking stages={thinkingStages} /></div>}{error && <div className="mt-5 flex items-start justify-between gap-4 rounded-2xl border border-[#ecc5be] bg-[#fff5f2] p-4 text-sm text-[#9f4941]"><div><p className="font-semibold">Yatri could not complete that request.</p><p className="mt-1 text-xs">{error}</p></div><button type="button" onClick={() => setError('')} aria-label="Dismiss error"><X className="h-4 w-4" /></button></div>}{messages.length > 0 && <div className="mt-5 space-y-3 rounded-[24px] border border-[#e2ddd3] bg-white p-5 shadow-[0_12px_35px_rgba(21,35,56,.06)]"><div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.15em] text-[#9a6b28]"><Sparkles className="h-3.5 w-3.5" />Conversation</div>{messages.slice(-8).map((message) => <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}><div className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === 'user' ? 'rounded-br-md bg-[#152338] text-white' : 'rounded-bl-md bg-[#f5f1e8] text-[#33445a]'}`}>{message.content || (running && message.id === messages[messages.length - 1]?.id ? 'Yatri is preparing a response…' : '')}</div></div>)}</div>}{hasTrainResults && <div className="mt-5 grid gap-4 sm:grid-cols-2"><TrainCard recommended compact /><TrainCard compact train={{ name: 'Gondwana Express', number: '12409', from: 'BSP', to: 'NZM', departure: '20:15', arrival: '11:10', duration: '14h 55m', fare: '₹1,820', confirmation: '86%', delay: '81%', reliability: 'Reliable' }} /></div>}{latestAssistantReply && <div className="mt-5 rounded-[24px] border border-[#e2ddd3] bg-white p-5 shadow-[0_12px_35px_rgba(21,35,56,.06)]"><div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.15em] text-[#9a6b28]"><Sparkles className="h-3.5 w-3.5" />Latest answer</div><p className="mt-4 whitespace-pre-wrap text-[15px] leading-7 text-[#33445a]">{latestAssistantReply}</p><div className="mt-6 flex flex-wrap gap-2 border-t border-[#eee9df] pt-4"><button type="button" onClick={() => void sendMessage('Compare the alternatives and explain the trade-offs.')} className="flex min-h-10 items-center gap-2 rounded-full bg-[#152338] px-4 text-xs font-semibold text-white">Compare options <ChevronRight className="h-3.5 w-3.5" /></button><button type="button" onClick={() => void sendMessage('Find a cheaper alternative.')} className="flex min-h-10 items-center gap-2 rounded-full border border-[#dcd5c9] px-4 text-xs font-semibold">Find cheaper <ArrowRight className="h-3.5 w-3.5" /></button></div></div>}{running && <button type="button" onClick={stop} className="mx-auto mt-3 flex items-center gap-2 text-xs font-semibold text-[#9f4941]"><Pause className="h-3.5 w-3.5" />Stop response</button>}<form onSubmit={submit} className="mt-6 rounded-[24px] border border-[#d9d3c8] bg-white p-2 shadow-[0_12px_35px_rgba(21,35,56,.07)]"><div className="flex items-end gap-2"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void sendMessage(input); } }} rows={2} placeholder="Tell Yatri anything..." className="min-h-14 flex-1 resize-none bg-transparent px-3 py-3 text-sm leading-6 outline-none placeholder:text-[#9ca6b3]" aria-label="Message Yatri" /><button type="button" onClick={toggleVoice} disabled={running || !voiceSupported} className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl transition ${voiceState === 'listening' ? 'bg-[#e7b75e] text-[#07111f]' : 'border border-[#e2ddd3] text-[#647185] hover:bg-[#f5f1e8] disabled:cursor-not-allowed disabled:opacity-45'}`} aria-label={voiceSupported ? (voiceState === 'listening' ? 'Stop voice input' : 'Start voice input') : 'Voice input unavailable'} title={voiceSupported ? 'Use voice input' : 'Voice input is unavailable in this browser'}><Mic className="h-4 w-4" /></button><button type="submit" disabled={!input.trim() || running} className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#152338] text-white transition hover:bg-[#254263] disabled:cursor-not-allowed disabled:opacity-35" aria-label="Send to Yatri"><ArrowRight className="h-4 w-4" /></button></div></form></section><aside className="space-y-5"><div className="rounded-[24px] border border-[#e2ddd3] bg-white p-5"><div className="flex items-start justify-between gap-3"><div><p className="eyebrow text-[#9a6b28]">Your conversations</p><h2 className="mt-2 font-serif text-2xl font-semibold">Travel memory</h2></div><button type="button" onClick={startNewConversation} disabled={running} className="grid h-9 w-9 place-items-center rounded-full border border-[#dcd5c9] text-[#647185] transition hover:bg-[#f5f1e8] disabled:opacity-40" aria-label="Start new conversation" title="Start new conversation"><Plus className="h-4 w-4" /></button></div><div className="mt-4 space-y-1">{historyLoading && <p className="px-2 py-3 text-xs text-[#7d8898]">Loading your conversations…</p>}{!historyLoading && conversations.length === 0 && <p className="px-2 py-3 text-xs leading-5 text-[#7d8898]">Your saved Yatri conversations will appear here.</p>}{conversations.slice(0, 6).map((conversation) => <button key={conversation.id} type="button" onClick={() => void loadConversation(conversation.id)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left transition ${conversation.id === conversationId ? 'bg-[#f5f1e8]' : 'hover:bg-[#faf8f3]'}`}><span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[#edf4f7] text-[#2e6f90]"><RotateCcw className="h-4 w-4" /></span><span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold text-[#34465b]">{conversation.summary || 'Yatri conversation'}</span><span className="mt-1 block text-[10px] text-[#9ca6b3]">{formatConversationDate(conversation.updatedAt)}</span></span><ChevronRight className="h-3.5 w-3.5 text-[#a2abb6]" /></button>)}</div></div><div className="rounded-[24px] border border-[#e2ddd3] bg-white p-5"><p className="eyebrow text-[#9a6b28]">Start with a move</p><h2 className="mt-2 font-serif text-2xl font-semibold">What can Yatri do?</h2><div className="mt-4 space-y-2">{QUICK_ACTIONS.map(({ label, prompt, icon: Icon }) => <button key={label} type="button" onClick={() => void sendMessage(prompt)} className="group flex min-h-12 w-full items-center gap-3 rounded-xl border border-transparent px-3 text-left text-sm text-[#34465b] transition hover:border-[#e2ddd3] hover:bg-[#faf8f3]"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#edf4f7] text-[#2e6f90]"><Icon className="h-4 w-4" /></span><span className="flex-1">{label}</span><ChevronRight className="h-4 w-4 text-[#a2abb6] transition group-hover:translate-x-0.5" /></button>)}</div></div><div className="rounded-[24px] border border-[#d6e4eb] bg-[#f1f8fb] p-5"><div className="flex items-center gap-2 text-sm font-semibold"><span className="grid h-8 w-8 place-items-center rounded-full bg-white text-[#2e6f90]"><Check className="h-4 w-4" /></span>How Yatri thinks</div><p className="mt-3 text-xs leading-5 text-[#657b8d]">Yatri shows the stages it actually receives from the railway intelligence service. Heartbeats keep the connection alive without pretending new work happened.</p></div><div className="rounded-[24px] bg-[#eee8dc] p-5"><div className="flex items-center gap-2 text-sm font-semibold"><RotateCcw className="h-4 w-4 text-[#9a6b28]" />Your context stays yours</div><p className="mt-3 text-xs leading-5 text-[#718094]">Yatri labels estimates and live signals clearly. No opaque scores, no invented railway updates.</p></div></aside></div></main></PageFrame>;
}
