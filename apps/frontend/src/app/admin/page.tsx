'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { 
  Sparkles, 
  ArrowLeft, 
  Check, 
  ChevronRight, 
  Clock, 
  X,
  AlertCircle,
  Zap,
  Info,
  Sliders,
  ShieldCheck,
  Activity,
  ToggleLeft,
  ToggleRight,
  Database,
  Search,
  Filter,
  RefreshCw,
  Terminal,
  Cpu
} from 'lucide-react';

interface MetricNode {
  nodeName: string;
  status: string;
  cpuPercent: number;
  memoryBytes: number;
  latencyMs: number;
  cacheHitRatio: number;
  queueLength: number;
}

interface AnalyticsSnapshot {
  date: string;
  activeUsersCount: number;
  aiMessagesCount: number;
  analysesCount: number;
  revenueAmount: string | number;
  retentionRate: number;
  conversionRatio: number;
}

interface FeatureFlagItem {
  id: string;
  name: string;
  enabled: boolean;
  description: string;
}

interface SystemConfigItem {
  id: string;
  key: string;
  value: string;
  description: string;
}

interface AuditLogItem {
  id: string;
  actorEmail: string;
  action: string;
  details: string;
  requestId: string | null;
  ipAddress: string | null;
  affectedResource: string | null;
  actionResult: string;
  timestamp: string;
}

