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
    <Box sx={{ my: 3 }} data-testid="error-display">
      <Alert severity="error" sx={{ mb: 2 }} data-testid="error-message">
        {error}
      </Alert>
      {onRetry && (
        <Button variant="outlined" onClick={onRetry}>
          {t('common.back')}
        </Button>
      )}
    </Box>
  );
}
