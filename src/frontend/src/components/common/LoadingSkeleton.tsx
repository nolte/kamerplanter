import Box from '@mui/material/Box';
import Skeleton from '@mui/material/Skeleton';
import LoadingStatus from './LoadingStatus';

interface LoadingSkeletonProps {
  variant?: 'table' | 'form' | 'card';
  rows?: number;
}

/**
 * Loading placeholder for a page or a data region (UI-NFR-002).
 *
 * All three variants used to carry `aria-label` directly on the wrapping
 * `<div>` (`aria-busy="true" aria-label="Loading table"`). A `<div>` maps to
 * `generic`, ARIA prohibits naming a generic element, so the name was dropped
 * and nothing was ever announced — issue #1324. The wrapper keeps `aria-busy`
 * and gives up the name; {@link LoadingStatus} carries the role, the name and
 * the announceable text. See that component for why the role deliberately does
 * *not* sit on the busy wrapper.
 *
 * The three variants share one status region instead of each spelling out its
 * own label: three sibling branches with three hand-written strings is exactly
 * how one gets repaired and the other two do not. The wording also stops being
 * hard-coded English — the name is now actually reachable, so it has to follow
 * the UI language like every other announced string.
 */
export default function LoadingSkeleton({ variant = 'table', rows = 5 }: LoadingSkeletonProps) {
  if (variant === 'form') {
    return (
      <Box sx={{ maxWidth: 600, mt: 2 }} aria-busy="true" data-testid="loading-skeleton">
        <LoadingStatus />
        <Skeleton variant="text" width="40%" height={40} sx={{ mb: 3 }} />
        {Array.from({ length: 4 }).map((_, i) => (
          <Box key={i} sx={{ mb: 2 }}>
            <Skeleton variant="text" width="30%" height={20} />
            <Skeleton variant="rectangular" height={40} />
          </Box>
        ))}
        <Skeleton variant="rectangular" width={120} height={36} sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (variant === 'card') {
    return (
      <Box sx={{ mt: 2 }} aria-busy="true" data-testid="loading-skeleton">
        <LoadingStatus />
        <Skeleton variant="text" width="40%" height={40} sx={{ mb: 3 }} />
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} variant="rectangular" width={300} height={150} />
          ))}
        </Box>
      </Box>
    );
  }

  // table
  return (
    <Box sx={{ mt: 2 }} aria-busy="true" data-testid="loading-skeleton">
      <LoadingStatus />
      <Skeleton variant="text" width="40%" height={40} sx={{ mb: 2 }} />
      <Skeleton variant="rectangular" height={52} sx={{ mb: 1 }} />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" height={48} sx={{ mb: 0.5 }} />
      ))}
    </Box>
  );
}
