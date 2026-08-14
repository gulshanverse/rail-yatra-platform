import { ShieldCheck } from 'lucide-react';

export function HomeTrustStatus() {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/10 bg-emerald-400/[0.04] px-3 py-1.5 text-xs text-slate-400">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
      <ShieldCheck className="h-3.5 w-3.5 text-emerald-300" aria-hidden="true" />
      AI systems operational
    </div>
  );
}
