import { useEffect, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { RefreshCw, Clock } from 'lucide-react';
import { cn } from '@/utils/cn';

interface DataFreshnessProps {
  readonly dataUpdatedAt: number;
  readonly isRefetching?: boolean;
  readonly staleThreshold?: number;
  readonly onRefresh?: () => void;
  readonly className?: string;
}

export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;

  if (diff < 30_000) return 'just now';
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

function DataFreshness({
  dataUpdatedAt,
  isRefetching = false,
  staleThreshold = 5 * 60 * 1000,
  onRefresh,
  className,
}: DataFreshnessProps) {
  const reduceMotion = useReducedMotion();
  const [relativeTime, setRelativeTime] = useState(() =>
    formatRelativeTime(dataUpdatedAt)
  );

  useEffect(() => {
    setRelativeTime(formatRelativeTime(dataUpdatedAt));

    const interval = setInterval(() => {
      setRelativeTime(formatRelativeTime(dataUpdatedAt));
    }, 15_000);

    return () => clearInterval(interval);
  }, [dataUpdatedAt]);

  const isStale = Date.now() - dataUpdatedAt >= staleThreshold;
  const isClickable = !!onRefresh;

  return (
    <button
      type="button"
      onClick={onRefresh}
      disabled={!isClickable || isRefetching}
      className={cn(
        'focus-ring inline-flex items-center gap-1.5 rounded-xl border border-border/70 bg-card px-2.5 py-1.5 text-xs font-medium text-muted-foreground shadow-sm transition-colors',
        isClickable && 'cursor-pointer hover:text-foreground',
        !isClickable && 'cursor-default',
        className
      )}
    >
      {isRefetching ? (
        <>
          <RefreshCw className="w-3 h-3 animate-spin" />
          <span>Refreshing…</span>
        </>
      ) : (
        <>
          <motion.span
            className={cn(
              'inline-block h-1.5 w-1.5 rounded-full',
              isStale ? 'bg-amber-500' : 'bg-emerald-500'
            )}
            animate={reduceMotion ? undefined : { opacity: [0.5, 1, 0.5] }}
            transition={reduceMotion ? undefined : { duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          />
          <Clock className="w-3 h-3" />
          <span>Updated {relativeTime}</span>
        </>
      )}
    </button>
  );
}

export default DataFreshness;
