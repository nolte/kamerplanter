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

const SUPPORTED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif'];

export interface NormalizedImage {
  file: File;
  /** Object URL for preview — caller is responsible for revoking it. */
  previewUrl: string;
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
 * @throws Error('UNSUPPORTED_FORMAT') for non-image inputs.
 */
export async function normalizeImage(input: File): Promise<NormalizedImage> {
  const type = input.type.toLowerCase();
  if (type && !SUPPORTED_TYPES.includes(type) && !type.startsWith('image/')) {
    throw new Error('UNSUPPORTED_FORMAT');
  }

  const sourceUrl = URL.createObjectURL(input);
  try {
    const img = await loadImage(sourceUrl);
    const { width, height } = img;
    const longest = Math.max(width, height);
    const scale = longest > MAX_EDGE ? MAX_EDGE / longest : 1;
    const targetW = Math.max(1, Math.round(width * scale));
    const targetH = Math.max(1, Math.round(height * scale));

    const canvas = document.createElement('canvas');
    canvas.width = targetW;
    canvas.height = targetH;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('CANVAS_UNAVAILABLE');
    ctx.drawImage(img, 0, 0, targetW, targetH);

    const blob = await canvasToBlob(canvas, 'image/jpeg', JPEG_QUALITY);
    const baseName = input.name.replace(/\.[^./\\]+$/, '') || 'plant';
    const file = new File([blob], `${baseName}.jpg`, { type: 'image/jpeg' });
    const previewUrl = URL.createObjectURL(file);
    return { file, previewUrl };
  } finally {
    URL.revokeObjectURL(sourceUrl);
  }
}
