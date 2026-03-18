import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  ExternalLink,
  Link2,
  Share2,
  Download,
  Heart,
  Lightbulb,
  FolderOpen,
  MessageCircle,
} from 'lucide-react';

import { apiClient } from '@/services/api';
import { Idea } from '@/types';
import { IdeaCard } from '@/components/IdeaCard';
import { IdeaCardSkeleton } from '@/components/LoadingSkeleton';
import DataFreshness from '@/components/DataFreshness';
import { useRefreshSettings } from './Settings';
import { useGlobalToast } from '@/contexts/ToastContext';
import { Button } from '@/components/ui/button';
import { cn } from '@/utils/cn';
import { useFavorites } from '@/hooks/useFavorites';

const formatDate = (value?: string): string => {
  if (!value) return 'Unknown';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unknown';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date);
};

const sentimentPillClass = (sentiment: Idea['sentiment']) => {
  if (sentiment === 'positive') return 'bg-success/10 text-success';
  if (sentiment === 'negative') return 'bg-destructive/10 text-destructive';
  return 'bg-muted text-muted-foreground';
};

export default function IdeaDetail() {
  const { id } = useParams<{ id: string }>();
  const toast = useGlobalToast();
  const { isFavorite, toggleFavorite, isMutating } = useFavorites()
  const { enabled: autoRefresh, interval: refreshInterval } = useRefreshSettings();

  const {
    data: idea,
    isLoading,
    isFetching,
    error,
    refetch,
    dataUpdatedAt,
    isRefetching,
  } = useQuery({
    queryKey: ['idea', id],
    queryFn: () => apiClient.getIdeaById(id!),
    enabled: !!id,
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  });

  const clusterId = idea?.cluster?.id ?? idea?.cluster_id;
  const favorited = Boolean(idea?.id && isFavorite(idea.id, 'idea'))
  const { data: relatedIdeas = [], isLoading: relatedLoading } = useQuery({
    queryKey: ['idea', id, 'related', clusterId],
    queryFn: async () => {
      if (!clusterId) return [];
      const response = await apiClient.getIdeas({
        cluster_id: clusterId,
        limit: 8,
        sort_by: 'quality',
        order: 'desc',
      });
      return response.ideas.filter((item) => item.id !== id).slice(0, 4);
    },
    enabled: !!clusterId && !!id,
    refetchInterval: autoRefresh ? refreshInterval * 2 : false,
  });

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(globalThis.location.href);
      toast.success('Idea link copied to clipboard.');
    } catch {
      toast.error('Could not copy link. Please copy from the address bar.');
    }
  };

  const handleExport = () => {
    if (!idea) return;
    const blob = new Blob([JSON.stringify(idea, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const safeId = idea.id.replaceAll(/[^a-zA-Z0-9-_]+/g, '-');
    a.href = url;
    a.download = `idea-${safeId}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Idea exported.');
  };

  if (isLoading) {
    return (
      <div className="app-page max-w-5xl space-y-4">
        <div className="h-8 w-24 rounded bg-muted animate-pulse" />
        <IdeaCardSkeleton />
        <IdeaCardSkeleton />
      </div>
    );
  }

  if (error || !idea) {
    return (
      <div className="app-page max-w-5xl">
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-destructive">
          <p className="font-medium">Failed to load idea details.</p>
          <p className="mt-1 text-sm">The idea may have been removed or is temporarily unavailable.</p>
          <div className="mt-4 flex items-center gap-2">
            <Button variant="outline" onClick={() => void refetch()}>
              Retry
            </Button>
            <Button asChild variant="ghost">
              <Link to="/ideas">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Ideas
              </Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-page max-w-5xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button asChild variant="ghost">
          <Link to="/ideas">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Ideas
          </Link>
        </Button>
        <div className="flex items-center gap-2">
          {dataUpdatedAt > 0 && (
            <DataFreshness dataUpdatedAt={dataUpdatedAt} isRefetching={isRefetching} onRefresh={() => void refetch()} />
          )}
          <Button type="button" variant="outline" size="sm" onClick={handleShare}>
            <Share2 className="mr-2 h-4 w-4" />
            Share
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button
            type="button"
            variant={favorited ? 'default' : 'outline'}
            size="sm"
            disabled={isMutating}
            onClick={() => idea && toggleFavorite(idea.id, 'idea')}
          >
            <Heart className={cn("mr-2 h-4 w-4", favorited && "fill-current")} />
            {favorited ? 'Saved' : 'Save Idea'}
          </Button>
        </div>
      </div>

      {isFetching && !isLoading && (
        <output aria-live="polite" className="inline-flex items-center rounded-xl border border-border/70 bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
          Updating idea…
        </output>
      )}

      <article className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3 min-w-0">
            <div className="inline-flex items-center gap-2 text-xs text-muted-foreground">
              <Lightbulb className="h-3.5 w-3.5" />
              Idea ID: <span className="font-mono">{idea.id}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight break-words">{idea.problem_statement}</h1>
            {idea.context && <p className="text-muted-foreground break-words">{idea.context}</p>}
          </div>
          <div className="flex items-center gap-2">
            <span className={cn('rounded-md px-2.5 py-1 text-xs font-medium capitalize', sentimentPillClass(idea.sentiment))}>
              {idea.sentiment}
            </span>
            <span className="rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
              {(idea.quality_score * 100).toFixed(0)}% quality
            </span>
          </div>
        </div>

        <dl className="mt-6 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div className="rounded-md bg-surface-sunken p-3">
            <dt className="text-muted-foreground">Domain</dt>
            <dd className="mt-1 font-medium">{idea.domain || 'Uncategorized'}</dd>
          </div>
          <div className="rounded-md bg-surface-sunken p-3">
            <dt className="text-muted-foreground">Extracted</dt>
            <dd className="mt-1 font-medium inline-flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" />
              {formatDate(idea.extracted_at)}
            </dd>
          </div>
        </dl>

        <div className="mt-6 flex flex-wrap items-center gap-2">
          {clusterId && (
            <Button asChild variant="outline" size="sm">
              <Link to={`/clusters/${clusterId}`}>
                <FolderOpen className="mr-2 h-4 w-4" />
                Open Cluster
              </Link>
            </Button>
          )}
          {idea.source_url && (
            <Button asChild variant="outline" size="sm">
              <a href={idea.source_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="mr-2 h-4 w-4" />
                View Source
              </a>
            </Button>
          )}
          {!idea.source_url && idea.raw_post?.url && (
            <Button asChild variant="outline" size="sm">
              <a href={idea.raw_post.url} target="_blank" rel="noopener noreferrer">
                <Link2 className="mr-2 h-4 w-4" />
                Open Original Post
              </a>
            </Button>
          )}
        </div>
      </article>

      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold tracking-tight">Related Ideas</h2>
        </div>
        {relatedLoading && (
          <div className="grid grid-cols-1 gap-4">
            <IdeaCardSkeleton />
            <IdeaCardSkeleton />
          </div>
        )}
        {!relatedLoading && relatedIdeas.length === 0 && (
          <div className="card p-6 text-sm text-muted-foreground">
            No related ideas found for this cluster yet.
          </div>
        )}
        {!relatedLoading && relatedIdeas.length > 0 && (
          <div className="grid grid-cols-1 gap-4">
            {relatedIdeas.map((related) => (
              <IdeaCard key={related.id} idea={related} showCluster />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
