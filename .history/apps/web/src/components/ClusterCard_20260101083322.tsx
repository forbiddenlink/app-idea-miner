import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowTrendingUpIcon, UsersIcon, HeartIcon } from '@heroicons/react/24/outline'
import { HeartIcon as HeartIconSolid } from '@heroicons/react/24/solid'
import type { FC } from 'react'
import type { Cluster } from '@/types'
import { useFavorites } from '@/hooks/useFavorites'
import { EnhancedTooltip } from './EnhancedTooltip'
import { ContextMenu, createClusterContextMenu } from './ContextMenu'

interface ClusterCardProps {
  cluster: Cluster
}

const ClusterCard: FC<ClusterCardProps> = ({ cluster }) => {
  const { isFavorite, toggleFavorite } = useFavorites()
  const favorited = isFavorite(cluster.id)

  const sentimentColor = cluster.avg_sentiment > 0.3
    ? 'text-success-400'
    : cluster.avg_sentiment < -0.3
    ? 'text-danger-400'
    : 'text-slate-400'

  const trendColor = cluster.trend_score > 0.7
    ? 'text-warning-400'
    : 'text-slate-400'

  const handleFavoriteClick = (e: React.MouseEvent) => {
    e.preventDefault() // Don't navigate when clicking star
    e.stopPropagation()
    toggleFavorite(cluster.id)
  }
  // Context menu items
  const contextMenuItems = createClusterContextMenu(
    { id: cluster.id, label: cluster.label },
    () => toggleFavorite(cluster.id, 'cluster'),
    favorited
  )
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      whileHover={{ y: -8, scale: 1.02 }}
      transition={{
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1]
      }}
    >
      <Link
        to={`/clusters/${cluster.id}`}
        className="card p-6 block group relative overflow-hidden"
        aria-label={`View cluster: ${cluster.label} with ${cluster.idea_count} ideas`}
      >
        {/* Gradient Glow Effect on Hover */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-purple-500/10 to-transparent" />
        </div>

        {/* Content */}
        <div className="relative z-10">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-primary-400 group-hover:to-purple-400 transition-all duration-300 line-clamp-2">
                {cluster.label}
              </h3>
            </div>

            <div className="flex items-center gap-2 ml-2 flex-shrink-0">
              {/* Favorite Button */}
              <EnhancedTooltip
                title={favorited ? "Remove from favorites" : "Add to favorites"}
                description="Save clusters you want to track"
              >
                <button
                  onClick={handleFavoriteClick}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                  aria-label={favorited ? "Remove from favorites" : "Add to favorites"}
                >
                  {favorited ? (
                    <HeartIconSolid className="w-5 h-5 text-red-400" />
                  ) : (
                    <HeartIcon className="w-5 h-5 text-slate-400 hover:text-red-400 transition-colors" />
                  )}
                </button>
              </EnhancedTooltip>

              {/* Hot Badge */}
              {cluster.trend_score > 0.7 && (
                <span className="badge badge-warning" role="status" aria-label="Trending cluster">
                  🔥 Hot
                </span>
              )}
            </div>
          </div>

        {/* Keywords */}
        <div className="flex flex-wrap gap-2 mb-4" role="list" aria-label="Cluster keywords">
          {cluster.keywords.slice(0, 4).map((keyword, idx) => (
            <span key={idx} className="badge badge-primary" role="listitem">
              {keyword}
            </span>
          ))}
          {cluster.keywords.length > 4 && (
            <span className="badge bg-slate-700 text-slate-400" role="listitem">
              +{cluster.keywords.length - 4} more
            </span>
          )}
        </div>

        {/* Metrics */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <EnhancedTooltip
              title="Idea Count"
              description="Number of user needs grouped in this cluster"
              metrics={[
                { label: 'Total Ideas', value: cluster.idea_count },
                { label: 'Quality', value: `${(cluster.quality_score * 100).toFixed(0)}%` },
              ]}
            >
              <div className="flex items-center space-x-1 cursor-help">
                <UsersIcon className="w-4 h-4 text-slate-400" aria-hidden="true" />
                <span className="text-slate-300">{cluster.idea_count}</span>
                <span className="sr-only">ideas</span>
              </div>
            </EnhancedTooltip>

            <EnhancedTooltip
              title="Sentiment Analysis"
              description="Average sentiment across all ideas in this cluster"
              metrics={[
                { label: 'Sentiment', value: `${(cluster.avg_sentiment * 100).toFixed(0)}%` },
                { label: 'Tone', value: cluster.avg_sentiment > 0.3 ? 'Positive' : cluster.avg_sentiment < -0.3 ? 'Negative' : 'Neutral' },
              ]}
            >
              <div className={`flex items-center space-x-1 cursor-help ${sentimentColor}`}>
                <span aria-hidden="true">😊</span>
                <span>{(cluster.avg_sentiment * 100).toFixed(0)}%</span>
                <span className="sr-only">positive sentiment</span>
              </div>
            </EnhancedTooltip>
          </div>

          {cluster.trend_score > 0.5 && (
            <EnhancedTooltip
              title="Trend Score"
              description="Indicates how rapidly this cluster is growing"
              metrics={[
                { label: 'Trend', value: `${(cluster.trend_score * 100).toFixed(0)}%` },
                { label: 'Status', value: cluster.trend_score > 0.7 ? 'Hot' : 'Growing' },
              ]}
            >
              <div className={`flex items-center space-x-1 cursor-help ${trendColor}`}>
                <ArrowTrendingUpIcon className="w-4 h-4" aria-hidden="true" />
                <span>{(cluster.trend_score * 100).toFixed(0)}%</span>
                <span className="sr-only">trend score</span>
              </div>
            </EnhancedTooltip>
          )}
        </div>

          {/* Quality Score Bar */}
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
              <span className="font-medium">Quality Score</span>
              <span className="font-bold text-sm">{(cluster.quality_score * 100).toFixed(0)}%</span>
            </div>
            <div className="relative w-full bg-slate-900/50 rounded-full h-2 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${cluster.quality_score * 100}%` }}
                transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
                className="h-full rounded-full relative"
                style={{
                  background: `linear-gradient(90deg,
                    rgb(99, 102, 241) 0%,
                    rgb(168, 85, 247) 50%,
                    rgb(236, 72, 153) 100%)`
                }}
              >
                <div className="absolute inset-0 animate-pulse opacity-50">
                  <div className="h-full bg-gradient-to-r from-transparent via-white/30 to-transparent" />
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>    </ContextMenu>  )
}

export default ClusterCard
