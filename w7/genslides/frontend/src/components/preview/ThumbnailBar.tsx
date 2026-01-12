import { useCallback } from 'react';
import type { ImageInfo } from '@/types';

interface ThumbnailBarProps {
  images: ImageInfo[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  getImageUrl: (filename: string) => string;
  onGenerate?: () => void;
  isGenerating?: boolean;
}

export function ThumbnailBar({
  images,
  selectedIndex,
  onSelect,
  getImageUrl,
  onGenerate,
  isGenerating,
}: ThumbnailBarProps) {
  const handleClick = useCallback(
    (index: number) => {
      onSelect(index);
    },
    [onSelect]
  );

  // Don't render if no images and no generate option
  if (images.length === 0 && !onGenerate) return null;

  return (
    <div
      className="p-2 rounded-lg overflow-y-auto"
      style={{
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(8px)',
        border: '2px solid var(--md-graphite)',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        maxHeight: '100%',
      }}
    >
      <div className="flex flex-col gap-2">
        {/* Generate new image button */}
        {onGenerate && (
          <button
            onClick={onGenerate}
            disabled={isGenerating}
            className="shrink-0 rounded flex items-center justify-center transition-all duration-150 disabled:opacity-50 hover:scale-105"
            style={{
              width: '120px',
              height: '68px',
              border: '2px dashed var(--md-graphite)',
              backgroundColor: 'var(--md-cloud)',
              color: 'var(--md-slate)',
              cursor: isGenerating ? 'not-allowed' : 'pointer',
            }}
            title="Generate image for current text"
            aria-label="Generate image for current text"
          >
            {isGenerating ? (
              <svg
                className="w-6 h-6 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            )}
          </button>
        )}

        {/* Thumbnail images */}
        {images.map((image, index) => (
          <button
            key={image.filename}
            onClick={() => handleClick(index)}
            className="relative shrink-0 rounded overflow-hidden transition-all duration-150"
            style={{
              width: '120px',
              height: '68px',
              border: index === selectedIndex
                ? '3px solid var(--md-sky-strong)'
                : '2px solid var(--md-graphite)',
              opacity: index === selectedIndex ? 1 : 0.7,
            }}
            aria-label={`Select image ${index + 1}`}
            aria-pressed={index === selectedIndex}
          >
            <img
              src={getImageUrl(image.filename)}
              alt={`Thumbnail ${index + 1}`}
              className="w-full h-full object-cover"
            />
            {image.is_current && (
              <div
                className="absolute bottom-0 left-0 right-0 text-center font-bold uppercase"
                style={{
                  backgroundColor: 'var(--md-sky)',
                  color: 'var(--md-ink)',
                  fontSize: '9px',
                  lineHeight: '14px',
                }}
              >
                Current
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
