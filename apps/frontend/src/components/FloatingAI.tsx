'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Sparkles, X, Send, Bot, User as UserIcon, Train, Calendar, TrendingUp, RefreshCw } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { API_BASE_URL, authenticatedFetch } from '../lib/api';
import { parseSSEBuffer } from '../lib/sse';
import MarkdownMessage from './MarkdownMessage';

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

const TEMPORARY_ERROR = 'RailYatra AI is temporarily unavailable. Please try again in a moment.';

export default function FloatingAI() {
  const { token, user } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [lastFailedQuery, setLastFailedQuery] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const createConversation = useCallback(async () => {
    if (!token) return null;

    setInitializing(true);
    setError(null);
    try {
      const response = await authenticatedFetch(`${API_BASE_URL}/api/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ summary: 'Quick Assist Session' }),
      });

      if (!response.ok) {
        throw new Error(`Conversation creation failed (${response.status})`);
      }

      const data = await response.json() as { id?: string; data?: { id?: string } };
      const conversationId = data.id ?? data.data?.id;
      if (!conversationId) throw new Error('Conversation ID missing from response');

      setActiveConversationId(conversationId);
      return conversationId;
    } catch (err) {
      console.error('Failed to create quick assist session:', err);
      setError(TEMPORARY_ERROR);
      return null;
    } finally {
      setInitializing(false);
    }
  }, [token]);

  const ensureConversation = useCallback(async () => {
    return activeConversationId ?? createConversation();
  }, [activeConversationId, createConversation]);

  const handleOpen = async () => {
    setIsOpen(true);
    if (!activeConversationId) {
      await createConversation();
    }
  };

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim() || loading) return;

    const conversationId = await ensureConversation();
    if (!conversationId) return;

    setError(null);
    setLastFailedQuery(null);
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setMessage('');
    setLoading(true);

    // Reserve the assistant slot before the stream begins so every token
    // updates the same message instead of appending duplicate bubbles.
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    let accumulatedContent = '';
    let receivedDone = false;

    const updateAssistantMessage = (content: string) => {
      setMessages(prev => {
        const updated = [...prev];
        const last = updated.length - 1;
        if (last >= 0 && updated[last].role === 'assistant') {
          updated[last] = { ...updated[last], content };
        }
        return updated;
      });
    };

    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/api/conversations/${conversationId}/chat`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: query,
            context: { current_page: window.location.pathname },
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`AI request failed (${response.status})`);
      }
      if (!response.body) throw new Error('Readable stream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processEvent = (rawData: string) => {
        const data = JSON.parse(rawData) as {
          type?: string;
          value?: string;
          reply?: string;
          message?: string;
        };

        if (data.type === 'token' && typeof data.value === 'string') {
          accumulatedContent += data.value;
          updateAssistantMessage(accumulatedContent);
          return;
        }

        if (data.type === 'done') {
          receivedDone = true;
          if (typeof data.reply === 'string' && data.reply !== accumulatedContent) {
            accumulatedContent = data.reply;
            updateAssistantMessage(accumulatedContent);
          }
          return;
        }

        if (data.type === 'error') {
          throw new Error(data.message || TEMPORARY_ERROR);
        }
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

      if (!receivedDone && !accumulatedContent.trim()) {
        throw new Error(TEMPORARY_ERROR);
      }
    } catch (err) {
      console.error('Floating AI chat failed:', err);
      setError(TEMPORARY_ERROR);
      setLastFailedQuery(query);
      setMessages(prev => {
        const updated = [...prev];
        const last = updated.length - 1;
        if (last >= 0 && updated[last].role === 'assistant') {
          updated[last] = { role: 'assistant', content: TEMPORARY_ERROR };
        }
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }, [ensureConversation, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendMessage(message.trim());
  };

  const retryLastMessage = async () => {
    if (!lastFailedQuery || loading) return;
    setMessages(prev => prev.slice(0, -1));
    await sendMessage(lastFailedQuery);
  };

  if (!user || !token) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {isOpen && (
        <div className="mb-4 flex h-[500px] w-96 flex-col overflow-hidden rounded-2xl border border-border bg-background/95 shadow-2xl backdrop-blur-md">
          <div className="flex items-center justify-between bg-gradient-to-r from-primary to-secondary p-4 text-primary-foreground">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 animate-pulse" />
              <div>
                <h4 className="text-sm font-bold">RailYatra AI Assistant</h4>
                <p className="text-[10px] opacity-80">Real-time Travel Intelligence</p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="cursor-pointer rounded-lg p-1 hover:bg-white/10" aria-label="Close assistant">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex gap-2 overflow-x-auto border-b border-border bg-muted/30 px-4 py-2 text-[10px]">
            <span className="flex items-center gap-1 whitespace-nowrap rounded bg-primary/10 px-2 py-1 font-medium text-primary"><Train className="h-3 w-3" /> Search Trains</span>
            <span className="flex items-center gap-1 whitespace-nowrap rounded bg-secondary/10 px-2 py-1 font-medium text-secondary"><TrendingUp className="h-3 w-3" /> PNR Predictor</span>
            <span className="flex items-center gap-1 whitespace-nowrap rounded bg-warning/10 px-2 py-1 font-medium text-warning"><Calendar className="h-3 w-3" /> Tatkal Window</span>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center space-y-3 p-6 text-center">
                {initializing ? <RefreshCw className="h-10 w-10 animate-spin text-primary" /> : <Bot className="h-10 w-10 text-primary" />}
                <p className="text-sm font-medium text-foreground">{initializing ? 'Starting your AI session…' : 'How can I assist you today?'}</p>
                <p className="text-xs text-muted-foreground">Ask me about train itineraries, check a PNR, estimate fares, or compare seats.</p>
                {error && <p className="max-w-[280px] text-xs text-destructive">{error}</p>}
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((msg, index) => (
                  <div key={index} className={`flex max-w-[90%] gap-2.5 ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
                    <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'}`}>
                      {msg.role === 'user' ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>
                    <div className={`rounded-2xl p-3 text-sm ${msg.role === 'user' ? 'rounded-tr-none bg-primary text-primary-foreground' : 'rounded-tl-none border border-border bg-muted/50 text-foreground'}`}>
                      {msg.role === 'assistant' ? <MarkdownMessage content={msg.content} /> : <span className="whitespace-pre-wrap">{msg.content}</span>}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="mr-auto flex max-w-[80%] gap-2.5">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted"><Bot className="h-4 w-4 animate-bounce" /></div>
                    <div className="flex items-center gap-1 rounded-2xl rounded-tl-none border border-border bg-muted/50 p-3">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/30 [animation-delay:-0.3s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/30 [animation-delay:-0.15s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-foreground/30" />
                    </div>
                  </div>
                )}

                {error && !loading && lastFailedQuery && (
                  <button onClick={retryLastMessage} className="ml-9 flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-medium hover:bg-muted" type="button">
                    <RefreshCw className="h-3.5 w-3.5" /> Retry
                  </button>
                )}
                <div ref={chatEndRef} />
              </div>
            )}
          </div>

          <form onSubmit={handleSend} className="flex gap-2 border-t border-border bg-background p-3">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask RailYatra AI..."
              disabled={loading || initializing}
              className="flex-1 rounded-xl border border-border bg-background px-4 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-60"
            />
            <button type="submit" disabled={loading || initializing || !message.trim()} className="cursor-pointer rounded-xl bg-primary p-2 text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50" aria-label="Send message">
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}

      <button onClick={isOpen ? () => setIsOpen(false) : handleOpen} className="group flex h-14 w-14 cursor-pointer items-center justify-center rounded-full bg-gradient-to-r from-primary to-secondary text-primary-foreground shadow-premium transition-transform duration-200 hover:scale-105" aria-label={isOpen ? 'Close AI assistant' : 'Open AI assistant'}>
        {isOpen ? <X className="h-6 w-6" /> : <Sparkles className="h-6 w-6 transition-transform group-hover:rotate-12" />}
      </button>
    </div>
  );
}
