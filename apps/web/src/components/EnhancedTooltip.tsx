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
        const tooltipWidth = 320;
        let x = rect.left + rect.width / 2 - tooltipWidth / 2;
        let y = rect.top - 10;

        if (x < 10) x = 10;
        if (x + tooltipWidth > window.innerWidth - 10) {
          x = window.innerWidth - tooltipWidth - 10;
        }
        if (y < 10) {
          y = rect.bottom + 10;
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
            className="pointer-events-none fixed z-50"
            style={{
              left: `${position.x}px`,
              top: `${position.y}px`,
            }}
          >
            <div className="min-w-[320px] max-w-[400px] rounded-lg border border-border bg-popover p-4 shadow-lg">
              <h4 className="mb-2 font-semibold text-foreground">{title}</h4>

              {description && (
                <p className="mb-3 text-sm leading-relaxed text-muted-foreground">{description}</p>
              )}

              {metrics.length > 0 && (
                <div className="grid grid-cols-2 gap-3 border-t border-border pt-3">
                  {metrics.map((metric, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        {metric.icon && (
                          <span className={metric.color || 'text-muted-foreground'}>
                            {metric.icon}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">{metric.label}</span>
                      </div>
                      <p className="font-semibold text-foreground">{metric.value}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 border-b border-r border-border bg-popover" />
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
            className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md border border-border bg-popover px-3 py-2 text-sm text-foreground shadow-lg"
          >
            {content}
            <div className="absolute -bottom-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 border-b border-r border-border bg-popover" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
