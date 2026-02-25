import React from 'react'
import {
  Box,
  Search,
  AlertCircle,
  FileText,
  BarChart3,
  Lightbulb,
  ArrowRight,
  Zap,
} from 'lucide-react'
import { Button } from './ui/button'

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>
  title: string
  description: string
  hint?: string
  action?: {
    label: string
    onClick: () => void
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = FileText,
  title,
  description,
  hint,
  action,
  secondaryAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
        <Icon className="h-8 w-8 text-primary/60" />
      </div>

      <h3 className="mb-2 text-lg font-semibold text-foreground">{title}</h3>
      <p className="mb-2 max-w-sm text-center text-sm text-muted-foreground">{description}</p>

      {hint && (
        <p className="mb-6 max-w-xs text-center text-xs text-muted-foreground/70 flex items-center gap-1">
          <Zap className="h-3 w-3 flex-shrink-0" />
          {hint}
        </p>
      )}

      {(action || secondaryAction) && (
        <div className="flex items-center gap-3 mt-2">
          {action && (
            <Button onClick={action.onClick}>
              {action.label}
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          )}
          {secondaryAction && (
            <Button variant="ghost" size="sm" onClick={secondaryAction.onClick}>
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

export const EmptyClusterList: React.FC<{ onLoadSample?: () => void }> = ({ onLoadSample }) => (
  <EmptyState
    icon={Box}
    title="No Clusters Yet"
    description="Clusters are groups of related app ideas discovered from real user discussions. They appear automatically after ingesting and processing posts."
    hint="Tip: Load sample data first to see how clustering works."
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
    icon={Search}
    title="No Matches Found"
    description="Your current filters didn't match any results. Try broadening your search or removing some filters."
    hint="Tip: Use fewer keywords for broader results."
    action={
      onClearSearch
        ? {
            label: 'Clear All Filters',
            onClick: onClearSearch,
          }
        : undefined
    }
  />
)

export const EmptyIdeasList: React.FC = () => (
  <EmptyState
    icon={Lightbulb}
    title="No Ideas Extracted"
    description="Ideas are automatically extracted from ingested posts using NLP. Once posts are processed, ideas will appear here with sentiment and quality scores."
    hint="Tip: Run ingestion from the Dashboard to fetch new posts."
  />
)

export const EmptyAnalytics: React.FC = () => (
  <EmptyState
    icon={BarChart3}
    title="Not Enough Data for Analytics"
    description="Analytics require at least a few processed clusters to generate meaningful insights. Load sample data or ingest posts to get started."
    hint="Tip: Analytics update automatically as new data flows in."
  />
)

export const ErrorState: React.FC<{ error: string; onRetry?: () => void }> = ({ error, onRetry }) => (
  <div className="flex flex-col items-center justify-center py-16 px-4">
    <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
      <AlertCircle className="h-8 w-8 text-destructive" />
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
      <td key={`loading-col-${i}`} className="px-6 py-4">
        <div className="h-4 w-3/4 rounded bg-muted"></div>
      </td>
    ))}
  </tr>
)

// Mini empty state for smaller sections
export const MiniEmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="py-8 text-center text-sm text-muted-foreground">{message}</div>
)
