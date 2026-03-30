import { Bookmark, BookmarkX, FolderOpen, Lightbulb } from "lucide-react";
import { Link } from "react-router-dom";
import ClusterCard from "@/components/ClusterCard";
import { IdeaCard } from "@/components/IdeaCard";
import { Button } from "@/components/ui/button";
import { useFavorites } from "@/hooks/useFavorites";
import type { Cluster, Idea } from "@/types";

type SavedItem = {
  id?: string;
  type?: "cluster" | "idea";
  timestamp?: number;
  item_type?: "cluster" | "idea";
  item_id?: string;
  created_at?: string;
  cluster?: Cluster;
  idea?: Idea;
};

const toCluster = (bookmark: SavedItem): Cluster | null => {
  const itemType = bookmark.item_type ?? bookmark.type;
  if (itemType !== "cluster") return null;
  const cluster = bookmark.cluster;

  if (cluster) {
    return {
      id: cluster.id,
      label: cluster.label,
      description: cluster.description ?? "",
      keywords: cluster.keywords ?? [],
      idea_count: cluster.idea_count ?? 0,
      avg_sentiment: cluster.avg_sentiment ?? 0,
      quality_score: cluster.quality_score ?? 0,
      trend_score: cluster.trend_score ?? 0,
      created_at:
        cluster.created_at ??
        bookmark.created_at ??
        new Date(bookmark.timestamp ?? Date.now()).toISOString(),
      updated_at:
        cluster.updated_at ??
        bookmark.created_at ??
        new Date(bookmark.timestamp ?? Date.now()).toISOString(),
    };
  }

  const id = bookmark.item_id ?? bookmark.id;
  if (!id) return null;

  return {
    id,
    label: `Cluster ${id}`,
    description: "",
    keywords: [],
    idea_count: 0,
    avg_sentiment: 0,
    quality_score: 0,
    trend_score: 0,
    created_at:
      bookmark.created_at ??
      new Date(bookmark.timestamp ?? Date.now()).toISOString(),
    updated_at:
      bookmark.created_at ??
      new Date(bookmark.timestamp ?? Date.now()).toISOString(),
  };
};

const toIdea = (bookmark: SavedItem): Idea | null => {
  const itemType = bookmark.item_type ?? bookmark.type;
  if (itemType !== "idea") return null;
  const idea = bookmark.idea;

  if (idea) {
    return {
      id: idea.id,
      raw_post_id:
        idea.raw_post?.id ?? bookmark.item_id ?? bookmark.id ?? "unknown",
      problem_statement: idea.problem_statement,
      context: idea.context ?? undefined,
      sentiment: idea.sentiment,
      sentiment_score: idea.sentiment_score,
      emotions: idea.emotions ?? undefined,
      domain: idea.domain ?? undefined,
      features_mentioned: idea.features_mentioned ?? undefined,
      quality_score: idea.quality_score,
      source_url: idea.raw_post?.url,
      raw_post: idea.raw_post ?? undefined,
      extracted_at:
        idea.extracted_at ??
        bookmark.created_at ??
        new Date(bookmark.timestamp ?? Date.now()).toISOString(),
    };
  }

  const id = bookmark.item_id ?? bookmark.id;
  if (!id) return null;

  return {
    id,
    raw_post_id: id,
    problem_statement: `Saved idea ${id}`,
    sentiment: "neutral",
    sentiment_score: 0,
    quality_score: 0,
    extracted_at:
      bookmark.created_at ??
      new Date(bookmark.timestamp ?? Date.now()).toISOString(),
  };
};

export default function Saved() {
  const {
    favorites,
    getFavorites,
    clearFavorites,
    isLoading,
    error,
    itemCounts,
    isMutating,
  } = useFavorites();

  const clusterBookmarks = getFavorites("cluster") as SavedItem[];
  const ideaBookmarks = getFavorites("idea") as SavedItem[];
  const savedClusters = clusterBookmarks
    .map(toCluster)
    .filter((item): item is Cluster => Boolean(item));
  const savedIdeas = ideaBookmarks
    .map(toIdea)
    .filter((item): item is Idea => Boolean(item));
  const missingClusterCount = clusterBookmarks.length - savedClusters.length;
  const missingIdeaCount = ideaBookmarks.length - savedIdeas.length;

  if (isLoading) {
    return (
      <div className="app-page">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Saved</h1>
        <div className="h-9 w-64 rounded bg-muted/50 animate-pulse" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div
              key={`saved-skeleton-${idx}`}
              className="h-56 rounded-xl border border-border bg-muted/40 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-page">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Saved</h1>
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-5 text-destructive">
          Failed to load saved items. Try refreshing the page.
        </div>
      </div>
    );
  }

  if (favorites.length === 0) {
    return (
      <div className="app-page mx-auto max-w-4xl py-12 sm:py-16">
        <div className="card p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <BookmarkX className="h-6 w-6 text-muted-foreground" />
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight">
            No saved items yet
          </h1>
          <p className="mt-2 text-muted-foreground">
            Save clusters and ideas to build a shortlist you can revisit.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
            <Button asChild variant="outline">
              <Link to="/clusters">Browse Clusters</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/ideas">Browse Ideas</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-page">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Saved
          </h1>
          <p className="text-muted-foreground">
            {itemCounts.cluster} clusters and {itemCounts.idea} ideas saved for
            later.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={isMutating || itemCounts.cluster === 0}
            onClick={() => clearFavorites("cluster")}
          >
            Clear Clusters
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={isMutating || itemCounts.idea === 0}
            onClick={() => clearFavorites("idea")}
          >
            Clear Ideas
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={isMutating || favorites.length === 0}
            onClick={() => clearFavorites()}
          >
            Clear All
          </Button>
        </div>
      </div>

      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <FolderOpen className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold tracking-tight">
            Saved Clusters ({savedClusters.length})
          </h2>
        </div>
        {savedClusters.length > 0 ? (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {savedClusters.map((cluster) => (
              <ClusterCard key={cluster.id} cluster={cluster} />
            ))}
          </div>
        ) : (
          <div className="card p-5 text-sm text-muted-foreground">
            No saved clusters available.
          </div>
        )}
        {missingClusterCount > 0 && (
          <p className="text-xs text-muted-foreground">
            {missingClusterCount} saved cluster reference
            {missingClusterCount > 1 ? "s were" : " was"} not found in current
            data.
          </p>
        )}
      </section>

      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-muted-foreground" />
          <h2 className="text-xl font-semibold tracking-tight">
            Saved Ideas ({savedIdeas.length})
          </h2>
        </div>
        {savedIdeas.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {savedIdeas.map((idea) => (
              <IdeaCard key={idea.id} idea={idea} showCluster />
            ))}
          </div>
        ) : (
          <div className="card p-5 text-sm text-muted-foreground">
            No saved ideas available.
          </div>
        )}
        {missingIdeaCount > 0 && (
          <p className="text-xs text-muted-foreground">
            {missingIdeaCount} saved idea reference
            {missingIdeaCount > 1 ? "s were" : " was"} not found in current
            data.
          </p>
        )}
      </section>

      <div className="card p-3 text-xs text-muted-foreground">
        <Bookmark className="mr-1 inline h-3.5 w-3.5" />
        Saved items are stored per browser scope key and synced through the API.
      </div>
    </div>
  );
}
