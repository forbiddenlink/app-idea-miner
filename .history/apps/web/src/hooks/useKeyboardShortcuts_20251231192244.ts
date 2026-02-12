import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface ShortcutConfig {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  action: () => void;
  description: string;
}

export const useKeyboardShortcuts = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const shortcuts: ShortcutConfig[] = [
      {
        key: 'h',
        altKey: true,
        action: () => navigate('/'),
        description: 'Go to Dashboard',
      },
      {
        key: 'c',
        altKey: true,
        action: () => navigate('/clusters'),
        description: 'Go to Cluster Explorer',
      },
      {
        key: 'a',
        altKey: true,
        action: () => navigate('/analytics'),
        description: 'Go to Analytics',
      },
      {
        key: '/',
        ctrlKey: true,
        action: () => {
          // Focus search input if available
          const searchInput = document.querySelector<HTMLInputElement>('input[type="search"], input[placeholder*="Search"]');
          if (searchInput) {
            searchInput.focus();
          }
        },
        description: 'Focus Search',
      },
      {
        key: 'k',
        ctrlKey: true,
        action: () => {
          // Open command palette (future feature)
          console.log('Command palette (future feature)');
        },
        description: 'Open Command Palette',
      },
      {
        key: '?',
        shiftKey: true,
        action: () => {
          // Show keyboard shortcuts help (future feature)
          alert(
            'Keyboard Shortcuts:\n\n' +
            'Alt + H - Dashboard\n' +
            'Alt + C - Cluster Explorer\n' +
            'Alt + A - Analytics\n' +
            'Ctrl + / - Focus Search\n' +
            'Esc - Clear Focus'
          );
        },
        description: 'Show Keyboard Shortcuts',
      },
    ];

    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        (e.target instanceof HTMLElement && e.target.isContentEditable)
      ) {
        return;
      }

      const matchingShortcut = shortcuts.find(
        (shortcut) =>
          e.key === shortcut.key &&
          !!e.ctrlKey === !!shortcut.ctrlKey &&
          !!e.shiftKey === !!shortcut.shiftKey &&
          !!e.altKey === !!shortcut.altKey
      );

      if (matchingShortcut) {
        e.preventDefault();
        matchingShortcut.action();
      }

      // ESC to clear focus
      if (e.key === 'Escape') {
        if (document.activeElement instanceof HTMLElement) {
          document.activeElement.blur();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);
};

// Hook to get all shortcuts for help UI
export const useShortcutList = () => {
  return [
    { keys: 'Alt + H', description: 'Go to Dashboard' },
    { keys: 'Alt + C', description: 'Go to Cluster Explorer' },
    { keys: 'Alt + A', description: 'Go to Analytics' },
    { keys: 'Ctrl + /', description: 'Focus Search' },
    { keys: 'Shift + ?', description: 'Show Keyboard Shortcuts' },
    { keys: 'Esc', description: 'Clear Focus' },
  ];
};
