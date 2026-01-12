import type { Slide } from '@/types';

/**
 * Get the preferred image filename for a slide.
 * Priority: default_image > hash match > latest_image
 */
export function getSlideImageFilename(slide: Slide): string | null {
  // Priority 1: Use default_image if set
  if (slide.default_image) {
    return slide.default_image;
  }

  // Priority 2: Use matching image (hash match)
  if (slide.has_matching_image) {
    return `${slide.content_hash}.jpg`;
  }

  // Priority 3: Use latest image
  if (slide.latest_image) {
    return slide.latest_image;
  }

  return null;
}

/**
 * Build the full image URL for a slide.
 */
export function getSlideImageUrl(
  slug: string,
  sid: string,
  filename: string
): string {
  return `/api/slides/${slug}/${sid}/images/${filename}`;
}
