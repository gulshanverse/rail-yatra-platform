'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { 
  Sparkles, 
  ArrowLeft, 
  Check, 
  ChevronRight, 
  Database, 
  Gauge, 
  HelpCircle, 
  Clock, 
  X,
  AlertCircle,
  Zap,
  Info,
  Sliders,
  Mail,
  Smartphone,
  Bell,
  CheckCircle,
  Eye,
  Activity,
  Heart,
  ShieldAlert,
  ThumbsUp,
  MessageCircle
} from 'lucide-react';

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: string; // Journey, PNR, AI, Billing, Marketing, System
  priority: string; // low, medium, high, critical
  read: boolean;
  timestamp: string;
}

interface NotificationPreference {
  id: string;
  emailAlerts: boolean;
  smsAlerts: boolean;
  pushAlerts: boolean;
  whatsappAlerts: boolean;
  quietHoursStart: string;
  quietHoursEnd: string;
  marketingAlerts: boolean;
  digestPreference: string;
}

interface UserInsight {
  id: string;
  title: string;
  content: string;
  timestamp: string;
}

export default function UserSettingsCockpit() {
  const { token, user } = useAuthStore();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [savingPrefs, setSavingPrefs] = useState(false);
  
  // Data States
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreference | null>(null);
  const [insights, setInsights] = useState<UserInsight[]>([]);
  const [engagementScore, setEngagementScore] = useState<number>(0);
  
  // Active Filter Tab
  const [filterTab, setFilterTab] = useState<'all' | 'unread' | 'read'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  
  // Travel checklist mock state
  const [checklist, setChecklist] = useState([
    { id: 1, text: 'Download ticket PDF offline', completed: true },
    { id: 2, text: 'Validate PNR prediction clearance', completed: false },
    { id: 3, text: 'Check weather forecast (active delay warnings)', completed: false },
    { id: 4, text: 'Verify boarding junction details (NDLS quota)', completed: false }
  ]);

  // Travel preferences configuration sliders (local representation)
  const [travelWeights, setTravelWeights] = useState({
    preferredClass: '3A',
    priorityType: 'comfort',
    favoriteBoarding: 'NDLS'
  });

  useEffect(() => {
    if (!token) {
      router.push('/login');
    } else {
      loadSettingsData();
    }
  }, [token, filterTab, categoryFilter]);

  const loadSettingsData = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      // Load notifications list
      const notifUrl = `http://localhost:5000/api/engagement/notifications?filter=${filterTab}${categoryFilter ? `&category=${categoryFilter}` : ''}`;
      const notifRes = await fetch(notifUrl, { headers });
      const prefsRes = await fetch('http://localhost:5000/api/engagement/preferences', { headers });
      const insightsRes = await fetch('http://localhost:5000/api/engagement/insights', { headers });
      const scoreRes = await fetch('http://localhost:5000/api/engagement/score', { headers });

      if (notifRes.ok && prefsRes.ok && insightsRes.ok && scoreRes.ok) {
        const notifData = await notifRes.json();
        const prefsData = await prefsRes.json();
        const insightsData = await insightsRes.json();
        const scoreData = await scoreRes.json();
        
        setNotifications(notifData);
        setPreferences(prefsData);
        setInsights(insightsData);
        setEngagementScore(scoreData.score);
      }
    } catch (err) {
      console.error('Failed to load personalization settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePreference = async (updates: Partial<NotificationPreference>) => {
    if (!preferences) return;
    setSavingPrefs(true);
    
    // Optimistic UI state update
    const nextPrefs = { ...preferences, ...updates } as NotificationPreference;
    setPreferences(nextPrefs);

    try {
      const res = await fetch('http://localhost:5000/api/engagement/preferences', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });
      
      if (!res.ok) throw new Error('Update failed');
    } catch (err) {
      console.error('Preferences save failure:', err);
      // rollback
      loadSettingsData();
    } finally {
      setSavingPrefs(false);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:5000/api/engagement/notifications/${id}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
        setEngagementScore(data.engagementScore);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      const res = await fetch('http://localhost:5000/api/engagement/notifications/read-all', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleChecklist = (id: number) => {
    setChecklist(prev => prev.map(item => item.id === id ? { ...item, completed: !item.completed } : item));
  };

  if (loading && !preferences) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <div className="text-center space-y-4">
          <Clock className="h-10 w-10 text-primary animate-spin mx-auto" />
          <p className="text-xs font-semibold text-muted-foreground">Loading personalization settings dashboard...</p>
        </div>
      </div>
    );
  }

  const categoryTags = ['Journey', 'PNR', 'AI', 'Billing', 'System'];

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 md:px-8 max-w-6xl mx-auto space-y-10">
      
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border pb-6">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => router.push('/chat')}
            className="p-2 border border-border hover:bg-muted/40 rounded-xl transition-colors cursor-pointer"
          >
            <ArrowLeft className="h-4.5 w-4.5" />
          </button>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Engagement & Personalization
            </h1>
            <p className="text-xs text-muted-foreground">Configure travel profiles, notifications preferences, and checklist tracks.</p>
          </div>
        </div>

        {/* User Engagement Score Dial */}
        <div className="flex items-center gap-3 bg-muted border border-border px-4 py-2 rounded-2xl shadow-sm">
          <div className="h-8 w-8 rounded-lg bg-primary/15 text-primary flex items-center justify-center">
            <Activity className="h-4.5 w-4.5" />
          </div>
          <div>
            <span className="block text-[9px] text-muted-foreground uppercase font-black tracking-wider">Engagement Level</span>
            <span className="text-xs font-bold text-foreground">{engagementScore} interaction pts</span>
          </div>
        </div>
      </header>

      {/* Main dashboard contents split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Preferences Controls & Insights */}
        <div className="lg:col-span-7 space-y-8">
          
          {/* Channels & Quiet hours preferences */}
          {preferences && (
            <section className="bg-muted/10 border border-border p-6 rounded-3xl space-y-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Sliders className="h-4.5 w-4.5 text-primary" />
                  <h3 className="font-bold text-xs">Notification Channels & Quiet Hours</h3>
                </div>
                {savingPrefs && <span className="text-[9px] text-primary font-bold">Autosaving updates...</span>}
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Email Toggle */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>Email Alerts</span>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={preferences.emailAlerts}
                    onChange={(e) => handleUpdatePreference({ emailAlerts: e.target.checked })}
                    className="accent-primary cursor-pointer"
                  />
                </div>

                {/* SMS Toggle */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs">
                    <Smartphone className="h-4 w-4 text-muted-foreground" />
                    <span>SMS updates</span>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={preferences.smsAlerts}
                    onChange={(e) => handleUpdatePreference({ smsAlerts: e.target.checked })}
                    className="accent-primary cursor-pointer"
                  />
                </div>

                {/* Web Push Toggle */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs">
                    <Bell className="h-4 w-4 text-muted-foreground" />
                    <span>Web Push Alerts</span>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={preferences.pushAlerts}
                    onChange={(e) => handleUpdatePreference({ pushAlerts: e.target.checked })}
                    className="accent-primary cursor-pointer"
                  />
                </div>

                {/* WhatsApp Toggle */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs">
                    <MessageCircle className="h-4 w-4 text-muted-foreground" />
                    <span>WhatsApp Alerts</span>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={preferences.whatsappAlerts}
                    onChange={(e) => handleUpdatePreference({ whatsappAlerts: e.target.checked })}
                    className="accent-primary cursor-pointer"
                  />
                </div>
              </div>

              {/* Quiet Hours configs */}
              <div className="border-t border-border pt-4 grid grid-cols-2 gap-4">
                <div className="space-y-1.5 text-xs">
                  <span className="block text-[10px] text-muted-foreground font-medium">Quiet Hours Start</span>
                  <input 
                    type="time" 
                    value={preferences.quietHoursStart} 
                    onChange={(e) => handleUpdatePreference({ quietHoursStart: e.target.value })}
                    className="w-full p-2 border border-border bg-background rounded-xl text-xs"
                  />
                </div>
                <div className="space-y-1.5 text-xs">
                  <span className="block text-[10px] text-muted-foreground font-medium">Quiet Hours End</span>
                  <input 
                    type="time" 
                    value={preferences.quietHoursEnd} 
                    onChange={(e) => handleUpdatePreference({ quietHoursEnd: e.target.value })}
                    className="w-full p-2 border border-border bg-background rounded-xl text-xs"
                  />
                </div>
              </div>
            </section>
          )}

          {/* Travel Profile Personalizations */}
          <section className="bg-muted/10 border border-border p-6 rounded-3xl space-y-6 shadow-sm">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Heart className="h-4.5 w-4.5 text-primary" />
              <h3 className="font-bold text-xs">Travel Personalization Priorities</h3>
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div className="space-y-1.5">
                <span className="block text-[10px] text-muted-foreground">Class entitlement</span>
                <select 
                  value={travelWeights.preferredClass} 
                  onChange={(e) => setTravelWeights(prev => ({ ...prev, preferredClass: e.target.value }))}
                  className="w-full p-2 border border-border bg-background rounded-xl text-xs"
                >
                  <option value="1A">1AC (First AC)</option>
                  <option value="2A">2AC (2-tier AC)</option>
                  <option value="3A">3AC (3-tier AC)</option>
                  <option value="SL">SL (Sleeper Class)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <span className="block text-[10px] text-muted-foreground">Routing Metric</span>
                <select 
                  value={travelWeights.priorityType} 
                  onChange={(e) => setTravelWeights(prev => ({ ...prev, priorityType: e.target.value }))}
                  className="w-full p-2 border border-border bg-background rounded-xl text-xs"
                >
                  <option value="comfort">Comfort Index</option>
                  <option value="budget">Cost Saving</option>
                  <option value="speed">Transit Speed</option>
                  <option value="reliability">Punctuality Focus</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <span className="block text-[10px] text-muted-foreground">Boarding Junction</span>
                <select 
                  value={travelWeights.favoriteBoarding} 
                  onChange={(e) => setTravelWeights(prev => ({ ...prev, favoriteBoarding: e.target.value }))}
                  className="w-full p-2 border border-border bg-background rounded-xl text-xs"
                >
                  <option value="NDLS">NDLS (New Delhi)</option>
                  <option value="BPL">BPL (Bhopal)</option>
                  <option value="CSMT">CSMT (Mumbai)</option>
                  <option value="HWH">HWH (Howrah)</option>
                </select>
              </div>
            </div>
          </section>

          {/* AI Travel Insights (spontaneous insights) */}
          <section className="space-y-4">
            <h4 className="text-xs font-bold uppercase text-muted-foreground tracking-wider flex items-center gap-1.5">
              <Zap className="h-4 w-4 text-primary" />
              <span>Proactive AI Travel Insights</span>
            </h4>
            
            {insights.map(item => (
              <div key={item.id} className="p-5 border border-border bg-background rounded-2xl flex gap-3 shadow-sm">
                <div className="h-8 w-8 rounded-lg bg-secondary/15 text-secondary flex items-center justify-center shrink-0 mt-0.5">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div className="space-y-1 text-xs">
                  <span className="font-bold text-foreground block">{item.title}</span>
                  <p className="text-muted-foreground leading-relaxed">{item.content}</p>
                </div>
              </div>
            ))}
          </section>

        </div>

        {/* Right Side: Notification TIMELINE Inbox & checklist */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Checklist Widget */}
          <section className="bg-background border border-border p-5 rounded-3xl space-y-4 shadow-sm">
            <div className="flex items-center gap-2 border-b border-border pb-2.5 text-xs font-bold text-foreground">
              <CheckCircle className="h-4.5 w-4.5 text-success" />
              <span>Active Journey Preparation Tracker</span>
            </div>

            <div className="space-y-3">
              {checklist.map(item => (
                <div 
                  key={item.id} 
                  onClick={() => handleToggleChecklist(item.id)}
                  className="flex items-center gap-3 p-2.5 hover:bg-muted/10 rounded-xl cursor-pointer text-xs transition-colors"
                >
                  <input 
                    type="checkbox" 
                    checked={item.completed} 
                    readOnly
                    className="accent-success"
                  />
                  <span className={`font-medium ${item.completed ? 'line-through text-muted-foreground' : 'text-foreground'}`}>
                    {item.text}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* Notifications Inbox Timeline */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase text-muted-foreground tracking-wider flex items-center gap-1.5">
                <Clock className="h-4.5 w-4.5 text-primary" />
                <span>Alerts Timeline</span>
              </h4>
              <button 
                onClick={handleMarkAllRead}
                className="text-[10px] font-bold text-primary hover:underline cursor-pointer"
              >
                Mark all read
              </button>
            </div>

            {/* Filter buttons */}
            <div className="flex gap-2">
              <button 
                onClick={() => setFilterTab('all')}
                className={`px-3 py-1 text-[10px] font-bold rounded-lg transition-colors cursor-pointer border ${
                  filterTab === 'all' ? 'bg-primary text-primary-foreground border-primary' : 'bg-muted/50 border-border text-muted-foreground hover:text-foreground'
                }`}
              >
                All
              </button>
              <button 
                onClick={() => setFilterTab('unread')}
                className={`px-3 py-1 text-[10px] font-bold rounded-lg transition-colors cursor-pointer border ${
                  filterTab === 'unread' ? 'bg-primary text-primary-foreground border-primary' : 'bg-muted/50 border-border text-muted-foreground hover:text-foreground'
                }`}
              >
                Unread
              </button>
              
              {/* Category Dropdown Filter */}
              <select 
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="ml-auto p-1 text-[9px] font-bold bg-muted/40 border border-border rounded-lg text-foreground focus:outline-none"
              >
                <option value="">All Categories</option>
                {categoryTags.map(tag => <option key={tag} value={tag}>{tag}</option>)}
              </select>
            </div>

            {/* Notification Cards list */}
            <div className="space-y-3">
              {notifications.length === 0 ? (
                <div className="p-10 border border-border border-dashed text-center text-xs text-muted-foreground rounded-2xl bg-muted/5">
                  No alerts inside this timeline tab.
                </div>
              ) : (
                notifications.map(notif => {
                  const borderClass = notif.read ? 'border-border bg-background/40' : 'border-primary bg-background shadow-premium ring-1 ring-primary/5';
                  const priorityColor = notif.priority === 'critical' || notif.priority === 'high' ? 'text-danger bg-danger/10' : 'text-primary bg-primary/15';
                  
                  return (
                    <div 
                      key={notif.id}
                      className={`p-4 border rounded-2xl flex flex-col gap-2 relative transition-all ${borderClass}`}
                    >
                      <div className="flex justify-between items-start gap-4">
                        <div className="space-y-1">
                          <span className="text-xs font-bold text-foreground block">{notif.title}</span>
                          <p className="text-[10px] text-muted-foreground leading-relaxed">{notif.message}</p>
                        </div>
                        
                        {/* Unread indicator / Mark read check */}
                        {!notif.read && (
                          <button 
                            onClick={() => handleMarkAsRead(notif.id)}
                            className="p-1 text-primary hover:bg-primary/10 rounded-lg cursor-pointer shrink-0 mt-0.5"
                            title="Mark as read"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>

                      <div className="flex justify-between items-center text-[8px] font-black tracking-wider text-muted-foreground border-t border-border pt-2 uppercase">
                        <span>{new Date(notif.timestamp).toLocaleDateString()} at {new Date(notif.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        <div className="flex gap-1.5">
                          <span className="px-1.5 py-0.5 rounded bg-muted text-foreground border border-border">{notif.category}</span>
                          <span className={`px-1.5 py-0.5 rounded ${priorityColor}`}>{notif.priority}</span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </section>

        </div>

      </div>

      {/* Info footer warning */}
      <footer className="flex gap-3 bg-muted/20 border border-border p-4 rounded-2xl text-[10px] text-muted-foreground leading-relaxed">
        <Info className="h-4.5 w-4.5 text-primary shrink-0" />
        <p>
          Engagement and Personalized insights are managed on an event-driven listener platform. Toggling quiet hours, channels preferences alerts, and checklists logs modifies SQLite tables locally and is validated against user entitlement scoring algorithms.
        </p>
      </footer>

    </div>
  );
}
