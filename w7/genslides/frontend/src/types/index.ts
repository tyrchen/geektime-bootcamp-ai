// Core domain types

export interface Style {
  prompt: string;
  image: string;
  image_url?: string;
}

export interface Slide {
  sid: string;
  content: string;
  content_hash: string;
  created_at: string;
  updated_at: string;
  has_matching_image: boolean;
  image_count: number;
  default_image: string | null;
  latest_image: string | null;
}

export interface Project {
  slug: string;
  title: string;
  style: Style | null;
  slides: Slide[];
  total_cost?: number;
}

// API Response types

export interface ProjectResponse {
  slug: string;
  title: string;
  style: Style | null;
  slides: Slide[];
  total_cost: number;
}

export interface SlideResponse {
  sid: string;
  content: string;
  content_hash: string;
  created_at: string;
  updated_at: string;
  has_matching_image: boolean;
  image_count: number;
  default_image: string | null;
  latest_image: string | null;
}

export interface CreateSlideRequest {
  title?: string;
  content: string;
  position?: number;
}

export interface UpdateSlideRequest {
  content: string;
}

export interface ReorderSlidesRequest {
  slide_ids: string[];
}

export interface ReorderSlidesResponse {
  success: boolean;
  slides: SlideResponse[];
}

export interface UpdateTitleRequest {
  title: string;
}

export interface UpdateTitleResponse {
  success: boolean;
  title: string;
}

export interface DeleteResponse {
  success: boolean;
  message: string;
}

export interface SetDefaultImageRequest {
  filename: string;
}

export interface SetDefaultImageResponse {
  success: boolean;
  default_image: string;
}

// Image types

export interface ImageInfo {
  filename: string;
  content_hash: string;
  url: string;
  is_current: boolean;
  created_at: string;
}

export interface SlideImagesResponse {
  sid: string;
  current_content_hash: string;
  images: ImageInfo[];
}

export interface GenerateImageRequest {
  prompt_override?: string;
}

export interface GenerateImageResponse {
  image: ImageInfo;
  generation_cost: number;
}

// Style types

export interface StyleCandidate {
  filename: string;
  url: string;
}

export interface GenerateStyleRequest {
  prompt: string;
}

export interface GenerateStyleResponse {
  candidates: StyleCandidate[];
  generation_cost: number;
}

export interface SelectStyleRequest {
  prompt: string;
  selected_image: string;
}

export interface StyleResponse {
  has_style: boolean;
  style: Style | null;
}

export interface SelectStyleResponse {
  success: boolean;
  style: Style;
}

// Cost types

export interface CostBreakdown {
  slide_images: number;
  style_images: number;
}

export interface CostResponse {
  slug: string;
  total_cost: number;
  currency: string;
  breakdown: CostBreakdown;
  image_count: number;
  cost_per_image: number;
}

// API Error type

export interface ApiError {
  detail: string;
  error_code?: string;
}
