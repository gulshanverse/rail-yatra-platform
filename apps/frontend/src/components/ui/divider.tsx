import { cn } from '@/lib/cn';

export function Divider({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div role="separator" className={cn('h-px w-full bg-border', className)} {...props} />;
}
