import { useState, useCallback, useEffect } from 'react';
import { useSlideStore, usePlayerStore } from '@/stores';

interface HeaderProps {
  onOpenStylePicker: () => void;
}

export function Header({ onOpenStylePicker }: HeaderProps) {
  const { title, totalCost, slides, style, updateTitle, isSaving } = useSlideStore();
  const { startPlayback } = usePlayerStore();
  const [localTitle, setLocalTitle] = useState(title);
  const [isEditing, setIsEditing] = useState(false);

  // Sync local title with store
  useEffect(() => {
    setLocalTitle(title);
  }, [title]);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
    if (localTitle !== title && localTitle.trim()) {
      updateTitle(localTitle.trim());
    } else {
      setLocalTitle(title);
    }
  }, [localTitle, title, updateTitle]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleBlur();
      } else if (e.key === 'Escape') {
        setLocalTitle(title);
        setIsEditing(false);
      }
    },
    [handleBlur, title]
  );

  const handlePlay = useCallback(() => {
    if (slides.length > 0) {
      startPlayback(slides.length, 0);
    }
  }, [slides.length, startPlayback]);

  return (
    <header className="md-eyebrow shrink-0">
      {/* Logo and Title */}
      <div className="flex items-center gap-4">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <svg
            className="w-8 h-8"
            style={{ color: 'var(--md-ink)' }}
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z" />
            <path d="M7.5 13h2v4h-2zM10.5 9h2v8h-2zM13.5 11h2v6h-2z" />
          </svg>
          <span
            className="text-xl font-bold uppercase tracking-wider"
            style={{ color: 'var(--md-ink)' }}
          >
            GenSlides
          </span>
        </div>

        {/* Divider */}
        <div
          className="h-6 w-px"
          style={{ backgroundColor: 'var(--md-graphite)' }}
        />

        {/* Title Input */}
        {isEditing ? (
          <input
            type="text"
            value={localTitle}
            onChange={(e) => setLocalTitle(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            className="md-input py-1"
            style={{ maxWidth: '300px' }}
            autoFocus
          />
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="px-2 py-1 font-medium rounded transition-colors"
            style={{
              color: 'var(--md-ink)',
              backgroundColor: 'transparent',
            }}
            disabled={isSaving}
          >
            {localTitle || 'Untitled Project'}
          </button>
        )}

        {isSaving && (
          <span
            style={{ fontSize: 'var(--font-tiny)', color: 'var(--md-ink)' }}
          >
            Saving...
          </span>
        )}

        {/* Cost Badge */}
        <span
          className="px-2 py-0.5 rounded font-bold"
          style={{
            fontSize: 'var(--font-tiny)',
            backgroundColor: 'var(--md-watermelon)',
            color: 'white',
          }}
        >
          ${totalCost.toFixed(2)}
        </span>
      </div>

      {/* Right side: Style and Play button */}
      <div className="flex items-center gap-4">
        {/* Style Button */}
        <button
          onClick={onOpenStylePicker}
          className="md-btn-secondary"
          style={{ padding: 'var(--space-2) var(--space-4)' }}
          title={style ? `Style: ${style.prompt}` : 'Set style'}
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
            />
          </svg>
          {style ? 'Style' : 'Set Style'}
        </button>

        {/* Play Button */}
        <button
          onClick={handlePlay}
          disabled={slides.length === 0}
          className="md-btn disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ padding: 'var(--space-2) var(--space-4)' }}
        >
          <svg
            className="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M8 5v14l11-7z" />
          </svg>
          Play
        </button>
      </div>
    </header>
  );
}
