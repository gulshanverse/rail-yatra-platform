import * as React from 'react';
import { cn } from '@/lib/cn';

export interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string;
  alt?: string;
  fallback?: string;
}

export function Avatar({ className, src, alt = '', fallback = '?', ...props }: AvatarProps) {
  const [failed, setFailed] = React.useState(false);

  return (
    <div
      className={cn(
        'relative flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-full border border-border bg-interactive text-sm font-semibold text-foreground',
        className,
      )}
      {...props}
    >
      {src && !failed ? (
        // Avatar accepts user/provider URLs, so Next Image remote-host configuration
        // would unnecessarily couple this primitive to deployment configuration.
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt={alt} className="h-full w-full object-cover" onError={() => setFailed(true)} />
      ) : (
        <span aria-hidden="true">{fallback.slice(0, 2).toUpperCase()}</span>
      )}
    </div>
  );
}
