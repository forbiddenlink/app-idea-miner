import { cn } from "@/utils/cn";
import { Filter } from "lucide-react";
import React from "react";

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
    <div className="card w-64 shrink-0 p-5" aria-label="Filter controls">
      <div className="mb-5 flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        <h2 className="text-sm font-semibold uppercase tracking-[0.1em] text-foreground">
          Filters
        </h2>
      </div>

      {/* Sort By */}
      <div className="mb-4">
        <label
          htmlFor="sort-by-select"
          className="mb-2 block text-sm font-medium text-muted-foreground"
        >
          Sort By
        </label>
        <select
          id="sort-by-select"
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          onBlur={(e) => onSortChange(e.target.value)}
          className="field-control"
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
          <div className="flex gap-2" aria-label="Sort order">
            <button
              type="button"
              onClick={() => onOrderChange("desc")}
              className={cn(
                "focus-ring flex-1 rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                order === "desc"
                  ? "bg-primary text-primary-foreground shadow-raised"
                  : "bg-secondary text-muted-foreground hover:text-foreground",
              )}
              aria-pressed={order === "desc"}
              aria-label="Sort high to low"
            >
              High to Low
            </button>
            <button
              type="button"
              onClick={() => onOrderChange("asc")}
              className={cn(
                "focus-ring flex-1 rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                order === "asc"
                  ? "bg-primary text-primary-foreground shadow-raised"
                  : "bg-secondary text-muted-foreground hover:text-foreground",
              )}
              aria-pressed={order === "asc"}
              aria-label="Sort low to high"
            >
              Low to High
            </button>
          </div>
        </fieldset>
      </div>

      {/* Minimum Size */}
      <div className="mb-5">
        <label
          htmlFor="min-size-input"
          className="mb-2 block text-sm font-medium text-muted-foreground"
        >
          Minimum Ideas
        </label>
        <input
          id="min-size-input"
          type="number"
          value={minSize || ""}
          onChange={(e) =>
            onMinSizeChange(
              e.target.value ? Number.parseInt(e.target.value) : undefined,
            )
          }
          placeholder="Any size"
          min="1"
          className="field-control"
          aria-label="Minimum number of ideas in cluster"
        />
      </div>

      {/* Reset Button */}
      <button
        type="button"
        onClick={() => {
          onSortChange("size");
          onOrderChange("desc");
          onMinSizeChange(undefined);
        }}
        className="focus-ring w-full rounded-xl border border-border bg-secondary px-4 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:text-foreground"
        aria-label="Reset all filters to default values"
      >
        Reset Filters
      </button>
    </div>
  );
};
