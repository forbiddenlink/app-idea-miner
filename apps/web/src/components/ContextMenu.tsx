import { useEffect, useRef, useState } from 'react'
import {
  ClipboardCopy,
  Link,
  Share2,
  Heart,
  Copy,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'

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

export function ContextMenu({ items, children, disabled = false }: Readonly<ContextMenuProps>) {
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const openAtPosition = (x: number, y: number) => {
    const menuWidth = 240
    const menuHeight = items.length * 40 + 16

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

  const handleContextMenu = (e: React.MouseEvent) => {
    if (disabled) return
    e.preventDefault()
    e.stopPropagation()
    openAtPosition(e.clientX, e.clientY)
  }

  const handleClose = () => {
    setIsOpen(false)
    setPosition(null)
  }

  const handleItemClick = (onClick: () => void) => {
    onClick()
    handleClose()
  }

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
            className="min-w-[240px] overflow-hidden rounded-lg border border-border bg-popover shadow-lg"
          >
            <div className="py-2">
              {items.map((item) => {
                const Icon = item.icon

                return (
                  <button
                    type="button"
                    key={item.label}
                    onClick={() => handleItemClick(item.onClick)}
                    disabled={item.disabled}
                    className={cn(
                      "flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition-[padding,background-color,color] duration-150",
                      item.disabled && "cursor-not-allowed opacity-50",
                      !item.disabled && item.danger && "text-destructive hover:bg-destructive/10",
                      !item.disabled && !item.danger && "text-foreground hover:bg-muted",
                      !item.disabled && "hover:pl-5"
                    )}
                  >
                    {Icon && <Icon className="h-4 w-4 flex-shrink-0" />}
                    <span className="flex-1">{item.label}</span>
                    {item.shortcut && (
                      <span className="text-xs text-muted-foreground">{item.shortcut}</span>
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
function useContextMenuActions() {
  const toCsvCell = (value: unknown): string => {
    const text = value == null ? '' : String(value)
    return `"${text.replaceAll('"', '""')}"`
  }

  const copyToClipboard = async (text: string, label: string = 'Text') => {
    try {
      await navigator.clipboard.writeText(text)
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
      await copyToClipboard(url, 'URL')
    }
  }

  const exportAsJson = (data: unknown, filename: string) => {
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportAsCsv = (headers: string[], rows: (string | number | boolean | null)[][], filename: string) => {
    const csv = [
      headers.map(toCsvCell).join(','),
      ...rows.map(row => row.map(toCsvCell).join(','))
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
export function useClusterContextMenu(
  cluster: { id: string; label: string },
  onFavorite?: () => void,
  isFavorited?: boolean
): ContextMenuItem[] {
  const { copyToClipboard, shareUrl } = useContextMenuActions()
  const url = `${globalThis.location.origin}/clusters/${cluster.id}`

  return [
    {
      label: 'Copy Cluster Name',
      icon: ClipboardCopy,
      onClick: () => void copyToClipboard(cluster.label, 'Cluster name'),
    },
    {
      label: 'Copy URL',
      icon: Link,
      onClick: () => void copyToClipboard(url, 'URL'),
      shortcut: '⌘C',
    },
    {
      label: 'Share',
      icon: Share2,
      onClick: () => void shareUrl(url, cluster.label),
    },
    ...(onFavorite
      ? [
        {
          label: isFavorited ? 'Remove from Favorites' : 'Add to Favorites',
          icon: Heart,
          onClick: onFavorite,
        },
      ]
      : []),
    {
      label: 'Open in New Tab',
      icon: Copy,
      onClick: () => window.open(url, '_blank', 'noopener,noreferrer'),
      shortcut: '⌘⏎',
    },
  ]
}

export function useIdeaContextMenu(
  idea: { id: string; problem_statement: string; source?: { url?: string } },
  onFavorite?: () => void,
  isFavorited?: boolean
): ContextMenuItem[] {
  const { copyToClipboard, shareUrl } = useContextMenuActions()
  const url = `${globalThis.location.origin}/ideas/${idea.id}`
  const sourceUrl = idea.source?.url

  return [
    {
      label: 'Copy Problem Statement',
      icon: ClipboardCopy,
      onClick: () => void copyToClipboard(idea.problem_statement, 'Problem statement'),
    },
    {
      label: 'Copy URL',
      icon: Link,
      onClick: () => void copyToClipboard(url, 'URL'),
    },
    ...(sourceUrl
      ? [
        {
          label: 'View Original Source',
          icon: Link,
          onClick: () => window.open(sourceUrl, '_blank', 'noopener,noreferrer'),
        },
      ]
      : []),
    {
      label: 'Share',
      icon: Share2,
      onClick: () => void shareUrl(url, idea.problem_statement),
    },
    ...(onFavorite
      ? [
        {
          label: isFavorited ? 'Remove from Favorites' : 'Add to Favorites',
          icon: Heart,
          onClick: onFavorite,
        },
      ]
      : []),
  ]
}

// Backward-compatible aliases used by card components
export const createClusterContextMenu = useClusterContextMenu
export const createIdeaContextMenu = useIdeaContextMenu
