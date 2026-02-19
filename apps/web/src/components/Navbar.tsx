import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  CubeIcon,
  LightBulbIcon,
  ChartBarIcon,
  CommandLineIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { SearchAutocomplete } from './SearchAutocomplete'
import { SimpleTooltip } from './EnhancedTooltip'
import { ModeToggle } from './mode-toggle'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Clusters', href: '/clusters', icon: CubeIcon },
  { name: 'Ideas', href: '/ideas', icon: LightBulbIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
]

export default function Navbar() {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!mobileMenuOpen) return

    const originalOverflow = document.body.style.overflow
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileMenuOpen(false)
      }
    }

    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = originalOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [mobileMenuOpen])

  return (
    <nav id="navigation" className="sticky top-0 z-50 backdrop-blur-xl bg-background/80 border-b border-border" role="navigation" aria-label="Main navigation">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between gap-4 h-16">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-2 flex-shrink-0"
            aria-label="App-Idea Miner home"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary" aria-hidden="true">
              <LightBulbIcon className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold text-foreground">
              App-Idea Miner
            </span>
          </Link>

          {/* Search Bar */}
          <div className="flex-1 max-w-2xl hidden lg:block" id="search" role="search">
            <SearchAutocomplete />
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center space-x-1" role="list">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  aria-label={`Navigate to ${item.name} page`}
                  className={`
                    flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors
                    ${isActive
                      ? 'bg-muted text-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>

          {/* Status & Command Palette Indicator */}
          <div className="flex items-center space-x-2 md:space-x-4">
            <ModeToggle />

            {/* Command Palette Shortcut */}
            <SimpleTooltip content="Quick search (Cmd+K / Ctrl+K)">
              <button
                type="button"
                onClick={() => {
                  window.dispatchEvent(new Event('app:command-palette-open'))
                }}
                aria-label="Open command palette"
                title="Open command palette (Cmd+K / Ctrl+K)"
                className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-muted text-muted-foreground text-xs font-medium transition-colors hover:bg-muted/80 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                <CommandLineIcon className="h-3.5 w-3.5" />
                <span>⌘K</span>
              </button>
            </SimpleTooltip>

            <button
              type="button"
              className="md:hidden inline-flex h-9 w-9 items-center justify-center rounded-md bg-muted text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-navigation-menu"
              onClick={() => setMobileMenuOpen((open) => !open)}
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
              ) : (
                <Bars3Icon className="h-5 w-5" aria-hidden="true" />
              )}
            </button>

            {/* Status */}
            <div className="hidden sm:flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-xs text-muted-foreground">Live</span>
            </div>
          </div>
        </div>

        {mobileMenuOpen && (
          <button
            type="button"
            className="fixed inset-0 top-16 z-40 bg-background/80 backdrop-blur-sm md:hidden"
            aria-label="Close mobile menu"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {mobileMenuOpen && (
          <div
            id="mobile-navigation-menu"
            className="relative z-50 md:hidden border-t border-border pb-4 pt-3"
            aria-label="Mobile navigation"
          >
            <div className="space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-muted text-foreground'
                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                    }`}
                    aria-current={isActive ? 'page' : undefined}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Icon className="h-5 w-5" aria-hidden="true" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </div>

            <div className="mt-3 rounded-md bg-muted p-2">
              <SearchAutocomplete />
            </div>

            <button
              type="button"
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md bg-muted px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/80 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              onClick={() => {
                window.dispatchEvent(new Event('app:command-palette-open'))
                setMobileMenuOpen(false)
              }}
            >
              <CommandLineIcon className="h-4 w-4" aria-hidden="true" />
              Open Command Palette
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
