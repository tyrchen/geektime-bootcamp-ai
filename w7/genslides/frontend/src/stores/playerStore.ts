import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface PlayerState {
  isPlaying: boolean;
  isFullscreen: boolean;
  currentIndex: number;
  interval: number; // in milliseconds
  totalSlides: number;

  // Actions
  startPlayback: (totalSlides: number, startIndex?: number) => void;
  stopPlayback: () => void;
  nextSlide: () => void;
  prevSlide: () => void;
  goToSlide: (index: number) => void;
  setInterval: (ms: number) => void;
  setFullscreen: (isFullscreen: boolean) => void;
}

export const usePlayerStore = create<PlayerState>()(
  devtools(
    (set, get) => ({
      isPlaying: false,
      isFullscreen: false,
      currentIndex: 0,
      interval: 5000, // 5 seconds default
      totalSlides: 0,

      startPlayback: (totalSlides, startIndex = 0) => {
        set({
          isPlaying: true,
          isFullscreen: true,
          currentIndex: startIndex,
          totalSlides,
        });
      },

      stopPlayback: () => {
        set({
          isPlaying: false,
          isFullscreen: false,
        });
      },

      nextSlide: () => {
        const { currentIndex, totalSlides } = get();
        const nextIndex = (currentIndex + 1) % totalSlides;
        set({ currentIndex: nextIndex });
      },

      prevSlide: () => {
        const { currentIndex, totalSlides } = get();
        const prevIndex = currentIndex === 0 ? totalSlides - 1 : currentIndex - 1;
        set({ currentIndex: prevIndex });
      },

      goToSlide: (index) => {
        const { totalSlides } = get();
        if (index >= 0 && index < totalSlides) {
          set({ currentIndex: index });
        }
      },

      setInterval: (ms) => {
        set({ interval: ms });
      },

      setFullscreen: (isFullscreen) => {
        set({ isFullscreen });
        if (!isFullscreen) {
          set({ isPlaying: false });
        }
      },
    }),
    { name: 'PlayerStore' }
  )
);
