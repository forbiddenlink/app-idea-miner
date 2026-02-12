import { useEffect } from 'react'

interface SkipLink {
  id: string
  label: string
}

/**
 * SkipNavigation Component
 *
 * Provides skip links for keyboard and screen reader users to jump to main content.
 * Implements WCAG 2.2 Level AA requirement for bypass blocks.
 *
 * Skip links appear on focus and allow users to:
 * - Skip to main content
 * - Skip to navigation
 * - Skip to search
 */
export function SkipNavigation() {
  const skipLinks: SkipLink[] = [
    { id: 'main-content', label: 'Skip to main content' },
    { id: 'navigation', label: 'Skip to navigation' },
    { id: 'search', label: 'Skip to search' },
  ]

  useEffect(() => {
    // Add IDs to target elements if they don't exist
    const main = document.querySelector('main')
    if (main && !main.id) {
      main.id = 'main-content'
    }

    const nav = document.querySelector('nav')
    if (nav && !nav.id) {
      nav.id = 'navigation'
    }
  }, [])

  const handleSkipClick = (e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault()
    const target = document.getElementById(targetId)
    if (target) {
      target.focus()
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <div
      className="sr-only focus-within:not-sr-only focus-within:absolute focus-within:top-4 focus-within:left-4 focus-within:z-50"
      role="navigation"
      aria-label="Skip navigation"
    >
      <div className="flex flex-col gap-2 bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-xl">
        {skipLinks.map((link) => (
          <a
            key={link.id}
            href={`#${link.id}`}
            onClick={(e) => handleSkipClick(e, link.id)}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            {link.label}
          </a>
        ))}
      </div>
    </div>
  )
}
