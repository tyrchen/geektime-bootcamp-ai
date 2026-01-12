import { get, post, put, del } from './index';
import type {
  ProjectResponse,
  SlideResponse,
  CreateSlideRequest,
  UpdateSlideRequest,
  ReorderSlidesResponse,
  UpdateTitleResponse,
  DeleteResponse,
  SetDefaultImageResponse,
} from '@/types';

export const slidesApi = {
  getProject: (slug: string) =>
    get<ProjectResponse>(`/slides/${slug}`),

  createSlide: (slug: string, data: CreateSlideRequest) =>
    post<SlideResponse>(`/slides/${slug}`, data),

  updateSlide: (slug: string, sid: string, data: UpdateSlideRequest) =>
    put<SlideResponse>(`/slides/${slug}/${sid}`, data),

  deleteSlide: (slug: string, sid: string) =>
    del<DeleteResponse>(`/slides/${slug}/${sid}`),

  reorderSlides: (slug: string, slideIds: string[]) =>
    put<ReorderSlidesResponse>(`/slides/${slug}/reorder`, { slide_ids: slideIds }),

  updateTitle: (slug: string, title: string) =>
    put<UpdateTitleResponse>(`/slides/${slug}/title`, { title }),

  setDefaultImage: (slug: string, sid: string, filename: string) =>
    put<SetDefaultImageResponse>(`/slides/${slug}/${sid}/default-image`, { filename }),
};
