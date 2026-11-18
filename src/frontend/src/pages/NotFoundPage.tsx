import Box from '@mui/material/Box';
import ErrorPage from './ErrorPage';

export default function NotFoundPage() {
  return (
    <Box data-testid="not-found-page">
      <ErrorPage statusCode={404} landmark={false} />
    </Box>
  );
}
