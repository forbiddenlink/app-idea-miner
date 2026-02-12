import { Link, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  CubeIcon,
  LightBulbIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import { SearchAutocomplete } from './SearchAutocomplete'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Clusters', href: '/clusters', icon: CubeIcon },
  { name: 'Ideas', href: '/ideas', icon: LightBulbIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
]

export default function Navbar() {
  const location = useLocation()

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-800/70 border-b border-slate-700/50" role="navigation" aria-label="Main navigation">
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

          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1.5">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
              <span className="text-xs text-slate-400">Live</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
