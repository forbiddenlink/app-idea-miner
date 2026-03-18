import { Sparkles } from 'lucide-react'

export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="border-t border-border/70 bg-surface-sunken/80 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
            <div className="grid h-8 w-8 place-items-center rounded-xl border border-primary/20 bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <p className="font-display text-sm font-semibold text-foreground">App-Idea Miner</p>
              <p className="text-xs text-muted-foreground">Signal intelligence for product opportunities</p>
            </div>
          </div>

          <p className="text-xs font-medium text-muted-foreground">
            &copy; {year} App-Idea Miner. Built with FastAPI, React, and HDBSCAN.
          </p>
        </div>
      </div>
    </footer>
  )
}