export default function AdminOperationsHub() {
  const { token, user } = useAuthStore();
  const router = useRouter();

  // Route protection
  const isAdmin = user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN';

  // State managers
  const [loading, setLoading] = useState(true);
  const [healthNodes, setHealthNodes] = useState<MetricNode[]>([]);
  const [analyticsTotals, setAnalyticsTotals] = useState<any>(null);
  const [analyticsHistory, setAnalyticsHistory] = useState<AnalyticsSnapshot[]>([]);
  const [flags, setFlags] = useState<FeatureFlagItem[]>([]);
  const [configs, setConfigs] = useState<SystemConfigItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  
  // Controls
  const [searchQuery, setSearchQuery] = useState('');
  const [configBanner, setConfigBanner] = useState('');
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    if (!isAdmin) {
      return; // Handled by inline check below
    }
    loadAdminMetrics();
  }, [token]);

  const loadAdminMetrics = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      const dashRes = await fetch('http://localhost:5000/api/admin/dashboard', { headers });
      const healthRes = await fetch('http://localhost:5000/api/admin/health', { headers });
      const configRes = await fetch('http://localhost:5000/api/admin/configs', { headers });
      const auditRes = await fetch('http://localhost:5000/api/admin/audit-logs', { headers });

      if (dashRes.ok && healthRes.ok && configRes.ok && auditRes.ok) {
        const dashData = await dashRes.json();
        const healthData = await healthRes.json();
        const configData = await configRes.json();
        const auditData = await auditRes.json();

        setAnalyticsTotals(dashData.totals);
        setAnalyticsHistory(dashData.history);
        setHealthNodes(healthData);
        setFlags(configData.flags);
        setConfigs(configData.configs);
        setAuditLogs(auditData);

        // Populate banner state
        const banner = configData.configs.find((c: any) => c.key === 'banner_announcement');
        if (banner) setConfigBanner(banner.value);
      }
    } catch (err) {
      console.error('Failed to load operational parameters:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFlag = async (name: string, currentEnabled: boolean) => {
    try {
      const res = await fetch('http://localhost:5000/api/admin/feature-flags', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ name, enabled: !currentEnabled })
      });

      if (res.ok) {
        setFlags(prev => prev.map(f => f.name === name ? { ...f, enabled: !currentEnabled } : f));
        setActionMessage({ type: 'success', text: `Feature flag '${name}' updated successfully.` });
        
        // Refresh audit logs
        const auditRes = await fetch('http://localhost:5000/api/admin/audit-logs', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (auditRes.ok) setAuditLogs(await auditRes.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveBanner = async () => {
    try {
      const res = await fetch('http://localhost:5000/api/admin/configs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ key: 'banner_announcement', value: configBanner })
      });

      if (res.ok) {
        setActionMessage({ type: 'success', text: 'System announcement banner config updated.' });
        
        // Refresh audit logs
        const auditRes = await fetch('http://localhost:5000/api/admin/audit-logs', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (auditRes.ok) setAuditLogs(await auditRes.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (!isAdmin) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground py-10 px-4">
        <div className="max-w-md w-full border border-danger/20 bg-danger/5 rounded-3xl p-6 text-center space-y-4 shadow">
          <ShieldCheck className="h-12 w-12 text-danger mx-auto" />
          <h2 className="text-lg font-extrabold tracking-tight text-foreground">Access Denied</h2>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Operations control is restricted. You do not possess the required administrator credentials to view this page.
          </p>
          <button 
            onClick={() => router.push('/chat')}
            className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-xs transition-all cursor-pointer"
          >
            Return to AI Workspace
          </button>
        </div>
      </div>
    );
  }

  if (loading && healthNodes.length === 0) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <div className="text-center space-y-4">
          <Clock className="h-10 w-10 text-primary animate-spin mx-auto" />
          <p className="text-xs font-semibold text-muted-foreground">Bootstrapping operations console...</p>
        </div>
      </div>
    );
  }

  // Format bytes helper
  const formatMB = (bytes: number) => {
    return `${Math.round(bytes / (1024 * 1024))} MB`;
  };

  const filteredLogs = auditLogs.filter(log => 
    log.actorEmail.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.details.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
              Operations & Ecosystem Dashboard
            </h1>
            <p className="text-xs text-muted-foreground">Manage feature toggles, system configs, system health, and audit logs.</p>
          </div>
        </div>

        <button 
          onClick={loadAdminMetrics}
          className="flex items-center gap-1.5 p-2.5 border border-border bg-muted/20 hover:bg-muted/40 text-xs font-bold rounded-xl transition-all cursor-pointer"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </header>

      {/* Action Banner Alerts */}
      {actionMessage && (
        <div className="p-4 border border-success/20 bg-success/5 text-success rounded-2xl flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Check className="h-4 w-4" />
            <span>{actionMessage.text}</span>
          </div>
          <button onClick={() => setActionMessage(null)} className="cursor-pointer">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Overview Analytics KPI Cards Grid */}
      {analyticsTotals && (
        <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="p-5 border border-border bg-background rounded-3xl flex items-center justify-between shadow-sm">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-black tracking-wider block">Total Active Users</span>
              <span className="text-xl font-black mt-1 block">{analyticsTotals.totalUsers}</span>
            </div>
            <div className="h-10 w-10 bg-primary/10 text-primary rounded-2xl flex items-center justify-center font-bold">U</div>
          </div>
          
          <div className="p-5 border border-border bg-background rounded-3xl flex items-center justify-between shadow-sm">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-black tracking-wider block">AI Conversation Logs</span>
              <span className="text-xl font-black mt-1 block">{analyticsTotals.totalChats}</span>
            </div>
            <div className="h-10 w-10 bg-secondary/10 text-secondary rounded-2xl flex items-center justify-center font-bold">AI</div>
          </div>

          <div className="p-5 border border-border bg-background rounded-3xl flex items-center justify-between shadow-sm">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-black tracking-wider block">Waitlist Analyses</span>
              <span className="text-xl font-black mt-1 block">{analyticsTotals.totalAnalyses}</span>
            </div>
            <div className="h-10 w-10 bg-success/10 text-success rounded-2xl flex items-center justify-center font-bold">W</div>
          </div>

          <div className="p-5 border border-border bg-background rounded-3xl flex items-center justify-between shadow-sm">
            <div>
              <span className="text-[10px] text-muted-foreground uppercase font-black tracking-wider block">Ecosystem Revenue</span>
              <span className="text-xl font-black mt-1 block">Rs. {analyticsTotals.totalRevenue}</span>
            </div>
            <div className="h-10 w-10 bg-warning/10 text-warning rounded-2xl flex items-center justify-center font-bold">Rs</div>
          </div>
        </section>
      )}

      {/* Split Dashboard blocks */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left pane: Health telemetry & charts */}
        <div className="lg:col-span-7 space-y-8">
          
          {/* Health Monitor */}
          <section className="bg-muted/10 border border-border p-6 rounded-3xl space-y-6 shadow-sm">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Activity className="h-4.5 w-4.5 text-primary" />
              <h3 className="font-bold text-xs">System Health Telemetry Monitor</h3>
            </div>

            <div className="space-y-4">
              {healthNodes.map(node => (
                <div key={node.nodeName} className="p-3 border border-border bg-background rounded-2xl space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-foreground capitalize">{node.nodeName.replace('_', ' ')}</span>
                    <div className="flex gap-2">
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-success/10 text-success uppercase">
                        {node.status}
                      </span>
                      <span className="text-[10px] text-muted-foreground font-semibold">{node.latencyMs}ms latency</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 text-[10px] text-muted-foreground pt-1">
                    <div>CPU: <span className="font-bold text-foreground">{node.cpuPercent}%</span></div>
                    <div>Memory: <span className="font-bold text-foreground">{formatMB(node.memoryBytes)}</span></div>
                    <div>Hit Ratio: <span className="font-bold text-foreground">{Math.round(node.cacheHitRatio * 100)}%</span></div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* SVG Modular Analytics Time Series chart */}
          {analyticsHistory.length > 0 && (
            <section className="bg-muted/10 border border-border p-6 rounded-3xl space-y-6 shadow-sm">
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <Sliders className="h-4.5 w-4.5 text-primary" />
                <h3 className="font-bold text-xs">Modular Growth Metrics Analytics (Last 7 Days)</h3>
              </div>

              {/* Custom SVG Time-series chart representing growth */}
              <div className="relative h-44 w-full border border-border bg-background rounded-2xl p-4 flex flex-col justify-between">
                <div className="flex justify-between text-[8px] font-black uppercase text-muted-foreground">
                  <span>Revenue Trendline</span>
                  <span>Active Conversions</span>
                </div>

                <svg className="w-full h-24 overflow-visible" viewBox="0 0 600 100">
                  {/* Grid Lines */}
                  <line x1="0" y1="20" x2="600" y2="20" stroke="var(--border)" strokeWidth="0.5" strokeDasharray="3" />
                  <line x1="0" y1="55" x2="600" y2="55" stroke="var(--border)" strokeWidth="0.5" strokeDasharray="3" />
                  <line x1="0" y1="90" x2="600" y2="90" stroke="var(--border)" strokeWidth="0.5" strokeDasharray="3" />

                  {/* SVG Area chart */}
                  <path 
                    d={`M 0 100 L 100 ${90 - analyticsHistory[0].analysesCount} L 200 ${90 - analyticsHistory[1].analysesCount} L 300 ${90 - analyticsHistory[2].analysesCount} L 400 ${90 - analyticsHistory[3].analysesCount} L 500 ${90 - analyticsHistory[4].analysesCount} L 600 ${90 - analyticsHistory[5].analysesCount} L 600 100 Z`}
                    fill="url(#areaGrad)" 
                    opacity="0.15"
                  />

                  {/* SVG Trend Path */}
                  <path 
                    d={`M 0 100 L 100 ${90 - analyticsHistory[0].analysesCount} L 200 ${90 - analyticsHistory[1].analysesCount} L 300 ${90 - analyticsHistory[2].analysesCount} L 400 ${90 - analyticsHistory[3].analysesCount} L 500 ${90 - analyticsHistory[4].analysesCount} L 600 ${90 - analyticsHistory[5].analysesCount}`}
                    fill="none" 
                    stroke="var(--primary)" 
                    strokeWidth="2.5" 
                    strokeLinecap="round"
                  />

                  {/* Gradient definition */}
                  <defs>
                    <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--primary)" />
                      <stop offset="100%" stopColor="transparent" />
                    </linearGradient>
                  </defs>
                </svg>

                <div className="flex justify-between text-[9px] text-muted-foreground font-semibold">
                  {analyticsHistory.map(day => <span key={day.date}>{day.date.slice(5)}</span>)}
                </div>
              </div>
            </section>
          )}

        </div>

        {/* Right pane: Toggles & audit logs */}
        <div className="lg:col-span-5 space-y-8">
          
          {/* Feature Flags & configs */}
          <section className="bg-background border border-border p-5 rounded-3xl space-y-5 shadow-sm">
            <div className="flex items-center gap-2 border-b border-border pb-2.5 text-xs font-bold text-foreground">
              <Zap className="h-4.5 w-4.5 text-primary" />
              <span>Feature Flags Management</span>
            </div>

            <div className="space-y-4">
              {flags.map(flag => (
                <div key={flag.id} className="flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-foreground block">{flag.name.replace(/_/g, ' ')}</span>
                    <p className="text-[10px] text-muted-foreground">{flag.description}</p>
                  </div>
                  <button 
                    onClick={() => handleToggleFlag(flag.name, flag.enabled)}
                    className="text-primary hover:opacity-90 transition-all cursor-pointer"
                  >
                    {flag.enabled ? (
                      <ToggleRight className="h-7 w-7 text-primary" />
                    ) : (
                      <ToggleLeft className="h-7 w-7 text-muted-foreground" />
                    )}
                  </button>
                </div>
              ))}
            </div>

            {/* Config banners inputs */}
            <div className="border-t border-border pt-4 space-y-2">
              <span className="block text-[10px] text-muted-foreground font-bold uppercase tracking-wider">System Announcement banner</span>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={configBanner}
                  onChange={(e) => setConfigBanner(e.target.value)}
                  className="flex-1 p-2.5 border border-border bg-background rounded-xl text-xs"
                />
                <button 
                  onClick={handleSaveBanner}
                  className="px-3 bg-foreground text-background font-bold text-xs rounded-xl cursor-pointer"
                >
                  Save
                </button>
              </div>
            </div>
          </section>

          {/* Audit Logs timelinse */}
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <Terminal className="h-4.5 w-4.5 text-primary" />
              <span className="text-xs font-bold uppercase text-muted-foreground tracking-wider">Ecosystem Audit Trail</span>
            </div>

            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input 
                type="text" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search audit actions or actor email..."
                className="w-full pl-9 pr-4 py-2 border border-border bg-background rounded-xl text-xs focus:outline-none"
              />
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto border border-border bg-muted/5 p-3 rounded-2xl">
              {filteredLogs.length === 0 ? (
                <div className="p-8 text-center text-xs text-muted-foreground">
                  No match found inside immutable audit registries.
                </div>
              ) : (
                filteredLogs.map(log => (
                  <div key={log.id} className="p-3 border border-border bg-background rounded-xl text-[10px] leading-relaxed space-y-1">
                    <div className="flex justify-between items-center font-bold text-foreground">
                      <span>{log.action.replace(/_/g, ' ').toUpperCase()}</span>
                      <span className="px-1.5 py-0.5 rounded bg-success/15 text-success uppercase text-[8px]">
                        {log.actionResult}
                      </span>
                    </div>
                    <div className="text-muted-foreground">Actor: <span className="text-foreground font-semibold">{log.actorEmail}</span></div>
                    <div className="text-muted-foreground">Resource: <span className="text-foreground">{log.affectedResource || 'N/A'}</span></div>
                    <div className="text-muted-foreground bg-muted/40 p-1.5 rounded font-mono text-[9px] mt-1 break-all">
                      {log.details}
                    </div>
                    <div className="text-[8px] text-muted-foreground text-right pt-1">
                      {new Date(log.timestamp).toLocaleDateString()} at {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>

        </div>

      </div>

    </div>
  );
}
