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
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm"
      onClick={onClose}
      onKeyDown={(e) => e.key === 'Escape' && onClose()}
      tabIndex={-1}
      role="dialog"
      aria-labelledby="shortcuts-title"
      aria-modal="true"
    >
      <div
        className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl border border-slate-700"
        onClick={(e) => e.stopPropagation()}
        role="button"
        tabIndex={0}
        onKeyDown={() => { }}
      >
        <h2 id="shortcuts-title" className="text-xl font-bold text-white mb-4">
          Keyboard Shortcuts
        </h2>
        <div className="space-y-3">
          {shortcuts.map((shortcut) => (
            <div key={shortcut.key} className="flex items-center justify-between">
              <span className="text-slate-300">{shortcut.description}</span>
              <kbd className="px-2 py-1 bg-slate-700 text-slate-200 rounded text-sm font-mono border border-slate-600">
                {shortcut.key}
              </kbd>
            </div>
          ))}
        </div>
        <button
          onClick={onClose}
          className="mt-6 w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-md
                     transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          Close
        </button>
      </div>
    </div>
  );
};
