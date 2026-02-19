import React from 'react';
import { FunnelIcon } from '@heroicons/react/24/outline';
import { cn } from '@/utils/cn';

interface FilterSidebarProps {
  sortBy: string;
  order: string;
  onSortChange: (sortBy: string) => void;
  onOrderChange: (order: string) => void;
  minSize?: number;
  onMinSizeChange: (size: number | undefined) => void;
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  sortBy,
  order,
  onSortChange,
  onOrderChange,
  minSize,
  onMinSizeChange,
}) => {
  return (
    <div className="w-64 shrink-0 rounded-lg border border-border bg-card p-5" role="complementary" aria-label="Filter controls">
      <div className="mb-5 flex items-center gap-2">
        <FunnelIcon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        <h3 className="text-sm font-semibold text-foreground">Filters</h3>
      </div>

      {/* Sort By */}
      <div className="mb-4">
        <label htmlFor="sort-by-select" className="mb-2 block text-sm font-medium text-muted-foreground">
          Sort By
        </label>
        <select
          id="sort-by-select"
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          aria-label="Select sorting criteria"
        >
          <option value="size">Size (Idea Count)</option>
          <option value="quality">Quality Score</option>
          <option value="sentiment">Sentiment</option>
          <option value="trend">Trend Score</option>
          <option value="created_at">Recently Created</option>
        </select>
      </div>

      {/* Order */}
      <div className="mb-4">
        <fieldset>
          <legend className="mb-2 block text-sm font-medium text-muted-foreground">
            Order
          </legend>
          <div className="flex gap-2" role="group" aria-label="Sort order">
            <button
              onClick={() => onOrderChange('desc')}
              className={cn(
                "flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                order === 'desc'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
              )}
              aria-pressed={order === 'desc'}
              aria-label="Sort high to low"
            >
              High to Low
            </button>
            <button
              onClick={() => onOrderChange('asc')}
              className={cn(
                "flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                order === 'asc'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground'
              )}
              aria-pressed={order === 'asc'}
              aria-label="Sort low to high"
            >
              Low to High
            </button>
          </div>
        </fieldset>
      </div>

      {/* Minimum Size */}
      <div className="mb-5">
        <label htmlFor="min-size-input" className="mb-2 block text-sm font-medium text-muted-foreground">
          Minimum Ideas
        </label>
        <input
          id="min-size-input"
          type="number"
          value={minSize || ''}
          onChange={(e) =>
            onMinSizeChange(e.target.value ? parseInt(e.target.value) : undefined)
          }
          placeholder="Any size"
          min="1"
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          aria-label="Minimum number of ideas in cluster"
        />
      </div>

      {/* Reset Button */}
      <button
        onClick={() => {
          onSortChange('size');
          onOrderChange('desc');
          onMinSizeChange(undefined);
        }}
        className="w-full rounded-md bg-muted px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground"
        aria-label="Reset all filters to default values"
      >
        Reset Filters
      </button>
    </div>
  );
};
