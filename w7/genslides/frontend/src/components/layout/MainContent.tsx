import { useSlideStore } from '@/stores';
import { ImagePreview } from '@/components/preview/ImagePreview';

export function MainContent() {
  const { slides, selectedSlideId } = useSlideStore();

  const selectedSlide = slides.find((s) => s.sid === selectedSlideId);

  if (!selectedSlide) {
    return (
      <main
        className="flex-1 flex items-center justify-center"
        style={{ backgroundColor: 'var(--md-cream)' }}
      >
        <div className="text-center" style={{ color: 'var(--md-slate)' }}>
          <svg
            className="w-16 h-16 mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <p
            className="font-medium"
            style={{ fontSize: 'var(--font-body)', color: 'var(--md-ink)' }}
          >
            No slide selected
          </p>
          <p style={{ fontSize: 'var(--font-small)', marginTop: 'var(--space-1)' }}>
            Select a slide from the sidebar or create a new one
          </p>
        </div>
      </main>
    );
  }

  return (
    <main
      className="flex-1 flex flex-col overflow-hidden"
      style={{ backgroundColor: 'var(--md-cream)' }}
    >
      <ImagePreview slide={selectedSlide} />
    </main>
  );
}
