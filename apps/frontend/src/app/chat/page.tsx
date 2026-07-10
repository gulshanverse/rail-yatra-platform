'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
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
  HelpCircle,
  AlertCircle
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

export default function AIWorkspace() {
  const { token, user } = useAuthStore();
  const router = useRouter();

  // Sidebar states
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [pinnedIds, setPinnedIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Active chat states
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Redirect if not logged in
  useEffect(() => {
    if (!token) {
      router.push('/login');
    } else {
      loadConversations();
      // Load pinned conversations from localStorage
      const savedPins = localStorage.getItem('railyatra_pinned_chats');
      if (savedPins) {
        setPinnedIds(JSON.parse(savedPins));
      }
    }
  }, [token]);

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
  }, [input, activeId, streaming]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadConversations = async () => {
    try {
      const res = await fetch('http://localhost:5000/api/conversations', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  const loadActiveConversation = async (id: string) => {
    setActiveId(id);
    setLoading(true);
    setMessages([]);
    try {
      const res = await fetch(`http://localhost:5000/api/conversations/${id}`, {
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

  const handleNewChat = async (initialQuery?: string) => {
    try {
      const res = await fetch('http://localhost:5000/api/conversations', {
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
          // Delay briefly to allow active ID to state-sync before submitting
          setTimeout(() => sendChatMessage(newChat.id, initialQuery), 100);
        }
      }
    } catch (err) {
      console.error('Error creating chat:', err);
    }
  };

  const handleRename = async (id: string) => {
    if (!editTitle.trim()) return;
    try {
      const res = await fetch(`http://localhost:5000/api/conversations/${id}`, {
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
      const res = await fetch(`http://localhost:5000/api/conversations/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setConversations(prev => prev.filter(c => c.id !== id));
        if (activeId === id) {
          setActiveId(null);
          setMessages([]);
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

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || streaming) return;
    
    const userQuery = input.trim();
    setInput('');

    if (!activeId) {
      handleNewChat(userQuery);
    } else {
      sendChatMessage(activeId, userQuery);
    }
  };

  const sendChatMessage = async (convId: string, queryText: string) => {
    setMessages(prev => [...prev, { role: 'user', content: queryText }]);
    setStreaming(true);

    try {
      const response = await fetch(`http://localhost:5000/api/conversations/${convId}/chat`, {
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
      
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);
      let accumulated = '';

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
                accumulated += data.value;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: 'assistant',
                    content: accumulated
                  };
                  return updated;
                });
              }
            } catch (err) {
              // Ignore boundary failures
            }
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Connection to RailYatra AI service lost. Please verify your endpoints.' }
      ]);
    } finally {
      setStreaming(false);
      loadConversations(); // refresh title if it was "New Chat"
    }
  };

  // Simple clean helper to render markdown headings and tables inside chats
  const renderMarkdown = (text: string) => {
    if (!text) return null;
    
    // Check if the output is structured as a Table
    if (text.includes('|') && text.includes('\n')) {
      const lines = text.split('\n');
      const tableLines = lines.filter(line => line.trim().startsWith('|'));
      
      if (tableLines.length >= 2) {
        const headers = tableLines[0].split('|').map(h => h.trim()).filter(Boolean);
        const rows = tableLines.slice(2).map(r => r.split('|').map(col => col.trim()).filter(Boolean));
        
        return (
          <div className="overflow-x-auto my-3 border border-border rounded-xl">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-muted border-b border-border">
                  {headers.map((h, i) => (
                    <th key={i} className="p-3.5 font-bold text-foreground/80">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, ri) => (
                  <tr key={ri} className="border-b border-border hover:bg-muted/20">
                    {row.map((col, ci) => (
                      <td key={ci} className="p-3.5 text-foreground font-medium">{col}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
    }

    // Split text by custom boxes/alerts
    const lines = text.split('\n');
    return (
      <div className="space-y-2">
        {lines.map((line, index) => {
          // Parse tips/warnings
          if (line.startsWith('> [!TIP]')) return null;
          if (line.startsWith('> [!NOTE]')) return null;
          if (line.startsWith('> ')) {
            return (
              <blockquote key={index} className="pl-4 border-l-4 border-primary/50 text-xs italic text-muted-foreground my-2 py-1 bg-primary/5 rounded-r">
                {line.substring(2)}
              </blockquote>
            );
          }
          if (line.startsWith('### ')) {
            return <h4 key={index} className="text-sm font-bold text-foreground mt-3 mb-1">{line.substring(4)}</h4>;
          }
          if (line.startsWith('## ')) {
            return <h3 key={index} className="text-base font-bold text-foreground mt-4 mb-2">{line.substring(3)}</h3>;
          }
          if (line.startsWith('- ') || line.startsWith('* ')) {
            return <li key={index} className="list-disc ml-5 text-sm">{line.substring(2)}</li>;
          }
          
          return <p key={index} className="text-sm leading-relaxed">{line}</p>;
        })}
      </div>
    );
  };

  // Filter conversations
  const filteredConversations = conversations.filter(c => 
    c.summary.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const pinnedConversations = filteredConversations.filter(c => pinnedIds.includes(c.id));
  const unpinnedConversations = filteredConversations.filter(c => !pinnedIds.includes(c.id));

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Workspace Sidebar */}
      <aside className="w-80 border-r border-border bg-muted/20 flex flex-col h-full">
        {/* Navigation & Header */}
        <div className="p-4 border-b border-border flex flex-col gap-3 shrink-0">
          <button 
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Dashboard
          </button>
          
          <button
            onClick={() => handleNewChat()}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/95 shadow-premium transition-all duration-200 cursor-pointer"
            title="Shortcut: Ctrl+K / Cmd+K"
          >
            <Plus className="h-4 w-4" /> New Chat
          </button>
        </div>

        {/* Search */}
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

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
          {/* Pinned Chats */}
          {pinnedConversations.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-muted-foreground uppercase px-2 tracking-wider">Pinned</span>
              {pinnedConversations.map(c => renderChatListItem(c))}
            </div>
          )}

          {/* All Chats */}
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
        <div className="p-4 border-t border-border bg-muted/30 shrink-0 flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
            {user?.fullName[0] || 'U'}
          </div>
          <div className="min-w-0 flex-1">
            <h5 className="text-sm font-semibold truncate">{user?.fullName}</h5>
            <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
      </aside>

      {/* Main Workspace active area */}
      <main className="flex-1 flex flex-col h-full bg-background relative">
        {/* Top bar */}
        <header className="px-6 py-4 border-b border-border flex items-center justify-between shrink-0 bg-background/50 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
              <Sparkles className="h-4.5 w-4.5" />
            </div>
            <div>
              <h3 className="font-bold text-sm">RailYatra AI Workspace</h3>
              <p className="text-[10px] text-muted-foreground">LangGraph Travel Intelligence Node</p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-muted-foreground bg-muted/40 px-3 py-1.5 rounded-lg border border-border font-medium">
            <Clock className="h-3.5 w-3.5" />
            <span>Tatkal AC: 10:00 AM | Sleeper: 11:00 AM</span>
          </div>
        </header>

        {/* Messages */}
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

              {/* Suggestions Panel */}
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
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg, index) => (
                <div 
                  key={index}
                  className={`flex gap-4 ${
                    msg.role === 'user' ? 'flex-row-reverse' : ''
                  }`}
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

        {/* Input panel */}
        <div className="p-4 border-t border-border shrink-0 bg-background/50 backdrop-blur-md">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
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
            <div className="max-w-3xl mx-auto mt-2 flex justify-between text-[10px] text-muted-foreground px-1">
              <span>Supports Markdown tables & formatting</span>
              <span>Workspace connected via SSE</span>
            </div>
          </form>
        </div>
      </main>
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
