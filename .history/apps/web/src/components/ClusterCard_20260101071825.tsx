import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowTrendingUpIcon, UsersIcon } from '@heroicons/react/24/outline'
import type { FC } from 'react'
import type { Cluster } from '@/types'

interface ClusterCardProps {
  cluster: Cluster
}

const ClusterCard: FC<ClusterCardProps> = ({ cluster }) => {
  const sentimentColor = cluster.avg_sentiment > 0.3
    ? 'text-success-400'
    : cluster.avg_sentiment < -0.3
    ? 'text-danger-400'
    : 'text-slate-400'

  const trendColor = cluster.trend_score > 0.7
    ? 'text-warning-400'
    : 'text-slate-400'

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
            <h3 className="text-xl font-bold text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-primary-400 group-hover:to-purple-400 transition-all duration-300 line-clamp-2">
              {cluster.label}
            </h3>
          {cluster.trend_score > 0.7 && (
            <span className="badge badge-warning ml-2 flex-shrink-0" role="status" aria-label="Trending cluster">
              🔥 Hot
            </span>
          )}
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
            <div className="flex items-center space-x-1" title={`${cluster.idea_count} ideas in this cluster`}>
              <UsersIcon className="w-4 h-4 text-slate-400" aria-hidden="true" />
              <span className="text-slate-300">{cluster.idea_count}</span>
              <span className="sr-only">ideas</span>
            </div>
            <div className={`flex items-center space-x-1 ${sentimentColor}`} title={`Average sentiment: ${(cluster.avg_sentiment * 100).toFixed(0)}%`}>
              <span aria-hidden="true">😊</span>
              <span>{(cluster.avg_sentiment * 100).toFixed(0)}%</span>
              <span className="sr-only">positive sentiment</span>
            </div>
          </div>

          {cluster.trend_score > 0.5 && (
            <div className={`flex items-center space-x-1 ${trendColor}`} title={`Trend score: ${(cluster.trend_score * 100).toFixed(0)}%`}>
              <ArrowTrendingUpIcon className="w-4 h-4" aria-hidden="true" />
              <span>{(cluster.trend_score * 100).toFixed(0)}%</span>
              <span className="sr-only">trend score</span>
            </div>
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
    </motion.div>
  )
}
              >
                <div className="absolute inset-0 animate-pulse opacity-50">
                  <div className="h-full bg-gradient-to-r from-transparent via-white/30 to-transparent" />
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

export default ClusterCard
