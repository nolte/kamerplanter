import type { CSSProperties } from 'react';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Skeleton from '@mui/material/Skeleton';
import BrokenImageIcon from '@mui/icons-material/BrokenImage';
import type { SxProps, Theme } from '@mui/material/styles';
import { useAuthImage } from '@/hooks/useAuthImage';

interface AuthImageProps {
  /**
   * Full backend attachment URI, e.g.
   * `/api/v1/t/{slug}/attachments/{id}/thumbnails/512`. The image bytes are
   * fetched through the authenticated axios client and shown via an Object-URL.
   */
  uri: string | null | undefined;
  /** Accessible alternative text. Pass `''` when an ancestor already labels the image. */
  alt: string;
  width?: number | string;
  height?: number | string;
  /** `object-fit` for the rendered image. Defaults to `cover`. */
  objectFit?: CSSProperties['objectFit'];
  /** Forwarded to the underlying MUI `Box` (image) for sizing/positioning. */
  sx?: SxProps<Theme>;
  /** Escape hatch for inline styles when `sx` is not convenient. */
  style?: CSSProperties;
  /** Test id for the rendered `<img>` (placeholder/skeleton get suffixed ids). */
  'data-testid'?: string;
  /**
   * Called once the blob load fails. Lets callers render a domain-specific
   * fallback (e.g. a botanical placeholder) instead of the default broken-image
   * box. When provided, the default error box is still rendered unless the caller
   * stops mounting the component.
   */
  onError?: () => void;
  /** Called once the blob loaded successfully. */
  onLoad?: () => void;
}

/**
 * REQ-034 — renders a permission-gated plant-photo attachment.
 *
 * The gallery thumbnail and original-download endpoints are
 * `require_attachment_permission(READ)`-gated and require a JWT Bearer header. A
 * native `<img src={uri}>` cannot send that header (the token lives only on the
 * axios request interceptor), so it would 401/403 into a broken image. This
 * component instead fetches the bytes authenticated as a blob (see
 * {@link useAuthImage}) and points the `<img>` at the resulting Object-URL.
 *
 * Renders a {@link Skeleton} while loading and a neutral broken-image icon on
 * failure — never a browser's broken-image glyph.
 *
 * S3 backend (known follow-up, NFR-013 §2.4): with the `s3` storage backend a
 * `GET /attachments/{id}` returns a 307 redirect to a presigned URL. axios
 * follows redirects, but the Bearer header is then also sent to the presign host;
 * depending on the bucket's signing policy this may be rejected. The development
 * default is `local-fs`, which streams the bytes through the API proxy and works
 * cleanly with this blob approach. Hardening the s3 redirect path (e.g. dropping
 * the Authorization header on cross-origin redirect) is deferred follow-up work.
 */
export default function AuthImage({
  uri,
  alt,
  width = '100%',
  height = '100%',
  objectFit = 'cover',
  sx,
  style,
  'data-testid': testId,
  onError,
  onLoad,
}: AuthImageProps) {
  const { t } = useTranslation();
  const { objectUrl, status } = useAuthImage(uri);

  useEffect(() => {
    if (status === 'error') onError?.();
    else if (status === 'loaded') onLoad?.();
  }, [status, onError, onLoad]);

  // `height: 'auto'` is meaningful for the loaded <img> (natural aspect ratio),
  // but a flex/skeleton placeholder with auto height collapses to 0px. Fall back
  // to filling the parent so loading/error states stay visible.
  const placeholderHeight = height === 'auto' ? '100%' : height;
  const sizingSx: SxProps<Theme> = {
    width,
    height: placeholderHeight,
    minHeight: height === 'auto' ? 120 : undefined,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    bgcolor: 'action.hover',
    color: 'text.disabled',
    overflow: 'hidden',
    flexShrink: 0,
  };

  if (status === 'loading') {
    return (
      <Box sx={sizingSx} style={style} data-testid={testId ? `${testId}-loading` : undefined}>
        <Skeleton
          variant="rectangular"
          width="100%"
          height="100%"
          sx={{ transform: 'none' }}
          aria-label={alt || undefined}
        />
      </Box>
    );
  }

  if (status === 'error' || !objectUrl) {
    return (
      <Box
        role="img"
        aria-label={alt || t('pages.plantPhotos.imageError')}
        title={t('pages.plantPhotos.imageError')}
        sx={sizingSx}
        style={style}
        data-testid={testId ? `${testId}-error` : undefined}
      >
        <BrokenImageIcon aria-hidden="true" />
      </Box>
    );
  }

  return (
    <Box
      component="img"
      src={objectUrl}
      alt={alt}
      sx={[{ width, height, objectFit, display: 'block' }, ...(Array.isArray(sx) ? sx : [sx])]}
      style={style}
      data-testid={testId}
    />
  );
}
