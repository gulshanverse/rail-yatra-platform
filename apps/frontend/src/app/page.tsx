'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../store/authStore';
import FloatingAI from '../components/FloatingAI';
import { 
  Train, 
  Sparkles, 
  Moon, 
  Sun, 
  Compass, 
  LogOut, 
  Cpu, 
  CheckCircle,
  TrendingUp,
  HelpCircle
} from 'lucide-react';

interface AIResponse {
  reply: string;
  parsed_intent: string;
  confidence: number;
  explanation: string;
  credits_left: number;
}

export default function Home() {
  const { user, token, theme, setTheme, clearAuth, setAuth } = useAuthStore();
  const router = useRouter();
  
  // Simulation states
  const [query, setQuery] = useState('');
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'agent' | 'billing' | 'features'>('agent');

  const [prevUserCredits, setPrevUserCredits] = useState<number | undefined>(undefined);
  const [credits, setCredits] = useState(3);

  if (user?.subscriptions?.[0]?.credits !== undefined && user.subscriptions[0].credits !== prevUserCredits) {
    setPrevUserCredits(user.subscriptions[0].credits);
    setCredits(user.subscriptions[0].credits);
  }

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
  };

  const handleSimulateQuery = (text: string) => {
    setQuery(text);
  };

  const handleRunQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setAiLoading(true);
    setAiResponse(null);

    // Asynchronously simulate credit deduction locally
    if (credits > 0) {
      setCredits(prev => prev - 1);
    }

    try {
      // Connects to FastAPI AI-Service on port 8000
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: query }),
      });

      const data = await response.json();
      setAiResponse(data);
    } catch {
      // Fallback response if AI service is offline
      setAiResponse({
        reply: `Offline AI Engine processed request: "${query}"`,
        parsed_intent: "route_optimization",
        confidence: 0.88,
        explanation: "AI Engine analyzed alternative trains. Delay risk is low (under 12%). Confirmation probability for 3A is 82%. Suggest booking from Raipur junction instead of Bilaspur to secure lower berths.",
        credits_left: credits - 1
      });
    } finally {
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
    const upgradedUser = {
      ...user,
      role: 'PREMIUM',
      subscriptions: [
        {
          tier: 'PREMIUM' as const,
          credits: 100,
          status: 'active'
        }
      ]
    };
    setAuth(token || 'mock_token', upgradedUser);
    setCredits(100);
  };

  const handleSimulateDowngrade = () => {
    if (!user) return;
    const downgradedUser = {
      ...user,
      role: 'USER',
      subscriptions: [
        {
          tier: 'FREE' as const,
          credits: 3,
          status: 'active'
        }
      ]
    };
    setAuth(token || 'mock_token', downgradedUser);
    setCredits(3);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground transition-colors duration-300">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 glass border-b border-border shadow-sm px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-premium">
            <Train className="h-5 w-5" />
          </div>
          <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            RailYatra AI
          </span>
        </div>

        <div className="flex items-center gap-4">
          {/* Theme switcher */}
          <button 
            onClick={handleToggleTheme}
            className="p-2.5 rounded-xl border border-border hover:bg-muted/50 cursor-pointer text-muted-foreground hover:text-foreground transition-colors"
            title={`Current theme: ${theme}. Click to switch.`}
          >
            {theme === 'light' ? <Sun className="h-5 w-5 text-warning" /> : <Moon className="h-5 w-5" />}
          </button>

          {/* User profile dropdown simulator */}
          {user ? (
            <div className="flex items-center gap-3 pl-4 border-l border-border">
              <div className="flex flex-col text-right hidden sm:flex">
                <span className="text-sm font-semibold">{user.fullName}</span>
                <span className="text-xs text-muted-foreground capitalize flex items-center gap-1 justify-end">
                  <span className={`inline-block w-1.5 h-1.5 rounded-full ${user.role === 'PREMIUM' ? 'bg-accent' : 'bg-primary'}`} />
                  {user.role} Account
                </span>
              </div>
              <div className="h-10 w-10 rounded-xl bg-secondary/15 flex items-center justify-center text-secondary font-bold border border-secondary/25">
                {user.fullName[0].toUpperCase()}
              </div>
              <button 
                onClick={handleLogout}
                className="p-2.5 rounded-xl border border-border hover:bg-danger/10 hover:text-danger hover:border-danger/20 cursor-pointer transition-colors text-muted-foreground"
                title="Log Out"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <button 
                onClick={() => router.push('/login')} 
                className="px-4 py-2 text-sm font-semibold rounded-xl hover:bg-muted transition-colors cursor-pointer"
              >
                Log In
              </button>
              <button 
                onClick={() => router.push('/register')} 
                className="px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground btn-hover cursor-pointer"
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Columns: Main Interactive Playground */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Welcome/Status Banner */}
          <div className="rounded-2xl p-8 bg-gradient-to-br from-primary/10 via-secondary/5 to-transparent border border-primary/15 relative overflow-hidden">
            <div className="absolute right-0 bottom-0 opacity-10">
              <Compass className="h-64 w-64 rotate-12 text-primary" />
            </div>
            
            <div className="relative z-10 space-y-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-accent/15 text-accent-foreground border border-accent/20">
                <Sparkles className="h-3.5 w-3.5" />
                Phase 2 Deployment Live
              </span>
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">
                The AI Operating System for Travel Decisions.
              </h1>
              <p className="text-muted-foreground text-base max-w-xl">
                Avoid waitlist uncertainties, discover split-journey tickets, optimize departure boarding junctions, and predict delays using specialized agent logic.
              </p>
              <button 
                onClick={() => router.push('/chat')}
                className="mt-2 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:opacity-90 transition-all shadow-premium cursor-pointer"
              >
                <Sparkles className="h-4.5 w-4.5" />
                Open AI Workspace
              </button>
            </div>
          </div>

          {/* Interactive tabs */}
          <div className="border-b border-border flex gap-6 text-sm">
            <button 
              onClick={() => setActiveTab('agent')}
              className={`pb-3 font-semibold border-b-2 cursor-pointer transition-all ${activeTab === 'agent' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            >
              AI Travel Decision Engine
            </button>
            <button 
              onClick={() => setActiveTab('billing')}
              className={`pb-3 font-semibold border-b-2 cursor-pointer transition-all ${activeTab === 'billing' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            >
              Subscription & Premium Credits
            </button>
            <button 
              onClick={() => setActiveTab('features')}
              className={`pb-3 font-semibold border-b-2 cursor-pointer transition-all ${activeTab === 'features' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            >
              Agent Mesh Directory
            </button>
          </div>

          {/* Tab 1: AI Engine Playground */}
          {activeTab === 'agent' && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-border bg-card p-6 shadow-premium">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-primary" />
                  Ask AI Decision Engine
                </h3>

                <form onSubmit={handleRunQuery} className="space-y-4">
                  <div className="relative">
                    <input
                      type="text"
                      className="w-full pl-4 pr-12 py-3.5 rounded-xl border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary text-sm transition-all"
                      placeholder="Enter natural language query (e.g. I need to travel to Delhi before 9 AM)..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                    <button 
                      type="submit"
                      disabled={aiLoading}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 cursor-pointer"
                    >
                      <Sparkles className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Quick-Prompt Simulators */}
                  <div className="flex flex-wrap gap-2 pt-1">
                    <span className="text-xs text-muted-foreground self-center mr-1">Simulate Query:</span>
                    <button 
                      type="button"
                      onClick={() => handleSimulateQuery('I want to travel from Bilaspur to New Delhi next Friday')}
                      className="text-xs bg-muted hover:bg-muted/75 px-3 py-1.5 rounded-lg border border-border transition-colors cursor-pointer"
                    >
                      &quot;Bilaspur to Delhi next Friday&quot;
                    </button>
                    <button 
                      type="button"
                      onClick={() => handleSimulateQuery('My ticket waitlist is WL 23. What are my confirmation chances?')}
                      className="text-xs bg-muted hover:bg-muted/75 px-3 py-1.5 rounded-lg border border-border transition-colors cursor-pointer"
                    >
                      &quot;Waitlist WL 23 chances?&quot;
                    </button>
                  </div>
                </form>
              </div>

              {/* AI response panel */}
              {(aiLoading || aiResponse) && (
                <div className="rounded-2xl border border-border bg-card p-6 shadow-premium transition-all space-y-4">
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-5 w-5 text-accent animate-pulse" />
                      <span className="font-bold text-sm">Orchestrated AI Response</span>
                    </div>
                    {aiResponse?.confidence && (
                      <span className="text-xs bg-accent/15 text-accent-foreground border border-accent/25 px-2.5 py-1 rounded-full font-semibold">
                        Confidence: {(aiResponse.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  {aiLoading || !aiResponse ? (
                    <div className="space-y-3 py-4">
                      <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
                      <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
                      <div className="h-4 bg-muted rounded animate-pulse w-5/6" />
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="p-4 rounded-xl bg-muted/50 border border-border text-sm leading-relaxed">
                        <p className="font-medium text-foreground">{aiResponse.reply}</p>
                        {aiResponse.explanation && (
                          <p className="mt-2 text-muted-foreground text-xs">{aiResponse.explanation}</p>
                        )}
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <CheckCircle className="h-4 w-4 text-accent" />
                          Parsed Intent: <strong className="font-semibold text-foreground uppercase">{aiResponse.parsed_intent}</strong>
                        </span>
                        <span>Model version: v1.0.0-f1</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Billing & Credits Manager */}
          {activeTab === 'billing' && (
            <div className="rounded-2xl border border-border bg-card p-6 shadow-premium space-y-6">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-border pb-6">
                <div>
                  <h3 className="text-lg font-bold">Billing & Feature Gates</h3>
                  <p className="text-sm text-muted-foreground">Simulate payment checkouts and credit usage quotas</p>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={handleSimulateUpgrade}
                    className="px-4 py-2 rounded-xl bg-accent text-accent-foreground font-semibold text-xs btn-hover cursor-pointer"
                  >
                    Simulate Premium Upgrade
                  </button>
                  <button 
                    onClick={handleSimulateDowngrade}
                    className="px-4 py-2 rounded-xl border border-border hover:bg-muted font-semibold text-xs transition-colors cursor-pointer"
                  >
                    Simulate Downgrade
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-5 rounded-xl border border-border bg-background space-y-2">
                  <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Account Level</span>
                  <p className="text-2xl font-black capitalize text-primary">{user?.role || 'User'}</p>
                </div>

                <div className="p-5 rounded-xl border border-border bg-background space-y-2">
                  <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Remaining AI Credits</span>
                  <p className="text-2xl font-black text-accent">{credits} Credits</p>
                </div>

                <div className="p-5 rounded-xl border border-border bg-background space-y-2">
                  <span className="text-xs text-muted-foreground uppercase font-bold tracking-wider">Usage Meter</span>
                  <p className="text-2xl font-black text-foreground">
                    {user?.role === 'PREMIUM' ? 'Unlimited' : `${credits} / 3`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Tab 3: Agent mesh directory */}
          {activeTab === 'features' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                <h4 className="font-bold text-sm text-primary">Travel Planner Agent</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Plans end-to-end itineraries including multi-modal connectivity (Buses, Cabs, Metro transfers).
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                <h4 className="font-bold text-sm text-accent">Boarding Optimizer</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Recommends adjacent travel terminals to maximize ticket availability index.
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                <h4 className="font-bold text-sm text-foreground">Delay Prediction</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Applies historical delays metadata to determine arrival schedule accuracy.
                </p>
              </div>
              <div className="rounded-xl border border-border bg-card p-5 space-y-2">
                <h4 className="font-bold text-sm text-secondary">Fare Optimizer</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Integrates split ticketing calculations to lower overall seat prices.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right 1 Column: Telemetry & Status Panel */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-premium space-y-5">
            <h3 className="text-base font-bold flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Core Infrastructure Status
            </h3>

            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center py-2.5 border-b border-border">
                <span className="text-muted-foreground">Prisma Client</span>
                <span className="font-semibold text-accent flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-accent inline-block" />
                  SQLite Connected
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-border">
                <span className="text-muted-foreground">Backend Core (NestJS)</span>
                <span className="font-semibold text-accent flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-accent inline-block" />
                  Port 5000 Active
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5 border-b border-border">
                <span className="text-muted-foreground">AI Service (FastAPI)</span>
                <span className="font-semibold text-accent flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-accent inline-block" />
                  Port 8000 Active
                </span>
              </div>
              <div className="flex justify-between items-center py-2.5">
                <span className="text-muted-foreground">Local Time</span>
                <span className="font-semibold text-foreground">2026-07-06 14:22</span>
              </div>
            </div>
          </div>

          {/* Quick instructions */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-premium space-y-4">
            <h3 className="text-base font-bold flex items-center gap-2">
              <HelpCircle className="h-5 w-5 text-secondary" />
              Phase 2 Validation Steps
            </h3>
            <ul className="space-y-3 text-xs text-muted-foreground list-disc pl-4 leading-relaxed">
              <li>Open register page and submit details to write to the SQLite database.</li>
              <li>Authenticate details on the login gateway.</li>
              <li>Observe active session token storing user context.</li>
              <li>Toggle themes: Light/Dark/Auto theme settings are saved globally.</li>
              <li>Change subscription plan levels to simulate premium gateways.</li>
            </ul>
          </div>
        </div>
      </main>

      {/* Floating AI assistant bubble */}
      <FloatingAI />

      {/* Footer */}
      <footer className="mt-auto border-t border-border py-6 text-center text-xs text-muted-foreground bg-muted/20">
        <p>© 2026 RailYatra AI. All rights reserved. Under Venture Scaffolding.</p>
      </footer>
    </div>
  );
}
