import React from 'react';
import { FunnelIcon } from '@heroicons/react/24/outline';

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
    <div className="card w-64 h-fit sticky top-4" role="complementary" aria-label="Filter controls">
      <div className="flex items-center gap-2 mb-4">
        <FunnelIcon className="w-5 h-5 text-primary-400" aria-hidden="true" />
        <h3 className="text-lg font-semibold text-white">Filters</h3>
      </div>

      {/* Sort By */}
      <div className="mb-4">
        <label htmlFor="sort-by-select" className="block text-sm font-medium text-slate-300 mb-2">
          Sort By
        </label>
        <select
          id="sort-by-select"
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
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
          <legend className="block text-sm font-medium text-slate-300 mb-2">
            Order
          </legend>
          <div className="flex gap-2" role="group" aria-label="Sort order">
            <button
              onClick={() => onOrderChange('desc')}
              className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                order === 'desc'
                  ? 'bg-primary-500 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
              aria-pressed={order === 'desc'}
              aria-label="Sort high to low"
            >
              High to Low
            </button>
            <button
              onClick={() => onOrderChange('asc')}
              className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                order === 'asc'
                  ? 'bg-primary-500 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
              aria-pressed={order === 'asc'}
              aria-label="Sort low to high"
            >
              Low to High
            </button>
          </div>
        </fieldset>
      </div>

      {/* Minimum Size */}
      <div className="mb-4">
        <label htmlFor="min-size-input" className="block text-sm font-medium text-slate-300 mb-2">
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
          className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
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
        className="w-full px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors text-sm font-medium"
        aria-label="Reset all filters to default values"
      >
        Reset Filters
      </button>
    </div>
  );
};
