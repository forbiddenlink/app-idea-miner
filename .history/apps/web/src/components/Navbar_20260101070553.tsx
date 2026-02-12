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
    <nav className="bg-slate-800 border-b border-slate-700" role="navigation" aria-label="Main navigation">
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
                  className={`
                    flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors
                    ${isActive
                      ? 'bg-slate-700 text-white'
                      : 'text-slate-300 hover:bg-slate-700/50 hover:text-white'
                    }
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
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
