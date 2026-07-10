'use client';

import { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, Bot, User as UserIcon, Train, Calendar, TrendingUp } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function FloatingAI() {
  const { token, user } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  if (!user || !token) return null;

  const handleOpen = async () => {
    setIsOpen(true);
    if (!activeConversationId) {
      try {
        // Auto-create a chat session on open
        const res = await fetch('http://localhost:5000/api/conversations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ summary: 'Quick Assist Session' }),
        });
        const data = await res.json();
        if (data.id) {
          setActiveConversationId(data.id);
        }
      } catch (err) {
        console.error('Failed to create quick assist session', err);
      }
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !activeConversationId || loading) return;

    const userQuery = message.trim();
    setMessage('');
    setMessages(prev => [...prev, { role: 'user', content: userQuery }]);
    setLoading(true);

    try {
      const response = await fetch(`http://localhost:5000/api/conversations/${activeConversationId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userQuery,
          context: { current_page: window.location.pathname }
        }),
      });

      if (!response.body) throw new Error('Readable stream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      // Append an empty assistant response slot
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
      setLoading(false);

      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'token') {
                accumulatedContent += data.value;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: 'assistant',
                    content: accumulatedContent
                  };
                  return updated;
                });
              }
            } catch (err) {
              // Ignore boundary parser errors
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered a communication error with the RailYatra AI service.' }
      ]);
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Floating Panel */}
      {isOpen && (
        <div className="mb-4 w-96 h-[500px] rounded-2xl border border-border bg-background/95 backdrop-blur-md shadow-2xl flex flex-col overflow-hidden transition-all duration-300 transform translate-y-0 scale-100">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-primary to-secondary text-primary-foreground flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 animate-pulse" />
              <div>
                <h4 className="font-bold text-sm">RailYatra AI Assistant</h4>
                <p className="text-[10px] opacity-80">Real-time Travel Intelligence</p>
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Quick Stats Panel (Floating Assistant Utility) */}
          <div className="px-4 py-2 border-b border-border bg-muted/30 flex gap-2 overflow-x-auto text-[10px]">
            <span className="px-2 py-1 rounded bg-primary/10 text-primary flex items-center gap-1 font-medium whitespace-nowrap">
              <Train className="h-3 w-3" /> Search Trains
            </span>
            <span className="px-2 py-1 rounded bg-secondary/10 text-secondary flex items-center gap-1 font-medium whitespace-nowrap">
              <TrendingUp className="h-3 w-3" /> PNR Predictor
            </span>
            <span className="px-2 py-1 rounded bg-warning/10 text-warning flex items-center gap-1 font-medium whitespace-nowrap">
              <Calendar className="h-3 w-3" /> Tatkal Window
            </span>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-3">
                <Bot className="h-10 w-10 text-primary" />
                <p className="text-sm font-medium text-foreground">How can I assist you today?</p>
                <p className="text-xs text-muted-foreground">
                  Ask me about train itineraries, check a PNR, estimate fares, or compare seats.
                </p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div 
                  key={index}
                  className={`flex gap-2.5 max-w-[85%] ${
                    msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                  }`}
                >
                  <div className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 ${
                    msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
                  }`}>
                    {msg.role === 'user' ? <UserIcon className="h-4.5 w-4.5" /> : <Bot className="h-4.5 w-4.5" />}
                  </div>
                  <div className={`p-3 rounded-2xl text-sm ${
                    msg.role === 'user' 
                      ? 'bg-primary text-primary-foreground rounded-tr-none' 
                      : 'bg-muted/50 border border-border text-foreground rounded-tl-none'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex gap-2.5 max-w-[80%] mr-auto">
                <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center shrink-0">
                  <Bot className="h-4.5 w-4.5 animate-bounce" />
                </div>
                <div className="p-3 rounded-2xl bg-muted/50 border border-border rounded-tl-none flex gap-1 items-center">
                  <span className="h-2 w-2 rounded-full bg-foreground/30 animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="h-2 w-2 rounded-full bg-foreground/30 animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="h-2 w-2 rounded-full bg-foreground/30 animate-bounce"></span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Footer */}
          <form onSubmit={handleSend} className="p-3 border-t border-border bg-background flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask RailYatra AI..."
              className="flex-1 px-4 py-2 border border-border rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary bg-background"
            />
            <button
              type="submit"
              disabled={loading || !message.trim()}
              className="p-2 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}

      {/* Launcher Button */}
      <button
        onClick={isOpen ? () => setIsOpen(false) : handleOpen}
        className="h-14 w-14 rounded-full bg-gradient-to-r from-primary to-secondary text-primary-foreground shadow-premium flex items-center justify-center hover:scale-105 transition-transform duration-200 cursor-pointer group"
      >
        {isOpen ? <X className="h-6 w-6" /> : <Sparkles className="h-6 w-6 group-hover:rotate-12 transition-transform" />}
      </button>
    </div>
  );
}
