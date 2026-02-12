// Enhanced Tooltip Component
// Rich hover cards with detailed information

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface TooltipMetric {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
}

interface EnhancedTooltipProps {
  children: React.ReactNode;
  title: string;
  description?: string;
  metrics?: TooltipMetric[];
  delay?: number;
  disabled?: boolean;
}

export const EnhancedTooltip = ({
  children,
  title,
  description,
  metrics = [],
  delay = 200,
  disabled = false,
}: EnhancedTooltipProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const timeoutRef = useRef<NodeJS.Timeout>();
  const triggerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleMouseEnter = () => {
    if (disabled) return;

    timeoutRef.current = setTimeout(() => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (rect) {
        // Position tooltip above the element, centered
        const tooltipWidth = 320;
        let x = rect.left + rect.width / 2 - tooltipWidth / 2;
        let y = rect.top - 10; // 10px above trigger

        // Keep tooltip within viewport
        if (x < 10) x = 10;
        if (x + tooltipWidth > window.innerWidth - 10) {
          x = window.innerWidth - tooltipWidth - 10;
        }
        if (y < 10) {
          y = rect.bottom + 10; // Show below if not enough space above
        }

        setPosition({ x, y });
        setIsVisible(true);
      }
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="inline-block"
      >
        {children}
      </div>

      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            transition={{ duration: 0.15 }}
            className="fixed z-50 pointer-events-none"
            style={{
              left: `${position.x}px`,
              top: `${position.y}px`,
            }}
          >
            <div className="card p-4 min-w-[320px] max-w-[400px] shadow-2xl">
              {/* Title */}
              <h4 className="font-semibold text-white mb-2">{title}</h4>

              {/* Description */}
              {description && (
                <p className="text-sm text-slate-400 mb-3 leading-relaxed">{description}</p>
              )}

              {/* Metrics */}
              {metrics.length > 0 && (
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-700/50">
                  {metrics.map((metric, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        {metric.icon && (
                          <span className={metric.color || 'text-slate-400'}>
                            {metric.icon}
                          </span>
                        )}
                        <span className="text-xs text-slate-500">{metric.label}</span>
                      </div>
                      <p className="font-semibold text-white">{metric.value}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Arrow pointing down */}
              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-800 border-b border-r border-slate-700/50 rotate-45" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

// Simple text-only tooltip variant
interface SimpleTooltipProps {
  children: React.ReactNode;
  content: string;
  delay?: number;
}

export const SimpleTooltip = ({ children, content, delay = 200 }: SimpleTooltipProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="relative inline-block">
      <div onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave}>
        {children}
      </div>

      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            transition={{ duration: 0.15 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 text-sm text-white bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-lg shadow-xl whitespace-nowrap pointer-events-none z-50"
          >
            {content}
            <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-900/95 border-b border-r border-slate-700/50 rotate-45" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
