import { useEffect, useCallback } from 'react';

type KeyHandler = () => void;
type KeyMap = Record<string, KeyHandler>;

export function useKeyboard(keyMap: KeyMap) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't trigger if user is typing in an input/textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      const handler = keyMap[event.key];
      if (handler) {
        event.preventDefault();
        handler();
      }
    },
    [keyMap]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
}

// Common key combinations hook
export function useKeyboardShortcuts(shortcuts: {
  onSave?: () => void;
  onEscape?: () => void;
  onDelete?: () => void;
}) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;

      // Cmd/Ctrl + S for save
      if ((event.metaKey || event.ctrlKey) && event.key === 's') {
        event.preventDefault();
        shortcuts.onSave?.();
        return;
      }

      // Don't trigger other shortcuts if user is typing
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Escape
      if (event.key === 'Escape') {
        event.preventDefault();
        shortcuts.onEscape?.();
        return;
      }

      // Delete or Backspace
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault();
        shortcuts.onDelete?.();
        return;
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
}
