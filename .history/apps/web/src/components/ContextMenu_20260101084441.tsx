import { useEffect, useRef, useState } from 'react'
import {
  ClipboardDocumentIcon,
  LinkIcon,
  ShareIcon,
  HeartIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'

export interface ContextMenuItem {
  label: string
  icon?: React.ComponentType<{ className?: string }>
  onClick: () => void
  danger?: boolean
  disabled?: boolean
  shortcut?: string
}

interface ContextMenuProps {
  items: ContextMenuItem[]
  children: React.ReactNode
  disabled?: boolean
}

export function ContextMenu({ items, children, disabled = false }: ContextMenuProps) {
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const handleContextMenu = (e: React.MouseEvent) => {
    if (disabled) return

    e.preventDefault()
    e.stopPropagation()

    // Calculate position
    const x = e.clientX
    const y = e.clientY

    // Adjust position to keep menu in viewport
    const menuWidth = 240 // Approximate menu width
    const menuHeight = items.length * 40 + 16 // Approximate menu height

    let adjustedX = x
    let adjustedY = y

    if (x + menuWidth > window.innerWidth) {
      adjustedX = window.innerWidth - menuWidth - 10
    }

    if (y + menuHeight > window.innerHeight) {
      adjustedY = window.innerHeight - menuHeight - 10
    }

    setPosition({ x: adjustedX, y: adjustedY })
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
    setPosition(null)
  }

  const handleItemClick = (onClick: () => void) => {
    onClick()
    handleClose()
  }

  // Close on click outside
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        handleClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen])

  return (
    <div onContextMenu={handleContextMenu} className="relative">
      {children}

      {isOpen && position && (
        <div
          ref={menuRef}
          className="fixed z-50"
          style={{
            left: `${position.x}px`,
            top: `${position.y}px`,
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.1 }}
            className="bg-slate-800/95 backdrop-blur-xl border border-slate-700/50 rounded-xl shadow-2xl overflow-hidden min-w-[240px]"
          >
            <div className="py-2">
              {items.map((item, index) => {
                const Icon = item.icon

                return (
                  <button
                    key={index}
                    onClick={() => handleItemClick(item.onClick)}
                    disabled={item.disabled}
                    className={`
                      w-full px-4 py-2.5 flex items-center gap-3 text-left text-sm
                      transition-all duration-150
                      ${
                        item.disabled
                          ? 'opacity-50 cursor-not-allowed'
                          : item.danger
                          ? 'text-red-400 hover:bg-red-500/10'
                          : 'text-slate-300 hover:bg-slate-700/50'
                      }
                      ${!item.disabled && 'hover:pl-5'}
                    `}
                  >
                    {Icon && <Icon className="w-4 h-4 flex-shrink-0" />}
                    <span className="flex-1">{item.label}</span>
                    {item.shortcut && (
                      <span className="text-xs text-slate-500">{item.shortcut}</span>
                    )}
                  </button>
                )
              })}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}

// Helper hook for common context menu actions
export function useContextMenuActions() {
  const copyToClipboard = async (text: string, label: string = 'Text') => {
    try {
      await navigator.clipboard.writeText(text)
      // You can integrate with toast notifications here
      console.log(`${label} copied to clipboard`)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  const shareUrl = async (url: string, title: string) => {
    if (navigator.share) {
      try {
        await navigator.share({ title, url })
      } catch (error) {
        if ((error as Error).name !== 'AbortError') {
          console.error('Share failed:', error)
        }
      }
    } else {
      // Fallback: copy to clipboard
      await copyToClipboard(url, 'URL')
    }
  }

  const exportAsJson = (data: any, filename: string) => {
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportAsCsv = (headers: string[], rows: any[][], filename: string) => {
    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return {
    copyToClipboard,
    shareUrl,
    exportAsJson,
    exportAsCsv,
  }
}

// Pre-built context menu items for common actions
export function createClusterContextMenu(
  cluster: { id: string; label: string },
  onFavorite?: () => void,
  isFavorited?: boolean
): ContextMenuItem[] {
  const { copyToClipboard, shareUrl } = useContextMenuActions()
  const url = `${window.location.origin}/clusters/${cluster.id}`

  return [
    {
      label: 'Copy Cluster Name',
      icon: ClipboardDocumentIcon,
      onClick: () => copyToClipboard(cluster.label, 'Cluster name'),
    },
    {
      label: 'Copy URL',
      icon: LinkIcon,
      onClick: () => copyToClipboard(url, 'URL'),
      shortcut: '⌘C',
    },
    {
      label: 'Share',
      icon: ShareIcon,
      onClick: () => shareUrl(url, cluster.label),
    },
    ...(onFavorite
      ? [
          {
            label: isFavorited ? 'Remove from Favorites' : 'Add to Favorites',
            icon: HeartIcon,
            onClick: onFavorite,
          },
        ]
      : []),
    {
      label: 'Open in New Tab',
      icon: DocumentDuplicateIcon,
      onClick: () => window.open(url, '_blank'),
      shortcut: '⌘⏎',
    },
  ]
}

export function createIdeaContextMenu(
  idea: { id: string; problem_statement: string; source?: { url?: string } }
): ContextMenuItem[] {
  const { copyToClipboard, shareUrl } = useContextMenuActions()
  const url = `${window.location.origin}/ideas/${idea.id}`
  const sourceUrl = idea.source?.url

  return [
    {
      label: 'Copy Problem Statement',
      icon: ClipboardDocumentIcon,
      onClick: () => copyToClipboard(idea.problem_statement, 'Problem statement'),
    },
    {
      label: 'Copy URL',
      icon: LinkIcon,
      onClick: () => copyToClipboard(url, 'URL'),
    },
    ...(sourceUrl
      ? [
          {
            label: 'View Original Source',
            icon: LinkIcon,
            onClick: () => window.open(sourceUrl, '_blank'),
          },
        ]
      : []),
    {
      label: 'Share',
      icon: ShareIcon,
      onClick: () => shareUrl(url, idea.problem_statement),
    },
  ]
}
