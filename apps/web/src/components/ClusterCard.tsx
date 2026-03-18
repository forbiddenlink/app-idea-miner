import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { TrendingUp, Heart } from 'lucide-react'
import type { FC } from 'react'
import type { Cluster } from '@/types'
import { useFavorites } from '@/hooks/useFavorites'
import { EnhancedTooltip } from './EnhancedTooltip'
import { ContextMenu, createClusterContextMenu } from './ContextMenu'
import { cn } from "@/utils/cn"

interface ClusterCardProps {
  cluster: Cluster
}

const getSentimentLabel = (score: number): string => {
  if (score > 0.3) return 'positive';
  if (score < -0.3) return 'negative';
  return 'neutral';
};

const ClusterCard: FC<ClusterCardProps> = ({ cluster }) => {
  const { isFavorite, toggleFavorite } = useFavorites()
  const favorited = isFavorite(cluster.id)

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    toggleFavorite(cluster.id)
  }

  const contextMenuItems = createClusterContextMenu(
    { id: cluster.id, label: cluster.label },
    () => toggleFavorite(cluster.id, 'cluster'),
    favorited
  )

  const sentimentDisplay = `${(cluster.avg_sentiment * 100).toFixed(0)}%`
  const sentimentLabel = getSentimentLabel(cluster.avg_sentiment)

  const isHot = cluster.trend_score > 0.7

  return (
    <ContextMenu items={contextMenuItems}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Link
          to={`/clusters/${cluster.id}`}
          className="group focus-ring card card-hover relative block border-border/80 p-5"
          aria-label={`View cluster: ${cluster.label}`}
        >
          {/* Header */}
          <div className="mb-3 flex items-start justify-between gap-3">
            <h3 className="line-clamp-2 text-base font-semibold leading-snug transition-colors group-hover:text-primary">
              {cluster.label}
            </h3>

            <EnhancedTooltip
              title={favorited ? "Remove from favorites" : "Add to favorites"}
              description="Save clusters you want to track"
            >
              <button
                type="button"
                onClick={handleFavoriteClick}
                aria-pressed={!!favorited}
                aria-label={favorited ? `Remove ${cluster.label} from favorites` : `Add ${cluster.label} to favorites`}
                className={cn(
                  "focus-ring shrink-0 rounded-lg p-1.5 transition-colors hover:bg-accent",
                  favorited ? "text-red-500" : "text-muted-foreground hover:text-red-400"
                )}
              >
                <Heart className={cn("h-4 w-4", favorited && "fill-current")} />
              </button>
            </EnhancedTooltip>
          </div>

          {/* Keywords - inline text, not chips */}
          <p className="mb-4 text-sm leading-relaxed text-muted-foreground">
            {cluster.keywords.slice(0, 3).join(' · ')}
            {cluster.keywords.length > 3 && (
              <span className="ml-1 opacity-60">+{cluster.keywords.length - 3}</span>
            )}
          </p>

          {/* Metrics row */}
          <div className="flex items-center gap-3 border-t border-border/70 pt-3 text-sm text-muted-foreground">
            <span>
              <span className="font-medium text-foreground">{cluster.idea_count}</span>
              {' '}ideas
            </span>

            <span className="text-border">·</span>

            <span className={cn(
              cluster.avg_sentiment > 0.3 && "text-success",
              cluster.avg_sentiment < -0.3 && "text-destructive"
            )}>
              {sentimentDisplay} {sentimentLabel}
            </span>

            {isHot && (
              <>
                <span className="text-border">·</span>
                <span className="flex items-center gap-1 text-warning">
                  <TrendingUp className="h-3.5 w-3.5" />
                  Hot
                </span>
              </>
            )}
          </div>
        </Link>
      </motion.div>
    </ContextMenu>
  )
}

export default ClusterCard
