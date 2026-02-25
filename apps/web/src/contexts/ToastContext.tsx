import { createContext, useContext, useState, useCallback, useMemo, ReactNode } from "react"
import { ToastContainer, ToastType, Toast } from "@/components/Toast"

interface ToastContextValue {
  toasts: Toast[]
  addToast: (type: ToastType, message: string, duration?: number) => void
  removeToast: (id: string) => void
  success: (message: string, duration?: number) => void
  error: (message: string, duration?: number) => void
  info: (message: string, duration?: number) => void
  warning: (message: string, duration?: number) => void
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined)

export function ToastProvider({ children }: Readonly<{ children: ReactNode }>) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((type: ToastType, message: string, duration?: number) => {
    const id = Math.random().toString(36).substring(2, 11)
    setToasts((prev) => [...prev, { id, type, message, duration }])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const success = useCallback(
    (message: string, duration?: number) => addToast("success", message, duration),
    [addToast]
  )
  const error = useCallback(
    (message: string, duration?: number) => addToast("error", message, duration),
    [addToast]
  )
  const info = useCallback(
    (message: string, duration?: number) => addToast("info", message, duration),
    [addToast]
  )
  const warning = useCallback(
    (message: string, duration?: number) => addToast("warning", message, duration),
    [addToast]
  )

  const value = useMemo(
    () => ({ toasts, addToast, removeToast, success, error, info, warning }),
    [toasts, addToast, removeToast, success, error, info, warning]
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  )
}

export function useGlobalToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error("useGlobalToast must be used within a ToastProvider")
  }
  return context
}
