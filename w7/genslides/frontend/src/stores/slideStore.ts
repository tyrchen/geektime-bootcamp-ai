import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { slidesApi } from '@/api/slides';
import { imagesApi } from '@/api/images';
import { styleApi } from '@/api/style';
import type { Slide, Style, ImageInfo, StyleCandidate } from '@/types';

interface SlideState {
  // Project data
  slug: string | null;
  title: string;
  style: Style | null;
  slides: Slide[];
  totalCost: number;

  // Selection
  selectedSlideId: string | null;
  currentImages: ImageInfo[];
  selectedImageIndex: number;

  // Style picker
  styleCandidates: StyleCandidate[];
  stylePrompt: string;

  // Loading states
  isLoading: boolean;
  generatingSlideId: string | null;  // Track which slide is generating
  isGeneratingStyle: boolean;
  isSaving: boolean;
  error: string | null;

  // Actions - Project
  loadProject: (slug: string) => Promise<void>;
  createProject: (slug: string, title: string) => Promise<void>;
  updateTitle: (title: string) => Promise<void>;

  // Actions - Slides
  selectSlide: (sid: string) => void;
  createSlide: (content: string, position?: number) => Promise<void>;
  updateSlide: (sid: string, content: string) => Promise<void>;
  deleteSlide: (sid: string) => Promise<void>;
  reorderSlides: (slideIds: string[]) => Promise<void>;

  // Actions - Images
  loadSlideImages: (sid: string) => Promise<void>;
  generateImage: (sid: string) => Promise<void>;
  selectImage: (index: number) => void;

  // Actions - Style
  generateStyleCandidates: (prompt: string) => Promise<void>;
  selectStyle: (candidateFilename: string) => Promise<void>;
  setStylePrompt: (prompt: string) => void;
  clearStyleCandidates: () => void;

  // Actions - Error
  clearError: () => void;
}

