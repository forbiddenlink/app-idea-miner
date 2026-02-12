import { Component, ErrorInfo, ReactNode } from 'react'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    console.error('Error caught by boundary:', error, errorInfo)

    // Update state with error info
    this.setState({
      error,
      errorInfo,
    })

    // Emit a structured browser event so monitoring can be attached without coupling this component.
    window.dispatchEvent(
      new CustomEvent('app:error', {
        detail: {
          message: error.message,
          stack: error.stack,
          componentStack: errorInfo.componentStack,
        },
      })
    )
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
    // Optionally reload the page
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
          <div className="max-w-md w-full bg-slate-800 rounded-lg shadow-xl p-8">
            <div className="flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mx-auto mb-6">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
            </div>

            <h1 className="text-2xl font-bold text-white text-center mb-2">
              Something went wrong
            </h1>

            <p className="text-slate-400 text-center mb-6">
              We encountered an unexpected error. Our team has been notified.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <div className="mb-6 p-4 bg-slate-900 rounded border border-slate-700 overflow-auto">
                <p className="text-xs font-mono text-red-400 mb-2">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <pre className="text-xs text-slate-500 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={this.handleReset}
                className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-colors"
              >
                Reload Page
              </button>
              <button
                type="button"
                onClick={() => window.history.back()}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
