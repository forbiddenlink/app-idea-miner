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
  const sentimentLabel = cluster.avg_sentiment > 0.3
    ? 'positive'
    : cluster.avg_sentiment < -0.3
      ? 'negative'
      : 'neutral'

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
          className="group relative block rounded-lg border border-border bg-card p-5 transition-colors hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
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
                aria-pressed={favorited}
                aria-label={favorited ? `Remove ${cluster.label} from favorites` : `Add ${cluster.label} to favorites`}
                className={cn(
                  "shrink-0 rounded p-1 transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                  favorited ? "text-red-500" : "text-muted-foreground hover:text-red-400"
                )}
              >
                <Heart className={cn("h-4 w-4", favorited && "fill-current")} />
              </button>
            </EnhancedTooltip>
          </div>

          {/* Keywords - inline text, not chips */}
          <p className="mb-4 text-sm text-muted-foreground">
            {cluster.keywords.slice(0, 3).join(' · ')}
            {cluster.keywords.length > 3 && (
              <span className="ml-1 opacity-60">+{cluster.keywords.length - 3}</span>
            )}
          </p>

          {/* Metrics row */}
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
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
