'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { API_BASE_URL } from '../../lib/api';
import { parseSSEBuffer } from '../../lib/sse';
import { 
  Sparkles, 
  Send, 
  Bot, 
  User as UserIcon, 
  Plus, 
  Search, 
  Pin, 
  Trash2, 
  Edit3, 
  ArrowLeft,
  Check,
  X,
  Clock,
  Sliders,
  Gauge,
  Award,
  ChevronRight,
  Info,
  ShieldCheck,
  Database,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
}

interface Conversation {
  id: string;
  summary: string;
  createdAt: string;
  updatedAt: string;
}

interface TravelOption {
  train_number: string;
  train_name: string;
  source: string;
  destination: string;
  departure: string;
  arrival: string;
  duration: string;
  booking_class: string;
  fare: number;
  waitlist_status: string;
  predicted_delay_mins: number;
  confirmation_probability: number;
  overall_score: number;
  confidence_score: number;
  reason_codes: string[];
  advantages: string[];
  disadvantages: string[];
  reasoning: string;
  is_alternative_station?: boolean;
  original_boarding_station?: string;
  is_alternative_date?: boolean;
  original_journey_date?: string;
  journey_date: string;
  data_quality?: {
    provider: string;
    last_updated: number;
    data_age_secs: number;
    confidence: number;
    source_type: string;
  };
}

