// Keyboard Navigation Hook
// Modern keyboard shortcuts and accessibility (WCAG 2.2)

import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  action: () => void;
  description: string;
}

export const useKeyboardShortcuts = (shortcuts: KeyboardShortcut[]) => {
  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatches = shortcut.ctrl ? event.ctrlKey || event.metaKey : !event.ctrlKey && !event.metaKey;
        const shiftMatches = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const altMatches = shortcut.alt ? event.altKey : !event.altKey;

        if (keyMatches && ctrlMatches && shiftMatches && altMatches) {
          event.preventDefault();
          shortcut.action();
          break;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);
};

// Global keyboard shortcuts for the app
export const useGlobalShortcuts = () => {
  const navigate = useNavigate();

  useKeyboardShortcuts([
    {
      key: '/',
      description: 'Focus search',
      action: () => {
        const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      },
    },
    {
      key: 'Escape',
      description: 'Clear search / Close modal',
      action: () => {
        const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
        if (searchInput && searchInput.value) {
          searchInput.value = '';
          searchInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
      },
    },
    {
      key: '1',
      ctrl: true,
      description: 'Go to Dashboard',
      action: () => navigate('/'),
    },
    {
      key: '2',
      ctrl: true,
      description: 'Go to Clusters',
      action: () => navigate('/clusters'),
    },
    {
      key: '3',
      ctrl: true,
      description: 'Go to Analytics',
      action: () => navigate('/analytics'),
    },
  ]);
};

// Skip to main content link (WCAG 2.2)
export const SkipLink = () => {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50
                 bg-indigo-600 text-white px-4 py-2 rounded-md
                 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
    >
      Skip to main content
    </a>
  );
};

// Keyboard shortcut help dialog
export const KeyboardShortcutsDialog = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const shortcuts = [
    { key: '/', description: 'Focus search' },
    { key: 'Esc', description: 'Clear search / Close modal' },
    { key: 'Ctrl+1', description: 'Go to Dashboard' },
    { key: 'Ctrl+2', description: 'Go to Clusters' },
    { key: 'Ctrl+3', description: 'Go to Analytics' },
    { key: '?', description: 'Show this help' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/50 backdrop-blur-sm">
      <button
        type="button"
        className="absolute inset-0"
        onClick={onClose}
        aria-label="Close keyboard shortcuts dialog"
      />
      <div
        className="relative bg-card rounded-lg p-6 max-w-md w-full mx-4 shadow-xl border border-border"
        role="dialog"
        aria-labelledby="shortcuts-title"
        aria-modal="true"
      >
        <h2 id="shortcuts-title" className="text-xl font-bold text-foreground mb-4">
          Keyboard Shortcuts
        </h2>
        <div className="space-y-3">
          {shortcuts.map((shortcut) => (
            <div key={shortcut.key} className="flex items-center justify-between">
              <span className="text-muted-foreground">{shortcut.description}</span>
              <kbd className="px-2 py-1 bg-muted text-foreground rounded text-sm font-mono border border-border">
                {shortcut.key}
              </kbd>
            </div>
          ))}
        </div>
        <button
          onClick={onClose}
          className="mt-6 w-full bg-primary hover:bg-primary/90 text-primary-foreground py-2 rounded-md
                     transition-colors focus:outline-none focus:ring-2 focus:ring-ring"
        >
          Close
        </button>
      </div>
    </div>
  );
};
