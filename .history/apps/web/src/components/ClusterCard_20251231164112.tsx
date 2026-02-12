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
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Link
        to={`/clusters/${cluster.id}`}
        className="card p-6 block hover:border-primary-500/50 transition-all group"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-semibold text-white group-hover:text-primary-400 transition-colors line-clamp-2">
            {cluster.label}
          </h3>
          {cluster.trend_score > 0.7 && (
            <span className="badge badge-warning ml-2 flex-shrink-0">
              🔥 Hot
            </span>
          )}
        </div>

        {/* Keywords */}
        <div className="flex flex-wrap gap-2 mb-4">
          {cluster.keywords.slice(0, 4).map((keyword, idx) => (
            <span key={idx} className="badge badge-primary">
              {keyword}
            </span>
          ))}
          {cluster.keywords.length > 4 && (
            <span className="badge bg-slate-700 text-slate-400">
              +{cluster.keywords.length - 4} more
            </span>
          )}
        </div>

        {/* Metrics */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <UsersIcon className="w-4 h-4 text-slate-400" />
              <span className="text-slate-300">{cluster.idea_count}</span>
            </div>
            <div className={`flex items-center space-x-1 ${sentimentColor}`}>
              <span>😊</span>
              <span>{(cluster.avg_sentiment * 100).toFixed(0)}%</span>
            </div>
          </div>

          {cluster.trend_score > 0.5 && (
            <div className={`flex items-center space-x-1 ${trendColor}`}>
              <ArrowTrendingUpIcon className="w-4 h-4" />
              <span>{(cluster.trend_score * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>

        {/* Quality Score Bar */}
        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>Quality Score</span>
            <span>{(cluster.quality_score * 100).toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${cluster.quality_score * 100}%` }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full"
            />
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

export default ClusterCard
