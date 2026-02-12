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
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6 hover:border-slate-600 transition-colors"
      role="region"
      aria-label={`${name} statistic`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400" id={`stat-${name.replace(/\s+/g, '-').toLowerCase()}`}>{name}</p>
          <p className="mt-2 text-3xl font-bold text-white" aria-labelledby={`stat-${name.replace(/\s+/g, '-').toLowerCase()}`}>{value}</p>
          {change && (
            <p className="mt-2 text-xs text-slate-500" aria-label={`Change: ${change}`}>{change}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`} aria-hidden="true">
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </motion.div>
  )
}

export default StatCard
