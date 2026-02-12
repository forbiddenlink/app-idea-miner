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
    <nav id="navigation" className="sticky top-0 z-50 backdrop-blur-xl bg-slate-800/70 border-b border-slate-700/50" role="navigation" aria-label="Main navigation">
      <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary-500/50 to-transparent" />
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between gap-4 h-16">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center space-x-2 flex-shrink-0"
            aria-label="App-Idea Miner home"
          >
            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center" aria-hidden="true">
              <LightBulbIcon className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">
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
                    relative flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 overflow-hidden group
                    ${isActive
                      ? 'bg-gradient-to-r from-primary-500/20 to-purple-500/20 text-white shadow-lg shadow-primary-500/20'
                      : 'text-slate-300 hover:text-white'
                    }
                  `}
                >
                  {/* Gradient hover overlay for inactive links */}
                  {!isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  )}
                  <Icon className="w-5 h-5 relative z-10" aria-hidden="true" />
                  <span className="relative z-10">{item.name}</span>
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
                className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-700/50 hover:bg-slate-600/50 border border-slate-600/50 transition-all duration-200 text-slate-300 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
              >
                <CommandLineIcon className="w-4 h-4" />
                <span className="text-xs font-medium">⌘K / Ctrl+K</span>
              </button>
            </SimpleTooltip>

            <button
              type="button"
              className="md:hidden inline-flex h-11 w-11 items-center justify-center rounded-lg border border-slate-600/50 bg-slate-700/50 text-slate-200 transition-colors hover:bg-slate-600/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
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
            <div className="flex items-center space-x-1.5">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
              <span className="text-xs text-slate-400">Live</span>
            </div>
          </div>
        </div>

        {mobileMenuOpen && (
          <button
            type="button"
            className="fixed inset-0 top-16 z-40 bg-slate-950/50 md:hidden"
            aria-label="Close mobile menu"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {mobileMenuOpen && (
          <div
            id="mobile-navigation-menu"
            className="relative z-50 md:hidden border-t border-slate-700/60 pb-4 pt-3"
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
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-500/20 text-white'
                        : 'text-slate-300 hover:bg-slate-700/50 hover:text-white'
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

            <div className="mt-3 rounded-lg bg-slate-700/20 p-2">
              <SearchAutocomplete />
            </div>

            <button
              type="button"
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-slate-600/50 bg-slate-700/40 px-3 py-2 text-sm text-slate-200 transition-colors hover:bg-slate-600/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
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
