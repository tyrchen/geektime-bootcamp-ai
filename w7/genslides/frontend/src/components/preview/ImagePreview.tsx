import { useCallback } from 'react';
import type { Slide } from '@/types';
import { useSlideStore } from '@/stores';
import { ThumbnailBar } from './ThumbnailBar';

interface ImagePreviewProps {
  slide: Slide;
}

export function ImagePreview({ slide }: ImagePreviewProps) {
  const {
    slug,
    currentImages,
    selectedImageIndex,
    generatingSlideId,
    generateImage,
    selectImage,
  } = useSlideStore();

  const selectedImage = currentImages[selectedImageIndex];
  const isGenerating = generatingSlideId === slide.sid;

  const handleGenerate = useCallback(() => {
    generateImage(slide.sid);
  }, [slide.sid, generateImage]);

  const getImageUrl = (filename: string) => {
    return `/api/slides/${slug}/${slide.sid}/images/${filename}`;
  };

  // Show generate button if no matching image
  const showGeneratePrompt = !slide.has_matching_image;

  return (
    <div className="h-full relative">
      {/* Main Image Area */}
      <div className="h-full flex items-center justify-center p-6">
        {selectedImage ? (
          <div className="relative" style={{ maxWidth: '100%', maxHeight: '100%' }}>
            <img
              src={getImageUrl(selectedImage.filename)}
              alt={slide.content}
              className="rounded"
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                border: '2px solid var(--md-graphite)',
                boxShadow: '-6px 6px 0px 0px rgba(0, 0, 0, 1)',
              }}
            />
            {!selectedImage.is_current && (
              <div
                className="absolute top-2 left-2 text-xs px-2 py-1 rounded font-bold uppercase"
                style={{
                  backgroundColor: 'var(--md-sunbeam)',
                  color: 'var(--md-ink)',
                  border: '2px solid var(--md-graphite)',
                }}
              >
                Previous version
              </div>
            )}
          </div>
        ) : (
          <div className="text-center" style={{ color: 'var(--md-slate)' }}>
            <svg
              className="w-16 h-16 mx-auto mb-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p
              className="font-bold mb-1"
              style={{ fontSize: 'var(--font-body)', color: 'var(--md-ink)' }}
            >
              No image yet
            </p>
            <p style={{ fontSize: 'var(--font-small)' }}>
              Click + to generate an image
            </p>
          </div>
        )}
      </div>

      {/* Thumbnail Bar - right side, overlapping image by half, vertically centered */}
      <div
        className="absolute top-1/2 -translate-y-1/2 flex items-center"
        style={{ right: '48px' }}
      >
        <ThumbnailBar
          images={currentImages}
          selectedIndex={selectedImageIndex}
          onSelect={selectImage}
          getImageUrl={getImageUrl}
          onGenerate={showGeneratePrompt ? handleGenerate : undefined}
          isGenerating={isGenerating}
        />
      </div>
    </div>
  );
}
