import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import { useTranslation } from 'react-i18next';

interface OptionsLoadErrorProps {
  /** Re-runs the failed load, e.g. `useAsyncOptions().reload`. */
  onRetry: () => void;
  /** i18n key of the message; defaults to the generic `errors.optionsLoadFailed`. */
  messageKey?: string;
  'data-testid'?: string;
}

/**
 * Inline failure for a picker or filter whose options did not load (#3013).
 *
 * The counterpart of `CatalogueLoadError` for option lists that are not a
 * seeded catalogue (`useAsyncOptions`): a failed load must not read as "there
 * are no entries". The retry is a real button with a 48 px hit area
 * (UI-NFR-001 R-011); MUI's `Alert` announces the failure (`role="alert"`).
 */
export default function OptionsLoadError({
  onRetry,
  messageKey = 'errors.optionsLoadFailed',
  'data-testid': testId = 'options-load-error',
}: OptionsLoadErrorProps) {
  const { t } = useTranslation();
  return (
    <Alert
      severity="error"
      sx={{ flexBasis: '100%', my: 1 }}
      data-testid={testId}
      action={
        <Button color="inherit" size="small" onClick={onRetry} sx={{ minHeight: 48, minWidth: 48 }} data-testid={`${testId}-retry`}>
          {t('common.retry')}
        </Button>
      }
    >
      {t(messageKey)}
    </Alert>
  );
}
