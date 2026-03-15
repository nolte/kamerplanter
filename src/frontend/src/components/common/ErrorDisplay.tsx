import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import { useTranslation } from 'react-i18next';

interface ErrorDisplayProps {
  error: string;
  onRetry?: () => void;
}

export default function ErrorDisplay({ error, onRetry }: ErrorDisplayProps) {
  const { t } = useTranslation();

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
        {error}
      </Alert>
    </Box>
  );
}
