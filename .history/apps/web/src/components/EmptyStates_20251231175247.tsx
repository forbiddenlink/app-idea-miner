import React from 'react'
import {
  CubeIcon,
  MagnifyingGlassIcon,
  ExclamationCircleIcon,
  DocumentTextIcon,
  ChartBarIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline'

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = DocumentTextIcon,
  title,
  description,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="flex items-center justify-center w-20 h-20 bg-slate-800 rounded-full mb-6">
        <Icon className="w-10 h-10 text-slate-500" />
      </div>

      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-slate-400 text-center max-w-md mb-6">{description}</p>

      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}

export const EmptyClusterList: React.FC<{ onLoadSample?: () => void }> = ({ onLoadSample }) => (
  <EmptyState
    icon={CubeIcon}
    title="No Clusters Yet"
    description="Start by loading sample data or ingesting posts from RSS feeds. Once processed, clusters will appear here automatically."
    action={
      onLoadSample
        ? {
            label: 'Load Sample Data',
            onClick: onLoadSample,
          }
        : undefined
    }
  />
)

export const EmptySearchResults: React.FC<{ onClearSearch?: () => void }> = ({ onClearSearch }) => (
  <EmptyState
    icon={MagnifyingGlassIcon}
    title="No Results Found"
    description="We couldn't find any clusters matching your search criteria. Try adjusting your filters or search query."
    action={
      onClearSearch
        ? {
            label: 'Clear Search',
            onClick: onClearSearch,
          }
        : undefined
    }
  />
)

export const EmptyIdeasList: React.FC = () => (
  <EmptyState
    icon={LightBulbIcon}
    title="No Ideas Found"
    description="This cluster doesn't have any ideas yet. Ideas are automatically extracted from posts and grouped into clusters."
  />
)

export const EmptyAnalytics: React.FC = () => (
  <EmptyState
    icon={ChartBarIcon}
    title="Not Enough Data"
    description="Analytics will appear once you have processed posts and generated clusters. Load sample data to get started."
  />
)

export const ErrorState: React.FC<{ error: string; onRetry?: () => void }> = ({ error, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-16 px-4">
    <div className="flex items-center justify-center w-20 h-20 bg-red-500/10 rounded-full mb-6">
      <ExclamationCircleIcon className="w-10 h-10 text-red-500" />
    </div>

    <h3 className="text-xl font-semibold text-white mb-2">Something Went Wrong</h3>
    <p className="text-slate-400 text-center max-w-md mb-2">{error}</p>

    {onRetry && (
      <button
        onClick={onRetry}
        className="mt-4 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
      >
        Try Again
      </button>
    )}
  </div>
)

// Inline loading states for tables/lists
export const LoadingRow: React.FC<{ columns?: number }> = ({ columns = 3 }) => (
  <tr className="animate-pulse">
    {Array.from({ length: columns }).map((_, i) => (
      <td key={i} className="px-6 py-4">
        <div className="h-4 bg-slate-700 rounded w-3/4"></div>
      </td>
    ))}
  </tr>
)

// Mini empty state for smaller sections
export const MiniEmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="text-center py-8 text-slate-400 text-sm">{message}</div>
)
