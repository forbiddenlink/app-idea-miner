import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Home,
  Box,
  Lightbulb,
  Bookmark,
  BarChart3,
  Sparkles,
  Settings as SettingsIcon,
  Command,
  HelpCircle,
  Menu,
  X,
} from 'lucide-react'

import { SearchAutocomplete } from './SearchAutocomplete'
import { SimpleTooltip } from './EnhancedTooltip'
import { ModeToggle } from './mode-toggle'
import { cn } from '@/utils/cn'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Clusters', href: '/clusters', icon: Box },
  { name: 'Ideas', href: '/ideas', icon: Lightbulb },
  { name: 'Saved', href: '/saved', icon: Bookmark },
  { name: 'Opportunities', href: '/opportunities', icon: Sparkles },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: SettingsIcon },
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
    globalThis.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = originalOverflow
      globalThis.removeEventListener('keydown', closeOnEscape)
    }
  }, [mobileMenuOpen])

  return (
    <nav
      id="navigation"
      className="sticky top-0 z-50 border-b border-border/80 bg-background/90 backdrop-blur-xl"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-3 px-4 sm:px-6">
        <Link to="/" className="group flex items-center gap-2.5" aria-label="App-Idea Miner home">
          <div className="grid h-9 w-9 place-items-center rounded-xl border border-primary/20 bg-gradient-to-br from-primary/20 via-primary/10 to-transparent text-primary shadow-raised">
            <Lightbulb className="h-4 w-4" aria-hidden="true" />
          </div>
          <div className="leading-none">
            <div className="font-display text-[0.96rem] font-semibold tracking-tight text-foreground">App-Idea Miner</div>
            <div className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Product Discovery
            </div>
          </div>
        </Link>

        <div className="hidden min-w-[16rem] flex-1 lg:block">
          <SearchAutocomplete />
        </div>

        <ul className="hidden items-center gap-1 md:flex">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href
            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={cn(
                    'focus-ring flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-[0.82rem] font-semibold transition-all',
                    isActive
                      ? 'bg-card text-foreground shadow-raised'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  )}
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>{item.name}</span>
                </Link>
              </li>
            )
          })}
        </ul>

        <div className="ml-auto flex items-center gap-2">
          <ModeToggle />

          <SimpleTooltip content="Quick search (Cmd+K / Ctrl+K)">
            <button
              type="button"
              onClick={() => globalThis.dispatchEvent(new Event('app:command-palette-open'))}
              aria-label="Open command palette"
              className="focus-ring hidden items-center gap-1.5 rounded-xl border border-border bg-card px-2.5 py-1.5 text-[0.72rem] font-semibold text-muted-foreground shadow-raised transition hover:text-foreground md:inline-flex"
            >
              <Command className="h-3.5 w-3.5" />
              <span>⌘K</span>
            </button>
          </SimpleTooltip>

          <SimpleTooltip content="Keyboard shortcuts (Shift+?)">
            <button
              type="button"
              onClick={() => globalThis.dispatchEvent(new Event('app:keyboard-shortcuts-open'))}
              aria-label="Open keyboard shortcuts help"
              className="focus-ring hidden h-9 w-9 items-center justify-center rounded-xl border border-border bg-card text-muted-foreground shadow-raised transition hover:text-foreground md:inline-flex"
            >
              <HelpCircle className="h-4 w-4" aria-hidden="true" />
            </button>
          </SimpleTooltip>

          <div className="hidden items-center gap-1.5 sm:flex">
            <span className="h-2 w-2 rounded-full bg-success" />
            <span className="text-[0.72rem] font-semibold uppercase tracking-[0.08em] text-muted-foreground">Live</span>
          </div>

          <button
            type="button"
            className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-card text-muted-foreground shadow-raised transition hover:text-foreground md:hidden"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation-menu"
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
          </button>
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
        <div id="mobile-navigation-menu" className="relative z-50 border-t border-border/70 bg-background/95 px-4 pb-4 pt-3 md:hidden">
          <div className="card space-y-2 p-3">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'focus-ring flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  )}
                  aria-current={isActive ? 'page' : undefined}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span>{item.name}</span>
                </Link>
              )
            })}

            <div className="pt-1">
              <SearchAutocomplete />
            </div>

            <button
              type="button"
              className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-sm font-semibold text-muted-foreground shadow-raised transition hover:text-foreground"
              onClick={() => {
                globalThis.dispatchEvent(new Event('app:command-palette-open'))
                setMobileMenuOpen(false)
              }}
            >
              <Command className="h-4 w-4" aria-hidden="true" />
              Open Command Palette
            </button>
          </div>
        </div>
      )}
    </nav>
  )
}
