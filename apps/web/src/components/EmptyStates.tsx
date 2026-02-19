import React from 'react'
import {
  CubeIcon,
  MagnifyingGlassIcon,
  ExclamationCircleIcon,
  DocumentTextIcon,
  ChartBarIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline'
import { Button } from './ui/button'

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
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>

      <h3 className="mb-2 text-lg font-semibold text-foreground">{title}</h3>
      <p className="mb-6 max-w-sm text-center text-sm text-muted-foreground">{description}</p>

      {action && (
        <Button onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  )
}

export const EmptyClusterList: React.FC<{ onLoadSample?: () => void }> = ({ onLoadSample }) => (
  <EmptyState
    icon={CubeIcon}
    title="No Clusters Yet"
    description="Start by loading sample data or ingesting posts from RSS feeds. Clusters will appear here automatically once processed."
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
    description="We couldn't find any clusters matching your search. Try adjusting your filters or search query."
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
    description="This cluster doesn't have any ideas yet. Ideas are extracted from posts and grouped into clusters."
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
    <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
      <ExclamationCircleIcon className="h-8 w-8 text-destructive" />
    </div>

    <h3 className="mb-2 text-lg font-semibold text-foreground">Something Went Wrong</h3>
    <p className="mb-2 max-w-sm text-center text-sm text-muted-foreground">{error}</p>

    {onRetry && (
      <Button variant="secondary" onClick={onRetry} className="mt-4">
        Try Again
      </Button>
    )}
  </div>
)

// Inline loading states for tables/lists
export const LoadingRow: React.FC<{ columns?: number }> = ({ columns = 3 }) => (
  <tr className="animate-pulse">
    {Array.from({ length: columns }).map((_, i) => (
      <td key={i} className="px-6 py-4">
        <div className="h-4 w-3/4 rounded bg-muted"></div>
      </td>
    ))}
  </tr>
)

// Mini empty state for smaller sections
export const MiniEmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="py-8 text-center text-sm text-muted-foreground">{message}</div>
)
