import { cn } from '@/lib/cn';

export function ShellSpacer({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn('h-16 md:hidden', className)} />;
}