export default function AIWorkspace() {
  const { token, user } = useAuthStore();
  const router = useRouter();

  // Sidebar states
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [pinnedIds, setPinnedIds] = useState<string[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('railyatra_pinned_chats');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Active chat states
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(false);

  // Journey Cockpit states
  const [options, setOptions] = useState<TravelOption[]>([]);
  const [activeOptionIndex, setActiveOptionIndex] = useState<number | null>(null);
  const [weights, setWeights] = useState({
    comfort: 1.0,
    budget: 1.0,
    speed: 1.0,
    reliability: 1.0
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadConversations = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
  }, [token]);

  const loadActiveConversation = async (id: string) => {
    setActiveId(id);
    setLoading(true);
    setMessages([]);
    setOptions([]);
    setActiveOptionIndex(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (err) {
      console.error('Error loading messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const sendChatMessage = useCallback(async (convId: string, queryText: string) => {
    setMessages(prev => [...prev, { role: 'user', content: queryText }]);
    setStreaming(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${convId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: queryText }),
      });

      if (!response.body) throw new Error('Readable stream not supported');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';

      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      const updateAssistantMessage = (content: string) => {
        setMessages(prev => {
          const updated = [...prev];
          const index = updated.length - 1;
          if (index >= 0 && updated[index].role === 'assistant') {
            updated[index] = { ...updated[index], content };
          }
          return updated;
        });
      };

      const processEvent = (rawData: string) => {
        try {
          const data = JSON.parse(rawData) as {
            type?: string;
            value?: string;
            reply?: string;
            options?: TravelOption[];
            message?: string;
          };

          if (data.type === 'token' && typeof data.value === 'string') {
            accumulated += data.value;
            updateAssistantMessage(accumulated);
          } else if (data.type === 'done') {
            if (typeof data.reply === 'string' && data.reply !== accumulated) {
              accumulated = data.reply;
              updateAssistantMessage(accumulated);
            }
            if (Array.isArray(data.options) && data.options.length > 0) {
              setOptions(data.options);
              setActiveOptionIndex(0);
            }
          } else if (data.type === 'error') {
            throw new Error(data.message || 'AI stream failed');
          }
        } catch (error) {
          if (error instanceof SyntaxError) {
            console.warn('Ignoring malformed SSE payload');
          } else {
            throw error;
          }
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
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Connection to RailYatra AI service lost. Please verify your endpoints.' }
      ]);
    } finally {
      setStreaming(false);
      void loadConversations();
    }
  }, [token, loadConversations]);

  const handleNewChat = useCallback(async (initialQuery?: string) => {
    setOptions([]);
    setActiveOptionIndex(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ summary: initialQuery ? `Query: ${initialQuery.slice(0, 20)}...` : 'New Chat' }),
      });
      if (res.ok) {
        const newChat = await res.json();
        setConversations(prev => [newChat, ...prev]);
        setActiveId(newChat.id);
        setMessages([]);
        
        if (initialQuery) {
          setTimeout(() => {
            void sendChatMessage(newChat.id, initialQuery);
          }, 100);
        }
      }
    } catch (err) {
      console.error('Error creating chat:', err);
    }
  }, [token, sendChatMessage]);

  const handleSubmit = useCallback((e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || streaming) return;
    
    const userQuery = input.trim();
    setInput('');

    if (!activeId) {
      void handleNewChat(userQuery);
    } else {
      void sendChatMessage(activeId, userQuery);
    }
  }, [input, streaming, activeId, handleNewChat, sendChatMessage]);

  const handleRename = async (id: string) => {
    if (!editTitle.trim()) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ summary: editTitle }),
      });
      if (res.ok) {
        setConversations(prev => prev.map(c => c.id === id ? { ...c, summary: editTitle } : c));
        setEditingId(null);
      }
    } catch (err) {
      console.error('Error renaming chat:', err);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this chat session?')) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setConversations(prev => prev.filter(c => c.id !== id));
        if (activeId === id) {
          setActiveId(null);
          setMessages([]);
          setOptions([]);
          setActiveOptionIndex(null);
        }
      }
    } catch (err) {
      console.error('Error deleting chat:', err);
    }
  };

  const handleTogglePin = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    let updatedPins;
    if (pinnedIds.includes(id)) {
      updatedPins = pinnedIds.filter(pid => pid !== id);
    } else {
      updatedPins = [...pinnedIds, id];
    }
    setPinnedIds(updatedPins);
    localStorage.setItem('railyatra_pinned_chats', JSON.stringify(updatedPins));
  };

  // Redirect if not logged in
  useEffect(() => {
    if (!token) {
      router.push('/login');
    } else {
      const timer = setTimeout(() => {
        void loadConversations();
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [token, loadConversations, router]);

  // Keyboard Shortcuts (Ctrl+Enter, Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        handleNewChat();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [input, activeId, streaming, handleSubmit, handleNewChat]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Helper local subscore and overall scoring recalculators for dynamic weight adjustments
  const getComfortSub = (bookingClass: string) => {
    const map: Record<string, number> = { '1A': 100, '2A': 85, '3A': 75, 'CC': 65, 'SL': 30 };
    return map[bookingClass.toUpperCase()] || 50;
  };
  const getCostSub = (fare: number) => {
    const ratio = Math.min(1.0, fare / 2500);
    return Math.round(100.0 * (1.0 - (ratio * 0.8)));
  };
  const getSpeedSub = (duration: string) => {
    try {
      const parts = duration.split(' ');
      const h = parseFloat(parts[0].replace('h', ''));
      const m = parts[1] ? parseFloat(parts[1].replace('m', '')) : 0;
      const hours = h + m / 60;
      const avgSpeed = 500 / hours;
      return Math.round(Math.min(100, Math.max(10, (avgSpeed - 40) * (90/50))));
    } catch {
      return 60;
    }
  };
  const getReliabilitySub = (prob: number, delay: number) => {
    const delayPenalty = Math.min(50, (delay / 60) * 25);
    return Math.round(Math.max(0, (prob * 0.7) + (30 - delayPenalty)));
  };

  const getOverallScore = (opt: TravelOption) => {
    const sub = {
      comfort: getComfortSub(opt.booking_class),
      cost: getCostSub(opt.fare),
      speed: getSpeedSub(opt.duration),
      reliability: getReliabilitySub(opt.confirmation_probability, opt.predicted_delay_mins)
    };
    const w = {
      comfort: weights.comfort * 0.25,
      cost: weights.budget * 0.25,
      speed: weights.speed * 0.25,
      reliability: weights.reliability * 0.25
    };
    const sumW = w.comfort + w.cost + w.speed + w.reliability;
    if (sumW > 0) {
      const finalScore = (sub.comfort * w.comfort + sub.cost * w.cost + sub.speed * w.speed + sub.reliability * w.reliability) / sumW;
      return Math.min(100, Math.max(0, Math.round(finalScore)));
    }
    return opt.overall_score;
  };

  const sortedOptions = [...options].map(opt => ({
    ...opt,
    overall_score: getOverallScore(opt)
  })).sort((a, b) => b.overall_score - a.overall_score);

  // Active option references
  const activeOption = activeOptionIndex !== null && sortedOptions[activeOptionIndex] ? sortedOptions[activeOptionIndex] : null;

  const renderMarkdown = (rawText: string) => {
    if (!rawText) return null;
    let text = rawText.trim();

    if ((text.startsWith('[') && text.endsWith(']')) || (text.startsWith('{') && text.endsWith('}'))) {
      try {
        const jsonish = text.replace(/'/g, '"').replace(/None/g, 'null').replace(/True/g, 'true').replace(/False/g, 'false');
        const parsed = JSON.parse(jsonish) as unknown;
        if (Array.isArray(parsed)) {
          const parts = parsed.map((item: unknown) => {
            if (typeof item === 'object' && item !== null) {
              const record = item as Record<string, unknown>;
              const value = record.text ?? record.reply ?? record.content ?? '';
              return typeof value === 'string' ? value : '';
            }
            return typeof item === 'string' ? item : '';
          }).filter(Boolean);
          if (parts.length) text = parts.join('\n\n');
        } else if (typeof parsed === 'object' && parsed !== null) {
          const record = parsed as Record<string, unknown>;
          const value = record.text ?? record.reply ?? record.content;
          if (typeof value === 'string') text = value;
        }
      } catch {
        const match = /'text':\s*'([\s\S]+?)'(?:,\s*'extras'|,\s*'signature'|\})/.exec(text);
        if (match?.[1]) text = match[1].replace(/\\n/g, '\n').replace(/\\'/g, "'");
      }
    }

    const renderInline = (value: string): React.ReactNode[] => {
      const nodes: React.ReactNode[] = [];
      const pattern = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\[[^\]]+\]\([^\)]+\)|\*[^*\n]+\*|_[^_\n]+_)/g;
      let last = 0;
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(value))) {
        if (match.index > last) nodes.push(value.slice(last, match.index));
        const token = match[0];
        if (token.startsWith('**') || token.startsWith('__')) {
          nodes.push(<strong key={`${match.index}-b`}>{token.slice(2, -2)}</strong>);
        } else if (token.startsWith('`')) {
          nodes.push(<code key={`${match.index}-c`} className="rounded bg-background/70 border border-border px-1.5 py-0.5 text-[0.9em] font-mono">{token.slice(1, -1)}</code>);
        } else if (token.startsWith('[')) {
          const link = /^\[([^\]]+)\]\(([^\)]+)\)$/.exec(token);
          nodes.push(link ? <a key={`${match.index}-a`} href={link[2]} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-2 hover:opacity-80">{link[1]}</a> : token);
        } else {
          nodes.push(<em key={`${match.index}-i`}>{token.slice(1, -1)}</em>);
        }
        last = match.index + token.length;
      }
      if (last < value.length) nodes.push(value.slice(last));
      return nodes;
    };

    const lines = text.split('\n');
    const blocks: React.ReactNode[] = [];
    let index = 0;

    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) { index += 1; continue; }

      if (line.trim().startsWith('```')) {
        const language = line.trim().slice(3).trim();
        const code: string[] = [];
        index += 1;
        while (index < lines.length && !lines[index].trim().startsWith('```')) {
          code.push(lines[index]);
          index += 1;
        }
        index += 1;
        blocks.push(<pre key={`code-${index}`} className="my-3 overflow-x-auto rounded-xl border border-border bg-background p-3 text-xs leading-relaxed"><code className="font-mono">{language ? `${language}\n` : ''}{code.join('\n')}</code></pre>);
        continue;
      }

      if (line.trim().startsWith('|')) {
        const table: string[] = [];
        while (index < lines.length && lines[index].trim().startsWith('|')) { table.push(lines[index]); index += 1; }
        if (table.length >= 2) {
          const parseRow = (row: string) => row.split('|').slice(1, -1).map(cell => cell.trim());
          const headers = parseRow(table[0]);
          const body = table.slice(1).filter(row => !/^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$/.test(row.trim())).map(parseRow);
          blocks.push(<div key={`table-${index}`} className="my-3 overflow-x-auto rounded-xl border border-border"><table className="w-full text-left text-xs"><thead><tr className="border-b border-border bg-background/60">{headers.map((cell, i) => <th key={i} className="p-3 font-bold">{renderInline(cell)}</th>)}</tr></thead><tbody>{body.map((row, ri) => <tr key={ri} className="border-b border-border last:border-0">{headers.map((_, ci) => <td key={ci} className="p-3 align-top">{renderInline(row[ci] ?? '')}</td>)}</tr>)}</tbody></table></div>);
          continue;
        }
      }

      const heading = /^(#{1,3})\s+(.+)$/.exec(line);
      if (heading) {
        const size = heading[1].length === 1 ? 'text-lg' : heading[1].length === 2 ? 'text-base' : 'text-sm';
        blocks.push(<h3 key={`h-${index}`} className={`${size} mt-3 font-bold text-foreground`}>{renderInline(heading[2])}</h3>);
        index += 1;
        continue;
      }

      if (/^>\s?/.test(line)) {
        const quote: string[] = [];
        while (index < lines.length && /^>\s?/.test(lines[index])) { quote.push(lines[index].replace(/^>\s?/, '')); index += 1; }
        blocks.push(<blockquote key={`q-${index}`} className="my-2 border-l-4 border-primary/40 bg-primary/5 px-4 py-2 text-sm italic text-muted-foreground">{quote.map((q, i) => <div key={i}>{renderInline(q)}</div>)}</blockquote>);
        continue;
      }

      if (/^\s*[-*]\s+/.test(line)) {
        const items: string[] = [];
        while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) { items.push(lines[index].replace(/^\s*[-*]\s+/, '')); index += 1; }
        blocks.push(<ul key={`ul-${index}`} className="my-2 list-disc space-y-1 pl-5 text-sm">{items.map((item, i) => <li key={i}>{renderInline(item)}</li>)}</ul>);
        continue;
      }

      if (/^\s*\d+\.\s+/.test(line)) {
        const items: string[] = [];
        while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index])) { items.push(lines[index].replace(/^\s*\d+\.\s+/, '')); index += 1; }
        blocks.push(<ol key={`ol-${index}`} className="my-2 list-decimal space-y-1 pl-5 text-sm">{items.map((item, i) => <li key={i}>{renderInline(item)}</li>)}</ol>);
        continue;
      }

      if (/^\s*---+\s*$/.test(line)) { blocks.push(<hr key={`hr-${index}`} className="my-3 border-border" />); index += 1; continue; }

      const paragraph: string[] = [line];
      index += 1;
      while (index < lines.length && lines[index].trim() && !/^(#{1,3})\s+/.test(lines[index]) && !/^\s*[-*]\s+/.test(lines[index]) && !/^\s*\d+\.\s+/.test(lines[index]) && !/^>\s?/.test(lines[index]) && !lines[index].trim().startsWith('```') && !lines[index].trim().startsWith('|')) { paragraph.push(lines[index]); index += 1; }
      blocks.push(<p key={`p-${index}`} className="text-sm leading-7">{renderInline(paragraph.join(' '))}</p>);
    }

    return <div className="space-y-1">{blocks}</div>;
  };

  const filteredConversations = conversations.filter(c => 
    c.summary.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pinnedConversations = filteredConversations.filter(c => pinnedIds.includes(c.id));
  const unpinnedConversations = filteredConversations.filter(c => !pinnedIds.includes(c.id));

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 border-r border-border bg-muted/20 flex flex-col h-full shrink-0">
        <div className="p-4 border-b border-border flex flex-col gap-3 shrink-0">
          <div className="flex justify-between items-center">
            <button 
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            >
              <ArrowLeft className="h-4 w-4" /> Back to Dashboard
            </button>
            <button 
              onClick={() => router.push('/settings')}
              className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              title="Settings & Personalizations"
            >
              <Sliders className="h-3.5 w-3.5" /> Settings
            </button>
            {(user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN') && (
              <button 
                onClick={() => router.push('/admin')}
                className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer text-primary"
                title="Admin Control Panel"
              >
                <ShieldCheck className="h-3.5 w-3.5" /> Admin
              </button>
            )}
          </div>
          
          <button
            onClick={() => handleNewChat()}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/95 shadow-premium transition-all duration-200 cursor-pointer"
          >
            <Plus className="h-4 w-4" /> New Chat
          </button>
        </div>

        <div className="px-4 py-2 shrink-0">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations..."
              className="w-full pl-9 pr-4 py-2 border border-border rounded-xl text-xs bg-background focus:outline-none"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
          {pinnedConversations.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-muted-foreground uppercase px-2 tracking-wider">Pinned</span>
              {pinnedConversations.map(c => renderChatListItem(c))}
            </div>
          )}

          <div className="space-y-1.5">
            {pinnedConversations.length > 0 && unpinnedConversations.length > 0 && (
              <span className="text-[10px] font-bold text-muted-foreground uppercase px-2 tracking-wider">All Recents</span>
            )}
            {unpinnedConversations.map(c => renderChatListItem(c))}
            {conversations.length === 0 && (
              <p className="text-center text-xs text-muted-foreground p-4">No recent conversations.</p>
            )}
          </div>
        </div>
        {/* User Card */}
        <div 
          onClick={() => router.push('/subscription')}
          className="p-4 border-t border-border bg-muted/30 hover:bg-muted/50 shrink-0 flex items-center gap-3 cursor-pointer"
          title="Manage Subscription & Billing"
        >
          <div className="h-9 w-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
            {user?.fullName[0] || 'U'}
          </div>
          <div className="min-w-0 flex-1 flex justify-between items-center">
            <div>
              <h5 className="text-xs font-semibold truncate">{user?.fullName}</h5>
              <p className="text-[9px] text-muted-foreground truncate">{user?.email}</p>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </div>
        </div>
      </aside>

      {/* Main Workspace Layout Split */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Pane */}
        <main className={`${options.length > 0 ? 'w-[45%]' : 'w-full'} flex flex-col h-full bg-background border-r border-border relative`}>
          <header className="px-6 py-4 border-b border-border flex items-center justify-between shrink-0 bg-background/50 backdrop-blur-md">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
                <Sparkles className="h-4.5 w-4.5" />
              </div>
              <div>
                <h3 className="font-bold text-sm">RailYatra AI Workspace</h3>
                <p className="text-[10px] text-muted-foreground">LangGraph Routing layer active</p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs text-muted-foreground bg-muted/40 px-3 py-1.5 rounded-lg border border-border font-medium">
              <Clock className="h-3.5 w-3.5" />
              <span>Tatkal AC: 10:00 AM | SL: 11:00 AM</span>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 && !loading ? (
              <div className="h-full flex flex-col items-center justify-center max-w-xl mx-auto text-center space-y-8 my-auto">
                <div className="space-y-3">
                  <Bot className="h-16 w-16 text-primary animate-pulse mx-auto" />
                  <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                    RailYatra Intelligence Hub
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    Get real-time answers, smart itinerary scores, prediction charts, and optimal train alternatives.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 w-full text-left">
                  <button 
                    onClick={() => handleNewChat('Search trains from New Delhi (NDLS) to Bhopal (BPL) for July 28')}
                    className="p-4 border border-border rounded-2xl hover:border-primary bg-muted/20 hover:bg-muted/40 transition-all text-xs flex flex-col gap-1 cursor-pointer"
                  >
                    <span className="font-bold text-foreground">Find Trains & Schedules</span>
                    <span className="text-muted-foreground text-[10px]">NDLS to BPL with live CC/EC fares.</span>
                  </button>
                  <button 
                    onClick={() => handleNewChat('Check status of PNR 4210987654 and confirm clearance probability')}
                    className="p-4 border border-border rounded-2xl hover:border-primary bg-muted/20 hover:bg-muted/40 transition-all text-xs flex flex-col gap-1 cursor-pointer"
                  >
                    <span className="font-bold text-foreground">PNR Waitlist Clear Risk</span>
                    <span className="text-muted-foreground text-[10px]">Compute confirmation metrics for waitlists.</span>
                  </button>
                  <button 
                    onClick={() => handleNewChat('What are the refund cancellation rules for confirmed 3AC tickets?')}
                    className="p-4 border border-border rounded-2xl hover:border-primary bg-muted/20 hover:bg-muted/40 transition-all text-xs flex flex-col gap-1 cursor-pointer"
                  >
                    <span className="font-bold text-foreground">Railway Cancellation Rules</span>
                    <span className="text-muted-foreground text-[10px]">Retrieve policies from Qdrant vector database.</span>
                  </button>
                  <button 
                    onClick={() => handleNewChat('Recommend the best class between CC and Sleeper for a 6 hour journey')}
                    className="p-4 border border-border rounded-2xl hover:border-primary bg-muted/20 hover:bg-muted/40 transition-all text-xs flex flex-col gap-1 cursor-pointer"
                  >
                    <span className="font-bold text-foreground">Compare Travel Tiers</span>
                    <span className="text-muted-foreground text-[10px]">Run scoring criteria mapping speed and comfort.</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((msg, index) => (
                  <div 
                    key={index}
                    className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <div className={`h-9 w-9 rounded-xl flex items-center justify-center shrink-0 ${
                      msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted border border-border text-foreground'
                    }`}>
                      {msg.role === 'user' ? <UserIcon className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
                    </div>
                    
                    <div className={`flex-1 p-4 rounded-2xl border ${
                      msg.role === 'user' 
                        ? 'bg-primary/5 border-primary/20 text-foreground' 
                        : 'bg-muted/30 border-border text-foreground'
                    }`}>
                      {renderMarkdown(msg.content)}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex gap-4">
                    <div className="h-9 w-9 rounded-xl bg-muted border border-border flex items-center justify-center shrink-0">
                      <Bot className="h-5 w-5 animate-pulse" />
                    </div>
                    <div className="flex-1 p-4 rounded-2xl border bg-muted/30 border-border flex gap-1.5 items-center">
                      <span className="h-2 w-2 rounded-full bg-foreground/30 animate-bounce [animation-delay:-0.3s]"></span>
                      <span className="h-2 w-2 rounded-full bg-foreground/30 animate-bounce [animation-delay:-0.15s]"></span>
                      <span className="h-2 w-2 rounded-full bg-foreground/30 animate-bounce"></span>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="p-4 border-t border-border shrink-0 bg-background/50 backdrop-blur-md">
            <form onSubmit={handleSubmit} className="w-full">
              <div className="relative border border-border focus-within:border-primary rounded-2xl overflow-hidden bg-background shadow-premium pr-12 pl-4 py-2 flex items-center">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit();
                    }
                  }}
                  placeholder="Message RailYatra (Ctrl+Enter to send)..."
                  rows={1}
                  className="w-full focus:outline-none text-sm bg-background resize-none py-1 h-7"
                />
                <button
                  type="submit"
                  disabled={streaming || !input.trim()}
                  className="absolute right-3 p-2 rounded-xl bg-primary text-primary-foreground hover:bg-primary/95 transition-colors disabled:opacity-40 cursor-pointer"
                >
                  <Send className="h-4.5 w-4.5" />
                </button>
              </div>
            </form>
          </div>
        </main>

        {/* Journey Intelligence Cockpit Pane (Right Side) */}
        {options.length > 0 && (
          <section className="w-[55%] flex flex-col h-full bg-muted/10 overflow-y-auto p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div className="flex items-center gap-2">
                <Gauge className="h-5 w-5 text-primary" />
                <h2 className="font-extrabold text-base tracking-tight">Journey Intelligence Cockpit</h2>
              </div>
              {/* Data quality / Freshness label */}
              {options[0]?.data_quality && (
                <div className="flex items-center gap-1.5 text-[10px] font-semibold text-muted-foreground bg-muted border border-border px-2 py-1 rounded-md">
                  <Database className="h-3 w-3" />
                  <span>Sandbox Mode | Provider: {options[0].data_quality.provider} | age: {options[0].data_quality.data_age_secs}s</span>
                </div>
              )}
            </div>

            {/* Custom Sliders config */}
            <div className="bg-background border border-border p-4 rounded-2xl space-y-4 shadow-sm">
              <div className="flex items-center gap-2 text-xs font-bold text-foreground">
                <Sliders className="h-4 w-4 text-primary" />
                <span>Adjust Journey Preference Weights</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-medium text-muted-foreground">
                    <span>Comfort Multiplier</span>
                    <span className="font-bold text-foreground">{weights.comfort.toFixed(1)}x</span>
                  </div>
                  <input 
                    type="range" min="0.5" max="3.0" step="0.1" 
                    value={weights.comfort} 
                    onChange={(e) => setWeights(prev => ({ ...prev, comfort: parseFloat(e.target.value) }))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary" 
                  />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-medium text-muted-foreground">
                    <span>Budget Multiplier</span>
                    <span className="font-bold text-foreground">{weights.budget.toFixed(1)}x</span>
                  </div>
                  <input 
                    type="range" min="0.5" max="3.0" step="0.1" 
                    value={weights.budget} 
                    onChange={(e) => setWeights(prev => ({ ...prev, budget: parseFloat(e.target.value) }))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary" 
                  />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-medium text-muted-foreground">
                    <span>Speed Multiplier</span>
                    <span className="font-bold text-foreground">{weights.speed.toFixed(1)}x</span>
                  </div>
                  <input 
                    type="range" min="0.5" max="3.0" step="0.1" 
                    value={weights.speed} 
                    onChange={(e) => setWeights(prev => ({ ...prev, speed: parseFloat(e.target.value) }))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary" 
                  />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[10px] font-medium text-muted-foreground">
                    <span>Reliability Multiplier</span>
                    <span className="font-bold text-foreground">{weights.reliability.toFixed(1)}x</span>
                  </div>
                  <input 
                    type="range" min="0.5" max="3.0" step="0.1" 
                    value={weights.reliability} 
                    onChange={(e) => setWeights(prev => ({ ...prev, reliability: parseFloat(e.target.value) }))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary" 
                  />
                </div>
              </div>
            </div>

            {/* Scored Options List */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase text-muted-foreground tracking-wider">Ranked Alternatives</h4>
              <div className="space-y-2.5">
                {sortedOptions.map((opt, i) => {
                  const isSelected = activeOptionIndex === i;
                  const scoreColor = opt.overall_score >= 80 ? 'bg-success/10 text-success' : (opt.overall_score >= 60 ? 'bg-primary/10 text-primary' : 'bg-danger/10 text-danger');
                  
                  return (
                    <div 
                      key={i}
                      onClick={() => setActiveOptionIndex(i)}
                      className={`p-4 border rounded-2xl cursor-pointer transition-all hover:bg-background/80 flex flex-col gap-3 ${
                        isSelected 
                          ? 'border-primary bg-background shadow-premium ring-1 ring-primary/20' 
                          : 'border-border bg-background/40'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="text-xs font-bold text-foreground">{opt.train_name} ({opt.train_number})</span>
                          {opt.is_alternative_station && (
                            <span className="ml-2 text-[9px] font-semibold text-warning bg-warning/10 px-1.5 py-0.5 rounded">Alternate Station</span>
                          )}
                          {opt.is_alternative_date && (
                            <span className="ml-2 text-[9px] font-semibold text-secondary bg-secondary/10 px-1.5 py-0.5 rounded">Alternate Date: {opt.journey_date}</span>
                          )}
                        </div>
                        <div className={`text-xs font-black px-2.5 py-1 rounded-lg ${scoreColor}`}>
                          Score: {opt.overall_score}
                        </div>
                      </div>

                      <div className="grid grid-cols-4 gap-2 text-[10px] text-muted-foreground">
                        <div>
                          <span className="block font-medium">Class & Fare</span>
                          <span className="font-bold text-foreground">{opt.booking_class} | Rs. {opt.fare}</span>
                        </div>
                        <div>
                          <span className="block font-medium">Waitlist / Status</span>
                          <span className={`font-bold ${opt.waitlist_status.includes('WL') ? 'text-warning' : 'text-success'}`}>{opt.waitlist_status}</span>
                        </div>
                        <div>
                          <span className="block font-medium">Delay Forecast</span>
                          <span className={`font-bold ${opt.predicted_delay_mins > 30 ? 'text-danger' : 'text-success'}`}>{opt.predicted_delay_mins} mins</span>
                        </div>
                        <div>
                          <span className="block font-medium">Clear Chance</span>
                          <span className="font-bold text-foreground">{opt.confirmation_probability}%</span>
                        </div>
                      </div>

                      {/* Pill tags */}
                      <div className="flex flex-wrap gap-1">
                        {opt.reason_codes.map((code, ci) => (
                          <span key={ci} className="text-[9px] font-bold text-primary bg-primary/5 border border-primary/10 px-2 py-0.5 rounded-full">{code}</span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Selected Option Deep Analysis panel */}
            {activeOption && (
              <div className="bg-background border border-border p-5 rounded-2xl space-y-4 shadow-sm">
                <div className="flex items-center gap-2 text-xs font-bold text-foreground border-b border-border pb-2.5">
                  <Award className="h-4.5 w-4.5 text-primary" />
                  <span>Tradeoff Analysis & Route Details</span>
                </div>

                {/* Journey Timeline */}
                <div className="relative pl-6 space-y-4 border-l border-primary/20 py-1 text-xs">
                  <div className="relative">
                    <span className="absolute -left-[30px] top-0 h-4 w-4 rounded-full bg-primary flex items-center justify-center text-[8px] text-primary-foreground font-bold">1</span>
                    <span className="font-semibold block text-foreground">Depart {activeOption.source}</span>
                    <span className="text-muted-foreground text-[10px]">Time: {activeOption.departure}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground text-[10px]">Transit Duration: {activeOption.duration} | Predict Delay: +{activeOption.predicted_delay_mins} mins</span>
                  </div>
                  <div className="relative">
                    <span className="absolute -left-[30px] top-0 h-4 w-4 rounded-full bg-secondary flex items-center justify-center text-[8px] text-secondary-foreground font-bold">2</span>
                    <span className="font-semibold block text-foreground">Arrive {activeOption.destination}</span>
                    <span className="text-muted-foreground text-[10px]">Expected Arrival: {activeOption.arrival}</span>
                  </div>
                </div>

                {/* Advantages / Disadvantages */}
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="space-y-1.5">
                    <span className="flex items-center gap-1 font-bold text-success">
                      <ThumbsUp className="h-3.5 w-3.5" /> Pros
                    </span>
                    <ul className="space-y-1 text-muted-foreground text-[10px] list-disc pl-4">
                      {activeOption.advantages.map((adv, ai) => <li key={ai}>{adv}</li>)}
                    </ul>
                  </div>
                  <div className="space-y-1.5">
                    <span className="flex items-center gap-1 font-bold text-danger">
                      <ThumbsDown className="h-3.5 w-3.5" /> Cons
                    </span>
                    <ul className="space-y-1 text-muted-foreground text-[10px] list-disc pl-4">
                      {activeOption.disadvantages.map((dis, di) => <li key={di}>{dis}</li>)}
                    </ul>
                  </div>
                </div>

                {/* Predictability summary */}
                <div className="flex gap-3 bg-muted/20 border border-border p-3.5 rounded-xl text-[10px] text-muted-foreground">
                  <Info className="h-4.5 w-4.5 text-primary shrink-0" />
                  <p className="leading-relaxed">{activeOption.reasoning}</p>
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );

  // Sub-render list item
  function renderChatListItem(c: Conversation) {
    const isSelected = activeId === c.id;
    const isPinned = pinnedIds.includes(c.id);

    return (
      <div
        key={c.id}
        onClick={() => !editingId && loadActiveConversation(c.id)}
        className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all ${
          isSelected 
            ? 'bg-primary/10 text-primary border border-primary/20' 
            : 'hover:bg-muted/40 border border-transparent'
        }`}
      >
        <div className="min-w-0 flex-1 flex items-center gap-2">
          {isPinned && <Pin className="h-3 w-3 rotate-45 text-primary shrink-0" />}
          {editingId === c.id ? (
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRename(c.id)}
              className="w-full text-xs bg-background border border-border rounded px-1.5 py-0.5 focus:outline-none"
              autoFocus
            />
          ) : (
            <span className="text-xs font-medium truncate">{c.summary}</span>
          )}
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {editingId === c.id ? (
            <>
              <button onClick={() => handleRename(c.id)} className="p-1 rounded hover:bg-muted text-primary cursor-pointer">
                <Check className="h-3 w-3" />
              </button>
              <button onClick={() => setEditingId(null)} className="p-1 rounded hover:bg-muted text-muted-foreground cursor-pointer">
                <X className="h-3 w-3" />
              </button>
            </>
          ) : (
            <>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setEditingId(c.id);
                  setEditTitle(c.summary);
                }} 
                className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <Edit3 className="h-3 w-3" />
              </button>
              <button 
                onClick={(e) => handleTogglePin(c.id, e)} 
                className={`p-1 rounded hover:bg-muted cursor-pointer ${isPinned ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}
              >
                <Pin className="h-3 w-3 rotate-45" />
              </button>
              <button 
                onClick={(e) => handleDelete(c.id, e)} 
                className="p-1 rounded hover:bg-danger/10 text-danger opacity-70 hover:opacity-100 cursor-pointer"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </>
          )}
        </div>
      </div>
    );
  }
}