export const useSlideStore = create<SlideState>()(
  devtools(
    (set, get) => ({
      // Initial state
      slug: null,
      title: '',
      style: null,
      slides: [],
      totalCost: 0,
      selectedSlideId: null,
      currentImages: [],
      selectedImageIndex: 0,
      styleCandidates: [],
      stylePrompt: '',
      isLoading: false,
      generatingSlideId: null,
      isGeneratingStyle: false,
      isSaving: false,
      error: null,

      // Project actions
      loadProject: async (slug) => {
        set({ isLoading: true, error: null });
        try {
          const data = await slidesApi.getProject(slug);
          set({
            slug,
            title: data.title,
            style: data.style,
            slides: data.slides,
            totalCost: data.total_cost,
            selectedSlideId: data.slides[0]?.sid ?? null,
            isLoading: false,
          });

          // Load images for the first slide
          if (data.slides[0]) {
            get().loadSlideImages(data.slides[0].sid);
          }
        } catch (e) {
          set({ error: (e as Error).message, isLoading: false });
        }
      },

      createProject: async (slug, title) => {
        set({ isLoading: true, error: null });
        try {
          await slidesApi.createSlide(slug, { title, content: 'Welcome to ' + title });
          set({
            slug,
            title,
            style: null,
            slides: [],
            isLoading: false,
          });
        } catch (e) {
          set({ error: (e as Error).message, isLoading: false });
        }
      },

      updateTitle: async (title) => {
        const { slug } = get();
        if (!slug) return;

        set({ isSaving: true });
        try {
          await slidesApi.updateTitle(slug, title);
          set({ title, isSaving: false });
        } catch (e) {
          set({ error: (e as Error).message, isSaving: false });
        }
      },

      // Slide actions
      selectSlide: (sid) => {
        set({ selectedSlideId: sid, currentImages: [], selectedImageIndex: 0 });
        get().loadSlideImages(sid);
      },

      createSlide: async (content, position) => {
        const { slug } = get();
        if (!slug) return;

        set({ isSaving: true });
        try {
          const newSlide = await slidesApi.createSlide(slug, { content, position });
          const slides = [...get().slides];

          if (position !== undefined && position >= 0 && position <= slides.length) {
            slides.splice(position, 0, newSlide);
          } else {
            slides.push(newSlide);
          }

          set({
            slides,
            selectedSlideId: newSlide.sid,
            isSaving: false,
          });
        } catch (e) {
          set({ error: (e as Error).message, isSaving: false });
        }
      },

      updateSlide: async (sid, content) => {
        const { slug, selectedSlideId } = get();
        if (!slug) return;

        set({ isSaving: true });
        try {
          const updatedSlide = await slidesApi.updateSlide(slug, sid, { content });
          const slides = get().slides.map((s) =>
            s.sid === sid ? updatedSlide : s
          );
          set({ slides, isSaving: false });

          // Reload images if this is the currently selected slide
          if (selectedSlideId === sid) {
            get().loadSlideImages(sid);
          }
        } catch (e) {
          set({ error: (e as Error).message, isSaving: false });
        }
      },

      deleteSlide: async (sid) => {
        const { slug, slides, selectedSlideId } = get();
        if (!slug) return;

        set({ isSaving: true });
        try {
          await slidesApi.deleteSlide(slug, sid);
          const newSlides = slides.filter((s) => s.sid !== sid);

          // Select next slide if deleted was selected
          let newSelectedId = selectedSlideId;
          if (selectedSlideId === sid) {
            const deletedIndex = slides.findIndex((s) => s.sid === sid);
            newSelectedId =
              newSlides[deletedIndex]?.sid ??
              newSlides[deletedIndex - 1]?.sid ??
              null;
          }

          set({
            slides: newSlides,
            selectedSlideId: newSelectedId,
            isSaving: false,
          });

          if (newSelectedId) {
            get().loadSlideImages(newSelectedId);
          }
        } catch (e) {
          set({ error: (e as Error).message, isSaving: false });
        }
      },

      reorderSlides: async (slideIds) => {
        const { slug, slides } = get();
        if (!slug) return;

        // Optimistic update
        const reorderedSlides = slideIds
          .map((id) => slides.find((s) => s.sid === id))
          .filter((s): s is Slide => s !== undefined);

        set({ slides: reorderedSlides });

        try {
          await slidesApi.reorderSlides(slug, slideIds);
        } catch (e) {
          // Rollback on error
          set({ slides, error: (e as Error).message });
        }
      },

      // Image actions
      loadSlideImages: async (sid) => {
        const { slug, slides } = get();
        if (!slug) return;

        try {
          const data = await imagesApi.getSlideImages(slug, sid);
          const currentSlide = slides.find((s) => s.sid === sid);

          // Priority: default_image > hash match > first image
          let initialIndex = 0;
          if (currentSlide?.default_image) {
            const defaultIndex = data.images.findIndex(
              (img) => img.filename === currentSlide.default_image
            );
            if (defaultIndex >= 0) {
              initialIndex = defaultIndex;
            }
          } else {
            const hashMatchIndex = data.images.findIndex((img) => img.is_current);
            if (hashMatchIndex >= 0) {
              initialIndex = hashMatchIndex;
            }
          }

          set({
            currentImages: data.images,
            selectedImageIndex: initialIndex,
          });
        } catch (e) {
          set({ currentImages: [], error: (e as Error).message });
        }
      },

      generateImage: async (sid) => {
        const { slug } = get();
        if (!slug) return;

        set({ generatingSlideId: sid, error: null });
        try {
          const result = await imagesApi.generateImage(slug, sid);

          // Only update currentImages if still on the same slide
          const { selectedSlideId } = get();
          if (selectedSlideId === sid) {
            const images = [...get().currentImages];
            images.unshift(result.image);
            set({
              currentImages: images,
              selectedImageIndex: 0,
            });
          }

          // Update total cost
          const newCost = get().totalCost + result.generation_cost;

          // Update slide to show it has a matching image
          const slides = get().slides.map((s) =>
            s.sid === sid
              ? { ...s, has_matching_image: true, image_count: s.image_count + 1, latest_image: result.image.filename }
              : s
          );

          set({
            totalCost: newCost,
            slides,
            generatingSlideId: null,
          });
        } catch (e) {
          set({ error: (e as Error).message, generatingSlideId: null });
        }
      },

      selectImage: async (index) => {
        const { slug, selectedSlideId, currentImages } = get();
        set({ selectedImageIndex: index });

        // Save as default image
        if (slug && selectedSlideId && currentImages[index]) {
          const filename = currentImages[index].filename;
          try {
            await slidesApi.setDefaultImage(slug, selectedSlideId, filename);
            // Update slide's default_image in store
            const slides = get().slides.map((s) =>
              s.sid === selectedSlideId ? { ...s, default_image: filename } : s
            );
            set({ slides });
          } catch (e) {
            console.error('Failed to set default image:', e);
          }
        }
      },

      // Style actions
      generateStyleCandidates: async (prompt) => {
        const { slug } = get();
        if (!slug) return;

        set({ isGeneratingStyle: true, error: null, stylePrompt: prompt });
        try {
          const result = await styleApi.generateStyleCandidates(slug, prompt);
          set({
            styleCandidates: result.candidates,
            totalCost: get().totalCost + result.generation_cost,
            isGeneratingStyle: false,
          });
        } catch (e) {
          set({ error: (e as Error).message, isGeneratingStyle: false });
        }
      },

      selectStyle: async (candidateFilename) => {
        const { slug, stylePrompt } = get();
        if (!slug) return;

        set({ isSaving: true });
        try {
          const result = await styleApi.selectStyle(slug, stylePrompt, candidateFilename);
          set({
            style: result.style,
            styleCandidates: [],
            isSaving: false,
          });
        } catch (e) {
          set({ error: (e as Error).message, isSaving: false });
        }
      },

      setStylePrompt: (prompt) => {
        set({ stylePrompt: prompt });
      },

      clearStyleCandidates: () => {
        set({ styleCandidates: [], stylePrompt: '' });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    { name: 'SlideStore' }
  )
);
