/**
 * Core Web Vitals Collector for Frontend RUM Monitoring (LCP, FID, CLS, INP, TTFB)
 */

export interface Metric {
  id: string;
  name: string;
  value: number;
  rating?: 'good' | 'needs-improvement' | 'poor';
  delta?: number;
}

export function reportWebVitals(metric: Metric) {
  if (process.env.NODE_ENV !== 'production') {
    console.log(`[Web Vitals] ${metric.name}:`, Math.round(metric.value * 100) / 100);
  }

  // Send to analytics endpoint or PostHog if configured
  const win = typeof window !== 'undefined' ? (window as unknown as { gtag?: (...args: unknown[]) => void }) : null;
  if (win?.gtag) {
    win.gtag('event', metric.name, {
      event_category: 'Web Vitals',
      event_label: metric.id,
      value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
      non_interaction: true,
    });
  }
}
