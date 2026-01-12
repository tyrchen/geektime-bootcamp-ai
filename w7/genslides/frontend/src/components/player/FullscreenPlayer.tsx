import { useEffect, useRef } from 'react';
import { useSlideStore, usePlayerStore } from '@/stores';
import { useKeyboard } from '@/hooks/useKeyboard';
import { getSlideImageFilename, getSlideImageUrl } from '@/utils/slideImage';

export function FullscreenPlayer() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { slug, slides } = useSlideStore();
  const {
    isFullscreen,
    currentIndex,
    nextSlide,
    prevSlide,
    goToSlide,
    stopPlayback,
    setFullscreen,
  } = usePlayerStore();

  const currentSlide = slides[currentIndex];

  // Keyboard controls
  useKeyboard({
    ArrowRight: nextSlide,
    ArrowLeft: prevSlide,
    Escape: stopPlayback,
  });

  // Handle fullscreen
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleFullscreenChange = () => {
      const isNowFullscreen = document.fullscreenElement === container;
      setFullscreen(isNowFullscreen);
    };

    if (isFullscreen && !document.fullscreenElement) {
      container.requestFullscreen().catch(console.error);
    } else if (!isFullscreen && document.fullscreenElement) {
      document.exitFullscreen().catch(console.error);
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [isFullscreen, setFullscreen]);

  if (!isFullscreen || !currentSlide || !slug) return null;

  const currentImageFilename = getSlideImageFilename(currentSlide);
  const currentImageUrl = currentImageFilename
    ? getSlideImageUrl(slug, currentSlide.sid, currentImageFilename)
    : null;

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 bg-black flex flex-col z-50"
    >
      {/* Main image area */}
      <div className="flex-1 flex items-center justify-center overflow-hidden">
        {currentImageUrl ? (
          <img
            src={currentImageUrl}
            alt={currentSlide.content}
            className="max-h-full max-w-full object-contain"
          />
        ) : (
          <div className="text-center text-white/60">
            <svg
              className="w-24 h-24 mx-auto mb-4"
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
            <p className="text-lg">No image available</p>
            <p className="text-sm mt-2 max-w-md mx-auto">
              {currentSlide.content}
            </p>
          </div>
        )}
      </div>

      {/* Controls overlay */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-4">
        {/* Progress indicators */}
        <div className="flex justify-center gap-2 mb-2">
          {slides.map((slide, index) => (
            <button
              key={slide.sid}
              onClick={() => goToSlide(index)}
              className={`
                w-2 h-2 rounded-full transition-all
                ${
                  index === currentIndex
                    ? 'bg-white scale-125'
                    : 'bg-white/40 hover:bg-white/60'
                }
              `}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>

        {/* Slide info and keyboard hints */}
        <div className="text-center text-white/50 text-xs">
          {currentIndex + 1} / {slides.length} · ← → to navigate · ESC to exit
        </div>
      </div>

      {/* Navigation arrows */}
      <button
        onClick={prevSlide}
        className="absolute left-4 top-1/2 -translate-y-1/2 p-3 text-white/60 hover:text-white transition-colors"
        aria-label="Previous slide"
      >
        <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
      </button>

      <button
        onClick={nextSlide}
        className="absolute right-4 top-1/2 -translate-y-1/2 p-3 text-white/60 hover:text-white transition-colors"
        aria-label="Next slide"
      >
        <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>

      {/* Close button */}
      <button
        onClick={stopPlayback}
        className="absolute top-4 right-4 p-2 text-white/60 hover:text-white transition-colors"
        aria-label="Exit fullscreen"
      >
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}
