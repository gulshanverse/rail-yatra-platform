import { CheckCircle2, Compass, Sparkles } from 'lucide-react';

const steps = [
  'Understand your constraints',
  'Compare route and train options',
  'Explain the best trade-off',
];

export function HomeIntelligence() {
  return (
    <section className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
      <div>
        <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
          <Compass className="h-3.5 w-3.5" aria-hidden="true" />
          How RailYatra thinks
        </p>
        <h2 className="mt-2 text-xl font-semibold tracking-tight text-white">One journey. Multiple trade-offs. One clear recommendation.</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">RailYatra turns a natural-language request into a decision you can understand and act on.</p>
      </div>
      <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-4">
        <div className="mb-3 flex items-center gap-2 text-xs font-medium text-indigo-200"><Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> Decision flow</div>
        <div className="space-y-2">
          {steps.map((step) => (
            <div key={step} className="flex items-center gap-2 text-xs text-slate-400">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400" aria-hidden="true" />
              {step}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
