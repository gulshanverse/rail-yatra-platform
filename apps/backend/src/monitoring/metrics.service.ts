import { Injectable } from '@nestjs/common';

export interface MetricBucket {
  le: number;
  count: number;
}

@Injectable()
export class MetricsService {
  private counters = new Map<string, number>();
  private gauges = new Map<string, number>();
  private histograms = new Map<string, number[]>();
  private readonly defaultBuckets = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0];

  constructor() {
    this.initDefaultMetrics();
  }

  private initDefaultMetrics() {
    this.setGauge('railyatra_backend_up', 1);
    this.incrementCounter('railyatra_backend_http_requests_total', 0);
    this.incrementCounter('railyatra_backend_errors_total', 0);
    this.incrementCounter('railyatra_redis_hits_total', 0);
    this.incrementCounter('railyatra_redis_misses_total', 0);
    this.incrementCounter('railyatra_auth_attempts_total', 0);
    this.incrementCounter('railyatra_auth_failures_total', 0);
    this.incrementCounter('railyatra_payments_processed_total', 0);
    this.incrementCounter('railyatra_ai_requests_total', 0);
  }

  incrementCounter(
    name: string,
    value = 1,
    labels: Record<string, string> = {},
  ) {
    const key = this.formatMetricKey(name, labels);
    const current = this.counters.get(key) || 0;
    this.counters.set(key, current + value);
  }

  setGauge(name: string, value: number, labels: Record<string, string> = {}) {
    const key = this.formatMetricKey(name, labels);
    this.gauges.set(key, value);
  }

  observeHistogram(
    name: string,
    durationSeconds: number,
    labels: Record<string, string> = {},
  ) {
    const key = this.formatMetricKey(name, labels);
    const values = this.histograms.get(key) || [];
    values.push(durationSeconds);
    if (values.length > 2000) {
      this.histograms.set(key, values.slice(-1000));
    } else {
      this.histograms.set(key, values);
    }
  }

  private formatMetricKey(
    name: string,
    labels: Record<string, string>,
  ): string {
    const labelPairs = Object.entries(labels)
      .map(([k, v]) => `${k}="${v}"`)
      .join(',');
    return labelPairs ? `${name}{${labelPairs}}` : name;
  }

  getPrometheusMetrics(): string {
    const lines: string[] = [
      '# HELP railyatra_backend_up System uptime indicator',
      '# TYPE railyatra_backend_up gauge',
      'railyatra_backend_up 1',
      '',
      `# HELP railyatra_node_memory_rss_bytes Node.js process resident set size`,
      `# TYPE railyatra_node_memory_rss_bytes gauge`,
      `railyatra_node_memory_rss_bytes ${process.memoryUsage().rss}`,
      '',
      `# HELP railyatra_node_heap_used_bytes Node.js heap memory used`,
      `# TYPE railyatra_node_heap_used_bytes gauge`,
      `railyatra_node_heap_used_bytes ${process.memoryUsage().heapUsed}`,
      '',
    ];

    // Export Counters
    lines.push('# HELP railyatra_counters Application counter metrics');
    lines.push('# TYPE railyatra_counters counter');
    for (const [key, val] of this.counters.entries()) {
      lines.push(`${key} ${val}`);
    }

    // Export Gauges
    lines.push('');
    lines.push('# HELP railyatra_gauges Application gauge metrics');
    lines.push('# TYPE railyatra_gauges gauge');
    for (const [key, val] of this.gauges.entries()) {
      lines.push(`${key} ${val}`);
    }

    // Export Histograms
    lines.push('');
    lines.push('# HELP railyatra_histograms Application latency histograms');
    lines.push('# TYPE railyatra_histograms histogram');
    for (const [key, values] of this.histograms.entries()) {
      if (values.length === 0) continue;
      const count = values.length;
      const sum = values.reduce((a, b) => a + b, 0);

      for (const bucket of this.defaultBuckets) {
        const bucketCount = values.filter((v) => v <= bucket).length;
        const bucketKey = key.includes('{')
          ? key.replace('{', `{le="${bucket}",`)
          : `${key}{le="${bucket}"}`;
        lines.push(`${bucketKey}_bucket ${bucketCount}`);
      }
      const infKey = key.includes('{')
        ? key.replace('{', `{le="+Inf",`)
        : `${key}{le="+Inf"}`;
      lines.push(`${infKey}_bucket ${count}`);
      lines.push(`${key}_sum ${sum.toFixed(4)}`);
      lines.push(`${key}_count ${count}`);
    }

    return lines.join('\n') + '\n';
  }
}
