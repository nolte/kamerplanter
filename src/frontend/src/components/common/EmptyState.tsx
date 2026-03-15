import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import InboxIcon from '@mui/icons-material/Inbox';
import { useTranslation } from 'react-i18next';

interface EmptyStateProps {
  message?: string;
  /** Optional secondary description shown below the main message. */
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  illustration?: string;
}

export default function EmptyState({
  message,
  description,
  actionLabel,
  onAction,
  illustration,
}: EmptyStateProps) {
  const { t } = useTranslation();

  return (
    <Box
      role="status"
      aria-live="polite"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        py: 6,
        px: 2,
        color: 'text.secondary',
        textAlign: 'center',
      }}
      data-testid="empty-state"
    >
      {illustration ? (
        <Box
          component="img"
          src={illustration}
          alt=""
          aria-hidden="true"
          sx={{ maxHeight: 180, maxWidth: '100%', objectFit: 'contain', mb: 2, opacity: 0.85 }}
        />
      ) : (
        <InboxIcon sx={{ fontSize: 64, mb: 2, opacity: 0.4 }} aria-hidden="true" />
      )}
      <Typography variant="body1" sx={{ mb: description ? 0.5 : 2, fontWeight: 500 }}>
        {message ?? t('common.noData')}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, maxWidth: 400 }}>
          {description}
        </Typography>
      )}
      {actionLabel && onAction && (
        <Button
          variant="contained"
          onClick={onAction}
          data-testid="empty-state-action"
        >
          {actionLabel}
        </Button>
      )}
    </Box>
  );
}
