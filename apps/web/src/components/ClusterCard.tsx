import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { TrendingUp, Users, Heart, Flame } from 'lucide-react'
import type { FC } from 'react'
import type { Cluster } from '@/types'
import { useFavorites } from '@/hooks/useFavorites'
import { EnhancedTooltip } from './EnhancedTooltip'
import { ContextMenu, createClusterContextMenu } from './ContextMenu'
import { cva } from "class-variance-authority"
import { cn } from "@/utils/cn"

interface ClusterCardProps {
  cluster: Cluster
}

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        warning: "border-transparent bg-yellow-500/15 text-yellow-600 dark:text-yellow-500 hover:bg-yellow-500/25",
        success: "border-transparent bg-green-500/15 text-green-600 dark:text-green-500 hover:bg-green-500/25",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const ClusterCard: FC<ClusterCardProps> = ({ cluster }) => {
  const { isFavorite, toggleFavorite } = useFavorites()
  const favorited = isFavorite(cluster.id)

  const sentimentVariant = cluster.avg_sentiment > 0.3
    ? 'bg-green-500/10 text-green-600 dark:text-green-500'
    : cluster.avg_sentiment < -0.3
      ? 'bg-red-500/10 text-red-600 dark:text-red-500'
      : 'bg-slate-500/10 text-slate-500'

  const trendColor = cluster.trend_score > 0.7
    ? 'text-yellow-600 dark:text-yellow-500'
    : 'text-muted-foreground'

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

  return (
    <ContextMenu items={contextMenuItems}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        whileHover={{ y: -8, scale: 1.02 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      >
        <Link
          to={`/clusters/${cluster.id}`}
          className="group relative block overflow-hidden rounded-xl border bg-card text-card-foreground shadow transition-all hover:shadow-lg hover:border-primary/50"
          aria-label={`View cluster: ${cluster.label}`}
        >
          {/* Content */}
          <div className="p-6">
            {/* Header */}
            <div className="mb-4 flex items-start justify-between gap-4">
              <h3 className="line-clamp-2 text-lg font-semibold tracking-tight transition-colors group-hover:text-primary">
                {cluster.label}
              </h3>

              <div className="flex shrink-0 items-center gap-2">
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
                      "rounded-lg p-1.5 transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
                      favorited ? "text-red-500" : "text-muted-foreground hover:text-red-500"
                    )}
                  >
                    <Heart className={cn("h-4 w-4", favorited && "fill-current")} />
                  </button>
                </EnhancedTooltip>

                {cluster.trend_score > 0.7 && (
                  <span className={cn(badgeVariants({ variant: "warning" }))}>
                    <Flame className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                    Hot
                  </span>
                )}
              </div>
            </div>

            {/* Keywords */}
            <div className="mb-6 flex flex-wrap gap-2">
              {cluster.keywords.slice(0, 4).map((keyword, idx) => (
                <span key={idx} className={cn(badgeVariants({ variant: "secondary" }))}>
                  {keyword}
                </span>
              ))}
              {cluster.keywords.length > 4 && (
                <span className="text-xs text-muted-foreground">
                  +{cluster.keywords.length - 4} more
                </span>
              )}
            </div>

            {/* Metrics */}
            <div className="flex items-center justify-between border-t py-4 text-sm">
              <div className="flex items-center gap-4">
                <EnhancedTooltip
                  title="Idea Count"
                  description="Number of issues in this cluster"
                  metrics={[{ label: 'Total', value: cluster.idea_count }]}
                >
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <Users className="h-4 w-4" />
                    <span>{cluster.idea_count}</span>
                  </div>
                </EnhancedTooltip>

                <div className={cn("flex items-center gap-1.5 rounded px-1.5 py-0.5 font-medium", sentimentVariant)}>
                  <span>{(cluster.avg_sentiment * 100).toFixed(0)}%</span>
                </div>
              </div>

              {cluster.trend_score > 0.5 && (
                <div className={cn("flex items-center gap-1.5 font-medium", trendColor)}>
                  <TrendingUp className="h-4 w-4" />
                  <span>{(cluster.trend_score * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>

            {/* Quality Score Bar */}
            <div className="mt-2 space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Quality Score</span>
                <span className="font-semibold">{(cluster.quality_score * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${cluster.quality_score * 100}%` }}
                  transition={{ duration: 1, delay: 0.2 }}
                  className="h-full bg-gradient-to-r from-primary to-purple-500"
                />
              </div>
            </div>
          </div>
        </Link>
      </motion.div>
    </ContextMenu>
  )
}

export default ClusterCard
