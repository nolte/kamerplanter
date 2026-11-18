import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import type { SxProps, Theme } from '@mui/material/styles';
import { captureHandledError } from '@/observability/errorTracking';

type IllustrationModule = { default: string };

/**
 * #3023 (P-02) — the error illustrations are loaded on demand, one dynamic import per status code.
 *
 * Both error pages render inside the eagerly loaded shell (the router's error element sits on the
 * root route), so a static `import` of all nine illustrations put their URLs into the entry chunk
 * and tied the files to the first paint. Behind `import()` each illustration is its own tiny chunk
 * that is fetched only when an error page actually shows that status code.
 */
const errorIllustrationLoaders: Readonly<Record<number, () => Promise<IllustrationModule>>> = {
  400: () => import('@/assets/illustrations/errors/error-400.svg'),
  401: () => import('@/assets/illustrations/errors/error-401.svg'),
  403: () => import('@/assets/illustrations/errors/error-403.svg'),
  404: () => import('@/assets/illustrations/errors/error-404.svg'),
  408: () => import('@/assets/illustrations/errors/error-408.svg'),
  429: () => import('@/assets/illustrations/errors/error-429.svg'),
  500: () => import('@/assets/illustrations/errors/error-500.svg'),
  502: () => import('@/assets/illustrations/errors/error-502.svg'),
  503: () => import('@/assets/illustrations/errors/error-503.svg'),
};

/** The loader for a status code; an unknown code falls back to the 500 illustration. */
function loaderFor(statusCode: number): () => Promise<IllustrationModule> {
  return errorIllustrationLoaders[statusCode] ?? errorIllustrationLoaders[500];
}

/** Intrinsic size of every illustration (1200 x 896); reserves the box while the file loads. */
const ASPECT_RATIO = '1200 / 896';

interface ErrorIllustrationProps {
  statusCode: number;
  sx?: SxProps<Theme>;
}

/** The decorative illustration of an error page, loaded lazily for its status code. */
export default function ErrorIllustration({ statusCode, sx }: ErrorIllustrationProps) {
  const load = loaderFor(statusCode);
  const [resolved, setResolved] = useState<{ load: () => Promise<IllustrationModule>; url: string } | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;
    load()
      .then((module) => {
        if (!cancelled) setResolved({ load, url: module.default });
      })
      .catch((err: unknown) => {
        // Decorative only: the page names the error in text, so a missing picture keeps the reserved space.
        captureHandledError(err, { source: 'ErrorIllustration.load', statusCode });
      });
    return () => {
      cancelled = true;
    };
  }, [load, statusCode]);

  const url = resolved?.load === load ? resolved.url : null;
  const baseSx: SxProps<Theme> = { maxWidth: 320, width: '100%', height: 'auto', aspectRatio: ASPECT_RATIO, mb: 3 };
  const mergedSx = [baseSx, ...(Array.isArray(sx) ? sx : [sx])] as SxProps<Theme>;

  if (url === null) {
    return <Box aria-hidden="true" data-testid="error-illustration-placeholder" sx={mergedSx} />;
  }
  return (
    <Box
      component="img"
      src={url}
      alt=""
      aria-hidden="true"
      decoding="async"
      data-testid="error-illustration"
      sx={mergedSx}
    />
  );
}
