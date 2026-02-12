// Filter Chips Component
// Shows active filters as removable chips

import { XMarkIcon } from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

export interface FilterChip {
  id: string;
  label: string;
  value: string;
  count?: number;
  onRemove: () => void;
}

interface FilterChipsProps {
  chips: FilterChip[];
  onClearAll?: () => void;
}

export const FilterChips = ({ chips, onClearAll }: FilterChipsProps) => {
  if (chips.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-wrap items-center gap-2 mb-4 p-4 rounded-lg backdrop-blur-xl bg-slate-800/40 border border-slate-700/50"
    >
      <span className="text-sm text-slate-400 font-medium">Active Filters:</span>

      <AnimatePresence mode="popLayout">
        {chips.map((chip) => (
          <motion.div
            key={chip.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-sm text-indigo-300 hover:bg-indigo-500/30 transition-colors group"
          >
            <span className="font-medium">{chip.label}:</span>
            <span>{chip.value}</span>
            {chip.count && (
              <span className="text-xs opacity-70">({chip.count})</span>
            )}
            <button
              onClick={chip.onRemove}
              className="ml-1 hover:text-red-400 transition-colors"
              aria-label={`Remove ${chip.label} filter`}
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>

      {onClearAll && chips.length > 1 && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={onClearAll}
          className="ml-auto text-sm text-slate-400 hover:text-red-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-slate-700/50"
        >
          Clear All
        </motion.button>
      )}
    </motion.div>
  );
};

// Utility hook to build filter chips
export const useFilterChips = () => {
  const buildChips = (filters: Record<string, unknown>, handlers: Record<string, () => void>): FilterChip[] => {
    const chips: FilterChip[] = [];

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '' && value !== 'all') {
        const handler = handlers[key];
        if (handler) {
          chips.push({
            id: key,
            label: formatLabel(key),
            value: formatValue(value),
            onRemove: handler,
          });
        }
      }
    });

    return chips;
  };

  const formatLabel = (key: string): string => {
    return key
      .replace(/([A-Z])/g, ' $1')
      .replace(/_/g, ' ')
      .replace(/^./, (str) => str.toUpperCase())
      .trim();
  };

  const formatValue = (value: unknown): string => {
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (typeof value === 'number') return value.toString();
    if (Array.isArray(value)) return value.join(', ');
    return String(value);
  };

  return { buildChips };
};
