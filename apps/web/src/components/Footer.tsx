import { Sparkles } from 'lucide-react'

export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="border-t border-border/50 bg-surface-sunken">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          {/* Brand */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="font-semibold text-foreground">App-Idea Miner</span>
            <span className="hidden sm:inline">&middot;</span>
            <span className="hidden sm:inline">ML-powered opportunity detection</span>
          </div>

          {/* Meta */}
          <p className="text-xs text-muted-foreground">
            &copy; {year} App-Idea Miner &middot; Built with FastAPI, React &amp; HDBSCAN
          </p>
        </div>
      </div>
    </footer>
  )
}
