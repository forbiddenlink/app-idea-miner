import { motion } from 'framer-motion'
import type { FC } from 'react'

interface StatCardProps {
  name: string
  value: string
  icon: React.ComponentType<{ className?: string }>
  color: 'primary' | 'success' | 'warning' | 'danger'
  change?: string
}

const colorClasses = {
  primary: 'bg-primary-500/10 text-primary-400',
  success: 'bg-success-500/10 text-success-400',
  warning: 'bg-warning-500/10 text-warning-400',
  danger: 'bg-danger-500/10 text-danger-400',
}

const StatCard: FC<StatCardProps> = ({ name, value, icon: Icon, color, change }) => {
  const gradientColors = {
    primary: 'from-primary-500/20 to-primary-600/10',
    success: 'from-success-500/20 to-success-600/10',
    warning: 'from-warning-500/20 to-warning-600/10',
    danger: 'from-danger-500/20 to-danger-600/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="card p-6 relative overflow-hidden group"
      role="region"
      aria-label={`${name} statistic`}
    >
      {/* Gradient overlay on hover */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradientColors[color]} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

      <div className="flex items-center justify-between relative z-10">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400" id={`stat-${name.replace(/\s+/g, '-').toLowerCase()}`}>{name}</p>
          <p className="mt-2 text-4xl font-bold text-white" aria-labelledby={`stat-${name.replace(/\s+/g, '-').toLowerCase()}`}>{value}</p>
          {change && (
            <p className="mt-2 text-xs text-slate-500" aria-label={`Change: ${change}`}>{change}</p>
          )}
        </div>
        <div className={`p-4 rounded-2xl ${colorClasses[color]} relative overflow-hidden`} aria-hidden="true">
          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
          <Icon className="w-7 h-7 relative z-10" />
        </div>
      </div>
    </motion.div>
  )
}

export default StatCard
