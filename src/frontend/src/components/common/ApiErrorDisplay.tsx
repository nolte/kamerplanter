import ErrorPage from '@/pages/ErrorPage';
import ErrorDisplay from './ErrorDisplay';

interface ApiErrorDisplayProps {
  error: string;
  statusCode?: number;
  onRetry?: () => void;
}

const ILLUSTRATED_CODES = new Set([400, 401, 403, 404, 408, 429, 500, 502, 503]);

export default function ApiErrorDisplay({ error, statusCode, onRetry }: ApiErrorDisplayProps) {
  if (statusCode && ILLUSTRATED_CODES.has(statusCode)) {
    return <ErrorPage statusCode={statusCode} onRetry={onRetry} />;
  }

  return <ErrorDisplay error={error} onRetry={onRetry} />;
}
