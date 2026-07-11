'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../store/authStore';
import { API_BASE_URL } from '../../lib/api';
import { 
  Sparkles, 
  ArrowLeft, 
  Check, 
  CreditCard, 
  Gauge, 
  Download, 
  Clock, 
  X,
  AlertCircle,
  Info
} from 'lucide-react';

interface BillingInvoice {
  id: string;
  invoiceNumber: string;
  amount: number;
  currency: string;
  status: string;
  createdAt: string;
}

interface SubscriptionDetails {
  tier: string;
  expiry: string | null;
  status: string;
  creditsRemaining: number;
  dailyChatsUsed: number;
  activePnrsCount: number;
  savedRoutesCount: number;
  entitlements: {
    tierName: string;
    price: number;
    currency: string;
    monthlyCreditsLimit: number;
    dailyMessagesLimit: number;
    pnrMonitorLimit: number;
    savedRoutesLimit: number;
    features: string[];
  };
}

export default function SubscriptionHub() {
  const { token } = useAuthStore();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [subDetails, setSubDetails] = useState<SubscriptionDetails | null>(null);
  const [invoices, setInvoices] = useState<BillingInvoice[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const loadBillingData = useCallback(async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      const subRes = await fetch(`${API_BASE_URL}/api/monetization/subscription`, { headers });
      const invoiceRes = await fetch(`${API_BASE_URL}/api/monetization/invoices`, { headers });

      if (subRes.ok && invoiceRes.ok) {
        const subData = await subRes.json();
        const invoiceData = await invoiceRes.json();
        setSubDetails(subData);
        setInvoices(invoiceData);
      }
    } catch (err) {
      console.error('Failed to load billing metrics:', err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      router.push('/login');
    } else {
      const timer = setTimeout(() => {
        void loadBillingData();
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [token, router, loadBillingData]);

  const handleCheckout = async (planName: string) => {
    setCheckoutLoading(planName);
    setMessage(null);
    try {
      // 1. Request Order creation from checkout API
      const res = await fetch(`${API_BASE_URL}/api/monetization/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ planName, gateway: 'stripe' }),
      });

      if (!res.ok) {
        throw new Error('Checkout initialization failed.');
      }

      const orderData = await res.json();

      // 2. Simulate payment processing and webhook trigger
      // In development sandbox, we trigger the webhook directly to auto-complete the payment
      const webhookRes = await fetch(`${API_BASE_URL}/api/monetization/webhooks/stripe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-signature': 'stripe_test_sig',
        },
        body: JSON.stringify({
          event: 'checkout.session.completed',
          id: orderData.orderId,
        }),
      });

      if (webhookRes.ok) {
        setMessage({ type: 'success', text: `Success! Subscribed to ${planName} Plan.` });
        await loadBillingData();
      } else {
        throw new Error('Webhook reconciliation failed.');
      }

    } catch (err) {
      console.error(err);
      const message = err instanceof Error ? err.message : 'Checkout failed. Please try again.';
      setMessage({ type: 'error', text: message });
    } finally {
      setCheckoutLoading(null);
    }
  };

  const calculateProgress = (used: number, limit: number) => {
    if (limit >= 999) return 5; // Unlimited representation
    return Math.min(100, Math.round((used / limit) * 100));
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background text-foreground">
        <div className="text-center space-y-4">
          <Clock className="h-10 w-10 text-primary animate-spin mx-auto" />
          <p className="text-xs font-semibold text-muted-foreground">Loading subscriptions cockpit...</p>
        </div>
      </div>
    );
  }

  const currentTier = subDetails?.tier || 'FREE';

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
              Monetization & Plans
            </h1>
            <p className="text-xs text-muted-foreground">Manage subscriptions, audit usage, and download invoices.</p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-primary/10 border border-primary/20 text-primary px-3.5 py-1.5 rounded-xl text-xs font-bold">
          <Sparkles className="h-4 w-4" />
          <span>Active Plan: {currentTier}</span>
        </div>
      </header>

      {/* Message Notifications */}
      {message && (
        <div className={`p-4 border rounded-2xl flex items-start gap-3 text-xs ${
          message.type === 'success' ? 'bg-success/5 border-success/20 text-success' : 'bg-danger/5 border-danger/20 text-danger'
        }`}>
          <AlertCircle className="h-4.5 w-4.5 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold block">{message.type === 'success' ? 'Completed' : 'Error'}</span>
            <p>{message.text}</p>
          </div>
          <button onClick={() => setMessage(null)} className="cursor-pointer opacity-70 hover:opacity-100">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Quotas & Usage Dashboard */}
      {subDetails && (
        <section className="bg-muted/10 border border-border p-6 rounded-3xl space-y-6 shadow-sm">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <Gauge className="h-5 w-5 text-primary" />
            <h3 className="font-bold text-sm">Active Plan Quota Utilization</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Daily Chats */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-muted-foreground">Daily Messages</span>
                <span className="font-bold text-foreground">
                  {subDetails.dailyChatsUsed} / {subDetails.entitlements.dailyMessagesLimit >= 999 ? 'Unlimited' : subDetails.entitlements.dailyMessagesLimit}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${calculateProgress(subDetails.dailyChatsUsed, subDetails.entitlements.dailyMessagesLimit)}%` }}
                />
              </div>
            </div>

            {/* AI Credits */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-muted-foreground">Analysis Credits</span>
                <span className="font-bold text-foreground">
                  {subDetails.creditsRemaining} / {subDetails.entitlements.monthlyCreditsLimit >= 999 ? 'Unlimited' : subDetails.entitlements.monthlyCreditsLimit}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-secondary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${calculateProgress(subDetails.entitlements.monthlyCreditsLimit - subDetails.creditsRemaining, subDetails.entitlements.monthlyCreditsLimit)}%` }}
                />
              </div>
            </div>

            {/* PNR History limit */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-muted-foreground">PNR Monitors</span>
                <span className="font-bold text-foreground">
                  {subDetails.activePnrsCount} / {subDetails.entitlements.pnrMonitorLimit >= 999 ? 'Unlimited' : subDetails.entitlements.pnrMonitorLimit}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-success h-2 rounded-full transition-all duration-300"
                  style={{ width: `${calculateProgress(subDetails.activePnrsCount, subDetails.entitlements.pnrMonitorLimit)}%` }}
                />
              </div>
            </div>

            {/* Saved routes limit */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="font-medium text-muted-foreground">Saved Routes</span>
                <span className="font-bold text-foreground">
                  {subDetails.savedRoutesCount} / {subDetails.entitlements.savedRoutesLimit >= 999 ? 'Unlimited' : subDetails.entitlements.savedRoutesLimit}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div 
                  className="bg-warning h-2 rounded-full transition-all duration-300"
                  style={{ width: `${calculateProgress(subDetails.savedRoutesCount, subDetails.entitlements.savedRoutesLimit)}%` }}
                />
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Plans Comparison Grid */}
      <section className="space-y-6">
        <h3 className="font-bold text-sm border-b border-border pb-3 flex items-center gap-2">
          <CreditCard className="h-4.5 w-4.5 text-primary" />
          <span>Select Your RailYatra Subscription</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* FREE PLAN */}
          <div className={`p-6 border rounded-3xl flex flex-col gap-6 bg-background ${currentTier === 'FREE' ? 'border-primary shadow' : 'border-border'}`}>
            <div className="space-y-2">
              <h4 className="font-extrabold text-base">Free Sandbox</h4>
              <p className="text-xs text-muted-foreground">Basic AI queries for casual travelers.</p>
              <div className="pt-3">
                <span className="text-2xl font-black">Rs. 0</span>
                <span className="text-xs text-muted-foreground"> / month</span>
              </div>
            </div>
            <button 
              disabled={currentTier === 'FREE' || checkoutLoading !== null}
              className="w-full py-2.5 rounded-xl border border-border font-semibold text-xs transition-all disabled:opacity-40 cursor-pointer"
            >
              {currentTier === 'FREE' ? 'Current Active Plan' : 'Free Default'}
            </button>
            <ul className="space-y-2.5 text-xs text-muted-foreground border-t border-border pt-4">
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> 10 Chat Messages / day</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> 3 AI analysis runs</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> 2 Active PNR Monitors</li>
            </ul>
          </div>

          {/* PREMIUM PLAN */}
          <div className={`p-6 border rounded-3xl flex flex-col gap-6 relative bg-background ${currentTier === 'PREMIUM' ? 'border-primary shadow' : 'border-border'}`}>
            <div className="absolute -top-3 right-6 bg-primary text-primary-foreground text-[9px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full">
              Popular Choice
            </div>
            <div className="space-y-2">
              <h4 className="font-extrabold text-base">Premium Travel</h4>
              <p className="text-xs text-muted-foreground">Perfect for frequent railway commuters.</p>
              <div className="pt-3">
                <span className="text-2xl font-black">Rs. 299</span>
                <span className="text-xs text-muted-foreground"> / month</span>
              </div>
            </div>
            <button 
              onClick={() => handleCheckout('PREMIUM')}
              disabled={currentTier === 'PREMIUM' || checkoutLoading !== null}
              className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/95 transition-all disabled:opacity-40 cursor-pointer"
            >
              {checkoutLoading === 'PREMIUM' ? 'Processing Transaction...' : (currentTier === 'PREMIUM' ? 'Current Active Plan' : 'Upgrade to Premium')}
            </button>
            <ul className="space-y-2.5 text-xs text-muted-foreground border-t border-border pt-4">
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> 100 Chat Messages / day</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> 30 Journey analyses</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> 20 PNR Active Monitors</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> Dynamic Scoring sliders</li>
            </ul>
          </div>

          {/* PREMIUM PLUS PLAN */}
          <div className={`p-6 border rounded-3xl flex flex-col gap-6 bg-background ${currentTier === 'PREMIUM_PLUS' ? 'border-primary shadow' : 'border-border'}`}>
            <div className="space-y-2">
              <h4 className="font-extrabold text-base">Premium Plus Pro</h4>
              <p className="text-xs text-muted-foreground">Complete priority node access for power travelers.</p>
              <div className="pt-3">
                <span className="text-2xl font-black">Rs. 599</span>
                <span className="text-xs text-muted-foreground"> / month</span>
              </div>
            </div>
            <button 
              onClick={() => handleCheckout('PREMIUM_PLUS')}
              disabled={currentTier === 'PREMIUM_PLUS' || checkoutLoading !== null}
              className="w-full py-2.5 rounded-xl bg-foreground text-background font-semibold text-xs hover:opacity-90 transition-all disabled:opacity-40 cursor-pointer"
            >
              {checkoutLoading === 'PREMIUM_PLUS' ? 'Processing Transaction...' : (currentTier === 'PREMIUM_PLUS' ? 'Current Active Plan' : 'Upgrade to Premium Plus')}
            </button>
            <ul className="space-y-2.5 text-xs text-muted-foreground border-t border-border pt-4">
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> Unlimited Chat Messages</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> Unlimited Journey analyses</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> Unlimited PNR Monitors</li>
              <li className="flex items-center gap-2"><Check className="h-3.5 w-3.5 text-success shrink-0" /> Dedicated Priority Core Node</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Invoices & Billing History */}
      <section className="space-y-6">
        <h3 className="font-bold text-sm border-b border-border pb-3 flex items-center gap-2">
          <Clock className="h-4.5 w-4.5 text-primary" />
          <span>Billing History</span>
        </h3>

        {invoices.length === 0 ? (
          <div className="p-6 border border-border bg-muted/10 rounded-2xl text-center text-xs text-muted-foreground">
            No previous transaction records found. Upgrade to Premium to generate invoices.
          </div>
        ) : (
          <div className="border border-border rounded-2xl overflow-hidden bg-background">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-muted/45 border-b border-border text-muted-foreground">
                  <th className="p-3.5 font-bold">Invoice Number</th>
                  <th className="p-3.5 font-bold">Date</th>
                  <th className="p-3.5 font-bold">Amount</th>
                  <th className="p-3.5 font-bold">Status</th>
                  <th className="p-3.5 font-bold text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id} className="border-b border-border hover:bg-muted/10">
                    <td className="p-3.5 font-bold text-foreground">{inv.invoiceNumber}</td>
                    <td className="p-3.5 text-muted-foreground">{new Date(inv.createdAt).toLocaleDateString()}</td>
                    <td className="p-3.5 font-bold text-foreground">Rs. {inv.amount}</td>
                    <td className="p-3.5">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        inv.status === 'paid' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                      }`}>{inv.status.toUpperCase()}</span>
                    </td>
                    <td className="p-3.5 text-right">
                      <button 
                        onClick={() => alert(`Downloading ${inv.invoiceNumber}.pdf... (Simulated file download)`)}
                        className="p-1.5 text-primary hover:bg-primary/10 rounded-lg cursor-pointer"
                        title="Download Invoice PDF"
                      >
                        <Download className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Info Warning */}
      <footer className="flex gap-3 bg-muted/20 border border-border p-4 rounded-2xl text-[10px] text-muted-foreground leading-relaxed">
        <Info className="h-4.5 w-4.5 text-primary shrink-0" />
        <p>
          RailYatra handles subscription validations on a configuration-driven authorization gate. In sandbox development mode, upgrade checks and payment callbacks are safely simulated to verify end-to-end webhook synchronization pipelines without charge verification.
        </p>
      </footer>

    </div>
  );
}
