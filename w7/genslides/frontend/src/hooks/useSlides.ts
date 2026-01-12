import { useEffect, useState } from 'react';
import { useSlideStore } from '@/stores';

/**
 * Hook to load and manage slides for a project
 */
export function useSlides(slug: string | null) {
  const {
    slides,
    selectedSlideId,
    isLoading,
    error,
    loadProject,
    selectSlide,
    clearError,
  } = useSlideStore();

  // Load project when slug changes
  useEffect(() => {
    if (slug) {
      loadProject(slug);
    }
  }, [slug, loadProject]);

  // Get selected slide
  const selectedSlide = slides.find((s) => s.sid === selectedSlideId);

  return {
    slides,
    selectedSlide,
    selectedSlideId,
    isLoading,
    error,
    selectSlide,
    clearError,
  };
}

/**
 * Hook to manage debounced content updates
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
