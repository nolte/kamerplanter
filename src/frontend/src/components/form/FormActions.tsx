import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import { useTranslation } from 'react-i18next';

interface FormActionsProps {
  onCancel: () => void;
  loading?: boolean;
  saveLabel?: string;
  disabled?: boolean;
}

export default function FormActions({
  onCancel,
  loading = false,
  saveLabel,
  disabled = false,
}: FormActionsProps) {
  const { t } = useTranslation();

  return (
    <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
      <Button variant="outlined" onClick={onCancel} disabled={loading} data-testid="form-cancel-button">
        {t('common.cancel')}
      </Button>
      <Button
        type="submit"
        variant="contained"
        disabled={loading || disabled}
        startIcon={loading ? <CircularProgress size={16} /> : undefined}
        data-testid="form-submit-button"
      >
        {saveLabel ?? t('common.save')}
      </Button>
    </Box>
  );
}
