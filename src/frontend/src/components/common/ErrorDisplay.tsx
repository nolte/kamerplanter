import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import { useTranslation } from 'react-i18next';

/** Patterns that match raw backend error messages and map them to i18n keys. */
const ERROR_PATTERNS: Array<{ pattern: RegExp; key: string }> = [
  { pattern: /not found\.?$/i, key: 'errors.notFound' },
  { pattern: /already exists\.?$/i, key: 'errors.duplicate' },
  { pattern: /permission|forbidden|not allowed/i, key: 'errors.forbidden' },
  { pattern: /network\s*error/i, key: 'errors.network' },
  { pattern: /timed?\s*out/i, key: 'errors.networkTimeout' },
  { pattern: /input data is invalid/i, key: 'errors.validation' },
  { pattern: /internal error/i, key: 'errors.server' },
];

/** Matches an i18n key from the `errors.*` namespace (e.g. `errors.loadFailed`). */
const ERROR_KEY_PATTERN = /^errors\.[a-zA-Z0-9.]+$/;

function translateError(error: string, t: (key: string) => string): string {
  // Slices store i18n keys (FE-L5) — resolve them to the active locale directly.
  if (ERROR_KEY_PATTERN.test(error)) {
    return t(error);
  }
  for (const { pattern, key } of ERROR_PATTERNS) {
    if (pattern.test(error)) {
      return t(key);
    }
  }
  return error;
}

interface ErrorDisplayProps {
  error: string;
  onRetry?: () => void;
}

export default function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  const { t } = useTranslation();
  const displayMessage = translateError(error, t);

  return (
    <Box sx={{ my: 3 }} data-testid="error-display" role="alert">
      <Alert
        severity="error"
        sx={{ mb: onRetry ? 1.5 : 0 }}
        data-testid="error-message"
        action={
          onRetry ? (
            <Button
              color="inherit"
              size="small"
              onClick={onRetry}
              data-testid="error-retry-button"
            >
              {t('common.retry')}
            </Button>
          ) : undefined
        }
      >
        {displayMessage}
      </Alert>
    </Box>
  );
}
