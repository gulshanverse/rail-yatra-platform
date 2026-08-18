'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, ChevronRight, Mic, Pause, RotateCcw, Search, Sparkles, Ticket, TrainFront, X } from 'lucide-react';
import { API_BASE_URL, authenticatedFetch } from '@/lib/api';
import { friendlyAIError, parseAIEvent, parseSSEBuffer, type AIEvent } from '@/lib/sse';
import { AIThinking, PageFrame, TrainCard } from '@/components/railyatra/railyatra-ui';

const QUICK_ACTIONS = [
  { label: 'Find trains', prompt: 'Find the most reliable train from Bilaspur to Delhi tomorrow.', icon: TrainFront },
  { label: 'Plan a trip', prompt: 'Plan a thoughtful three-day trip from Bilaspur to Goa next weekend.', icon: Search },
  { label: 'Check PNR', prompt: 'Check the status of my PNR and explain what the confirmation probability means.', icon: Ticket },
  { label: 'Track train', prompt: 'Track my train and tell me what is next at the station.', icon: ArrowRight },
  { label: 'Find cheaper alternatives', prompt: 'Find a cheaper alternative with a similar arrival time.', icon: Sparkles },
];

interface ConversationResponse { id?: string; }

export default function YatriWorkspace() {
  const [input, setInput] = useState('');
  const [reply, setReply] = useState('');
  const [events, setEvents] = useState<AIEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'processing' | 'responding' | 'error'>('idle');

  useEffect(() => () => abortRef.current?.abort(), []);

  const startConversation = async (message: string) => {
    if (conversationId) return conversationId;
    const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ summary: `Yatri: ${message.slice(0, 42)}` }) });
    if (!response.ok) throw new Error('Could not start a Yatri workspace.');
    const data = await response.json() as ConversationResponse;
    if (!data.id) throw new Error('Conversation ID missing.');
    setConversationId(data.id);
    return data.id;
  };

  const sendMessage = async (message: string) => {
    const trimmed = message.trim();
    if (!trimmed || running) return;
    setInput(''); setReply(''); setEvents([]); setError(''); setRunning(true);
    const controller = new AbortController(); abortRef.current = controller;
    const timeout = window.setTimeout(() => controller.abort(), 70000);
    try {
      const id = await startConversation(trimmed);
      const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations/${id}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: trimmed, context: { current_page: '/chat', surface: 'yatri-command-center' } }), signal: controller.signal });
      if (!response.ok) throw new Error('Yatri could not reach the railway service.');
      if (!response.body) throw new Error('Yatri returned no stream.');
      const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = '';
      const process = (raw: string) => {
        const event = parseAIEvent(raw); if (!event) { setError('Yatri returned an unreadable event. Please try again.'); return; }
        setEvents((current) => [...current.slice(-30), event]);
        if (event.type === 'token' && typeof event.value === 'string') setReply((current) => current + event.value);
        if (event.type === 'message' && typeof event.message === 'string') setReply((current) => current ? `${current}\n\n${event.message}` : event.message as string);
        if (event.type === 'done' && typeof event.reply === 'string') setReply(event.reply);
        if (event.type === 'error') setError(friendlyAIError(event));
      };
      while (true) {
        const { done, value } = await reader.read(); if (done) break;
        buffer += decoder.decode(value, { stream: true }); const [frames, remainder] = parseSSEBuffer(buffer); buffer = remainder; frames.forEach((frame) => process(frame.data));
      }
      buffer += decoder.decode(); const [finalFrames] = parseSSEBuffer(buffer); finalFrames.forEach((frame) => process(frame.data));
    } catch (caught) {
      if (!controller.signal.aborted) setError(caught instanceof Error ? caught.message : 'Yatri could not complete that request.');
    } finally { window.clearTimeout(timeout); abortRef.current = null; setRunning(false); setVoiceState('idle'); }
  };

  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); void sendMessage(input); };
  const stop = () => { abortRef.current?.abort(); setRunning(false); };
  const voice = () => { if (voiceState === 'listening') { setVoiceState('processing'); window.setTimeout(() => setVoiceState('idle'), 800); } else setVoiceState('listening'); };
  const visibleStages = ['Understanding your request', 'Searching trains', 'Checking availability', 'Comparing reliability', 'Finding alternatives'];
  const stageIndex = events.some((event) => event.type === 'done') ? 5 : events.length > 0 ? Math.min(4, events.length) : 0;

  return <PageFrame><main className="mx-auto min-h-[calc(100vh-72px)] max-w-[1440px] px-5 py-8 sm:px-8 lg:px-12 lg:py-12"><div className="grid gap-8 lg:grid-cols-[1fr_360px]"><section className="min-w-0"><div className="mb-8 flex items-center justify-between"><div><p className="eyebrow text-[#9a6b28]">AI travel command center</p><p className="mt-2 text-sm text-[#718094]">A calm place to turn an intention into a journey.</p></div><span className="hidden items-center gap-2 rounded-full border border-[#d7e9de] bg-[#f0f8f2] px-3 py-2 text-xs font-medium text-[#28714b] sm:flex"><span className="h-2 w-2 animate-pulse rounded-full bg-[#5ea77b]" />Yatri online</span></div><div className="relative overflow-hidden rounded-[30px] bg-[#0f2b43] px-6 py-12 text-white sm:px-12 sm:py-16"><div className="absolute -right-16 -top-20 h-72 w-72 rounded-full border-[35px] border-[#e7b75e]/10" /><div className="relative max-w-2xl"><div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#e7b75e] text-[#07111f]"><Sparkles className="h-6 w-6" /></div><h1 className="font-serif text-5xl font-semibold leading-[.98] tracking-[-.055em] sm:text-6xl">{running ? 'Let’s make sense of it.' : reply ? 'Here is what I found.' : 'Good evening. What are we planning?'}</h1><p className="mt-6 max-w-xl text-base leading-7 text-white/65">{running ? 'Yatri is checking the signals that make a journey feel predictable.' : reply ? 'You can act on the result directly, or ask Yatri to look at it from another angle.' : 'Tell Yatri anything about the journey you have in mind. You do not need to know the station codes.'}</p></div></div>{running && <div className="mt-5"><AIThinking active={Math.min(3, stageIndex)} /></div>}{error && <div className="mt-5 flex items-start justify-between gap-4 rounded-2xl border border-[#ecc5be] bg-[#fff5f2] p-4 text-sm text-[#9f4941]"><div><p className="font-semibold">Yatri couldn’t reach the railway service.</p><p className="mt-1 text-xs">{error}</p></div><button type="button" onClick={() => setError('')} aria-label="Dismiss error"><X className="h-4 w-4" /></button></div>}{reply && <div className="mt-5 rounded-[24px] border border-[#e2ddd3] bg-white p-5 shadow-[0_12px_35px_rgba(21,35,56,.06)]"><div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.15em] text-[#9a6b28]"><Sparkles className="h-3.5 w-3.5" />Yatri says</div><p className="mt-4 whitespace-pre-wrap text-[15px] leading-7 text-[#33445a]">{reply}</p><div className="mt-6 flex flex-wrap gap-2 border-t border-[#eee9df] pt-4"><button type="button" onClick={() => void sendMessage('Compare the alternatives and explain the trade-offs.')} className="flex min-h-10 items-center gap-2 rounded-full bg-[#152338] px-4 text-xs font-semibold text-white">Compare options <ChevronRight className="h-3.5 w-3.5" /></button><button type="button" onClick={() => void sendMessage('Find a cheaper alternative.')} className="flex min-h-10 items-center gap-2 rounded-full border border-[#dcd5c9] px-4 text-xs font-semibold">Find cheaper <ArrowRight className="h-3.5 w-3.5" /></button></div></div>}{events.some((event) => event.type === 'train_results' || event.type === 'recommendation' || event.type === 'done') && <div className="mt-5 grid gap-4 sm:grid-cols-2"><TrainCard recommended compact /><TrainCard compact train={{ name: 'Gondwana Express', number: '12409', from: 'BSP', to: 'NZM', departure: '20:15', arrival: '11:10', duration: '14h 55m', fare: '₹1,820', confirmation: '86%', delay: '81%', reliability: 'Reliable' }} /></div>}<form onSubmit={submit} className="mt-6 rounded-[24px] border border-[#d9d3c8] bg-white p-2 shadow-[0_12px_35px_rgba(21,35,56,.07)]"><div className="flex items-end gap-2"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void sendMessage(input); } }} rows={2} placeholder="Tell Yatri anything..." className="min-h-14 flex-1 resize-none bg-transparent px-3 py-3 text-sm leading-6 outline-none placeholder:text-[#9ca6b3]" aria-label="Message Yatri" /><button type="button" onClick={voice} className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl transition ${voiceState === 'listening' ? 'bg-[#e7b75e] text-[#07111f]' : 'border border-[#e2ddd3] text-[#647185] hover:bg-[#f5f1e8]'}`} aria-label={voiceState === 'listening' ? 'Stop voice input' : 'Start voice input'}><Mic className="h-4 w-4" /></button><button type="submit" disabled={!input.trim() || running} className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[#152338] text-white transition hover:bg-[#254263] disabled:cursor-not-allowed disabled:opacity-35" aria-label="Send to Yatri"><ArrowRight className="h-4 w-4" /></button></div></form>{running && <button type="button" onClick={stop} className="mx-auto mt-3 flex items-center gap-2 text-xs font-semibold text-[#9f4941]"><Pause className="h-3.5 w-3.5" />Stop response</button>}</section><aside className="space-y-5"><div className="rounded-[24px] border border-[#e2ddd3] bg-white p-5"><p className="eyebrow text-[#9a6b28]">Start with a move</p><h2 className="mt-2 font-serif text-2xl font-semibold">What can Yatri do?</h2><div className="mt-4 space-y-2">{QUICK_ACTIONS.map(({ label, prompt, icon: Icon }) => <button key={label} type="button" onClick={() => void sendMessage(prompt)} className="group flex min-h-12 w-full items-center gap-3 rounded-xl border border-transparent px-3 text-left text-sm text-[#34465b] transition hover:border-[#e2ddd3] hover:bg-[#faf8f3]"><span className="grid h-8 w-8 place-items-center rounded-lg bg-[#edf4f7] text-[#2e6f90]"><Icon className="h-4 w-4" /></span><span className="flex-1">{label}</span><ChevronRight className="h-4 w-4 text-[#a2abb6] transition group-hover:translate-x-0.5" /></button>)}</div></div><div className="rounded-[24px] border border-[#d6e4eb] bg-[#f1f8fb] p-5"><div className="flex items-center gap-2 text-sm font-semibold"><span className="grid h-8 w-8 place-items-center rounded-full bg-white text-[#2e6f90]"><Check className="h-4 w-4" /></span>How Yatri thinks</div><ul className="mt-4 space-y-3 text-xs leading-5 text-[#657b8d]">{visibleStages.map((stage, index) => <li key={stage} className="flex items-center gap-2"><span className={`h-1.5 w-1.5 rounded-full ${index < stageIndex ? 'bg-[#5ea77b]' : 'bg-[#b9ccd6]'}`} />{stage}</li>)}</ul></div><div className="rounded-[24px] bg-[#eee8dc] p-5"><div className="flex items-center gap-2 text-sm font-semibold"><RotateCcw className="h-4 w-4 text-[#9a6b28]" />Your context stays yours</div><p className="mt-3 text-xs leading-5 text-[#718094]">Yatri labels estimates and live signals clearly. No opaque scores, no invented railway updates.</p></div></aside></div></main></PageFrame>;
}
