import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import { useTranslation } from 'react-i18next';
import type { Translate } from '@/i18n/translate';

/** An i18n key such as `errors.loadFailed` or `pages.bed.photos.loadError`. */
const I18N_KEY_PATTERN = /^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z0-9_]+)+$/;

/**
 * Resolve the `error` prop (FRONTEND.md §10.3, #3013).
 *
 * Slices and `errorKey` hand over an i18n **key**, which is translated here.
 * A caller that already translated (`t('errors.notFound')`, `parseApiError(err, t)`)
 * passes a sentence, which is shown as given. There is no English
 * pattern table any more: the producers no longer emit backend text, and a key
 * the bundle does not know falls back to the generic message instead of being
 * shown raw.
 */
function translateError(error: string, t: Translate): string {
  if (I18N_KEY_PATTERN.test(error)) {
    return t(error, { defaultValue: t('errors.generic') });
  }
  return error;
}

interface ErrorDisplayProps {
  /** An i18n key (preferred — e.g. a slice's `error`) or an already translated message. */
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
