import { get, post } from './index';
import type {
  SlideImagesResponse,
  GenerateImageResponse,
  GenerateImageRequest,
} from '@/types';

export const imagesApi = {
  getSlideImages: (slug: string, sid: string) =>
    get<SlideImagesResponse>(`/slides/${slug}/${sid}/images`),

  generateImage: (slug: string, sid: string, data?: GenerateImageRequest) =>
    post<GenerateImageResponse>(`/slides/${slug}/${sid}/generate`, data),

  getImageUrl: (slug: string, sid: string, filename: string) =>
    `/api/slides/${slug}/${sid}/images/${filename}`,
};
