import { useEffect } from 'react';

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
