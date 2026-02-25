import Box from '@mui/material/Box';
import Skeleton from '@mui/material/Skeleton';

interface LoadingSkeletonProps {
  variant?: 'table' | 'form' | 'card';
  rows?: number;
}

export default function LoadingSkeleton({ variant = 'table', rows = 5 }: LoadingSkeletonProps) {
  if (variant === 'form') {
    return (
      <Box sx={{ maxWidth: 600, mt: 2 }} aria-busy="true" aria-label="Loading form" data-testid="loading-skeleton">
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
      <Box sx={{ mt: 2 }} aria-busy="true" aria-label="Loading cards" data-testid="loading-skeleton">
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
    <Box sx={{ mt: 2 }} aria-busy="true" aria-label="Loading table" data-testid="loading-skeleton">
      <Skeleton variant="text" width="40%" height={40} sx={{ mb: 2 }} />
      <Skeleton variant="rectangular" height={52} sx={{ mb: 1 }} />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" height={48} sx={{ mb: 0.5 }} />
      ))}
    </Box>
  );
}
