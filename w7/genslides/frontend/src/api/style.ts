import { get, post, put } from './index';
import type {
  StyleResponse,
  GenerateStyleResponse,
  SelectStyleResponse,
} from '@/types';

export const styleApi = {
  getStyle: (slug: string) =>
    get<StyleResponse>(`/slides/${slug}/style`),

  generateStyleCandidates: (slug: string, prompt: string) =>
    post<GenerateStyleResponse>(`/slides/${slug}/style/generate`, { prompt }),

  selectStyle: (slug: string, prompt: string, selectedImage: string) =>
    put<SelectStyleResponse>(`/slides/${slug}/style`, {
      prompt,
      selected_image: selectedImage,
    }),

  getStyleImageUrl: (slug: string, filename: string) =>
    `/api/slides/${slug}/style/${filename}`,
};
