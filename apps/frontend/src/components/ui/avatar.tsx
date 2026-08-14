import * as React from 'react';
import Image from 'next/image';
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
        <Image
          src={src}
          alt={alt}
          fill
          sizes="40px"
          unoptimized
          className="object-cover"
          onError={() => setFailed(true)}
        />
      ) : (
        <span aria-hidden="true">{fallback.slice(0, 2).toUpperCase()}</span>
      )}
    </div>
  );
}
