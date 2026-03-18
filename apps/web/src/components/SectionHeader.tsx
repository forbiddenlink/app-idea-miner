import type { LucideIcon } from 'lucide-react'

interface SectionHeaderProps {
  /** Section title (H2) */
  title: string
  /** Optional subtitle / description */
  description?: string
  /** Optional leading icon */
  icon?: LucideIcon
  /** Optional right-aligned action slot */
  action?: React.ReactNode
}

/**
 * Consistent section header used across all pages.
 * Follows the design rule pack: H2 = text-xl font-semibold tracking-tight.
 */
export function SectionHeader({ title, description, icon: Icon, action }: Readonly<SectionHeaderProps>) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        {Icon && (
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="h-4 w-4" />
          </div>
        )}
        <div className="min-w-0">
          <h2 className="text-xl font-semibold tracking-tight text-foreground truncate">
            {title}
          </h2>
          {description && (
            <p className="mt-0.5 text-sm text-muted-foreground line-clamp-1">
              {description}
            </p>
          )}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
