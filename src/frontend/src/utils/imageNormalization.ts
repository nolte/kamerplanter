/**
 * REQ-029-A §0.1.1 point 4 — client-side image normalization before upload.
 *
 * Downscales the longer edge to {@link MAX_EDGE} and re-encodes as JPEG. Drawing
 * the bitmap onto a `<canvas>` and reading it back drops all EXIF metadata
 * (including GPS), so the upload carries no location/orientation side-channel.
 * The backend strips EXIF again defensively; this is the first line of defence
 * and also keeps the payload comfortably under the 5 MB API limit.
 */

export const MAX_EDGE = 1280;
export const JPEG_QUALITY = 0.85;
export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;

/**
 * REQ-034 §2.2 — gallery photos are kept in higher resolution/quality than the
 * recognition-normalized images, because they document the plant's growth over
 * time. The recognition path keeps its smaller defaults.
 */
export const GALLERY_MAX_EDGE = 2048;
export const GALLERY_JPEG_QUALITY = 0.9;

const SUPPORTED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];

export interface NormalizedImage {
  file: File;
  /** Object URL for preview — caller is responsible for revoking it. */
  previewUrl: string;
}

export interface NormalizeImageOptions {
  /** Longest-edge cap in pixels (default {@link MAX_EDGE}). */
  maxEdge?: number;
  /** JPEG re-encode quality 0–1 (default {@link JPEG_QUALITY}). */
  quality?: number;
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('IMAGE_DECODE_FAILED'));
    img.src = url;
  });
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('CANVAS_ENCODE_FAILED'))),
      type,
      quality,
    );
  });
}

/**
 * Normalize a captured/selected image: optionally downscale, re-encode as JPEG,
 * strip metadata. Returns the new `File` and a preview object URL.
 *
 * The optional {@link NormalizeImageOptions} let callers raise the resolution
 * and quality (e.g. the gallery upload, REQ-034 §2.2) without affecting the
 * recognition defaults.
 *
 * @throws Error('UNSUPPORTED_FORMAT') for non-image inputs.
 */
export async function normalizeImage(
  input: File,
  options: NormalizeImageOptions = {},
): Promise<NormalizedImage> {
  const maxEdge = options.maxEdge ?? MAX_EDGE;
  const quality = options.quality ?? JPEG_QUALITY;
  const type = input.type.toLowerCase();
  if (type && !SUPPORTED_TYPES.includes(type) && !type.startsWith('image/')) {
    throw new Error('UNSUPPORTED_FORMAT');
  }

  const sourceUrl = URL.createObjectURL(input);
  try {
    const img = await loadImage(sourceUrl);
    const { width, height } = img;
    const longest = Math.max(width, height);
    const scale = longest > maxEdge ? maxEdge / longest : 1;
    const targetW = Math.max(1, Math.round(width * scale));
    const targetH = Math.max(1, Math.round(height * scale));

    const canvas = document.createElement('canvas');
    canvas.width = targetW;
    canvas.height = targetH;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('CANVAS_UNAVAILABLE');
    ctx.drawImage(img, 0, 0, targetW, targetH);

    const blob = await canvasToBlob(canvas, 'image/jpeg', quality);
    const baseName = input.name.replace(/\.[^./\\]+$/, '') || 'plant';
    const file = new File([blob], `${baseName}.jpg`, { type: 'image/jpeg' });
    const previewUrl = URL.createObjectURL(file);
    return { file, previewUrl };
  } finally {
    URL.revokeObjectURL(sourceUrl);
  }
}
