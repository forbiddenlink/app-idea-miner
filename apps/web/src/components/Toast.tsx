// Toast Notification System
// Modern feedback for user actions (success, error, info, warning)

import { useEffect, useState } from 'react';
import { X, CheckCircle, AlertTriangle, Info } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastProps {
  toast: Toast;
  onClose: (id: string) => void;
}

const toastStyles = {
  success: 'bg-success/10 text-success border-success/25',
  error: 'bg-destructive/10 text-destructive border-destructive/25',
  info: 'bg-primary/10 text-primary border-primary/25',
  warning: 'bg-warning/10 text-warning border-warning/25',
};

const ToastIcon = ({ type }: { type: ToastType }) => {
  const className = "h-5 w-5 flex-shrink-0";

  switch (type) {
    case 'success':
      return <CheckCircle className={className} />;
    case 'error':
      return <AlertTriangle className={className} />;
    case 'warning':
      return <AlertTriangle className={className} />;
    default:
      return <Info className={className} />;
  }
};

export const ToastItem = ({ toast, onClose }: ToastProps) => {
  const [isExiting, setIsExiting] = useState(false);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const duration = toast.duration || 5000;
    const startTime = Date.now();

    // Update progress bar
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
    }, 50);

    const timer = setTimeout(() => {
      setIsExiting(true);
      setTimeout(() => onClose(toast.id), 300); // Wait for exit animation
    }, duration);

    return () => {
      clearTimeout(timer);
      clearInterval(progressInterval);
    };
  }, [toast.id, toast.duration, onClose]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => onClose(toast.id), 300);
  };

  const progressColor = {
    success: 'bg-success',
    error: 'bg-destructive',
    info: 'bg-primary',
    warning: 'bg-warning',
  }[toast.type];

  return (
    <div
      role="alert"
      aria-live="polite"
      aria-atomic="true"
      className={`
        relative flex max-w-md items-center gap-3 overflow-hidden rounded-2xl border p-4 backdrop-blur-sm
        ${toastStyles[toast.type]}
        border-border/70 shadow-overlay transition-transform transition-opacity duration-300 transform
        ${isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'}
      `}
    >
      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/5">
        <div
          className={`h-full transition-[width] duration-50 ${progressColor}`}
          style={{ width: `${progress}%` }}
        />
      </div>

      <ToastIcon type={toast.type} />
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        type="button"
        onClick={handleClose}
        className="focus-ring rounded p-1 transition-colors hover:bg-white/10"
        aria-label="Close notification"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
};

export const ToastContainer = ({ toasts, onClose }: { toasts: Toast[]; onClose: (id: string) => void }) => {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 sm:bottom-6 sm:right-6">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={onClose} />
      ))}
    </div>
  );
};

// Toast hook for easy usage
export const useToast = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (type: ToastType, message: string, duration?: number) => {
    const id = Math.random().toString(36).substring(2, 11);
    const newToast: Toast = { id, type, message, duration };
    setToasts((prev) => [...prev, newToast]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return {
    toasts,
    addToast,
    removeToast,
    success: (message: string, duration?: number) => addToast('success', message, duration),
    error: (message: string, duration?: number) => addToast('error', message, duration),
    info: (message: string, duration?: number) => addToast('info', message, duration),
    warning: (message: string, duration?: number) => addToast('warning', message, duration),
  };
};
