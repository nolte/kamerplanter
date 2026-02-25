import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import InboxIcon from '@mui/icons-material/Inbox';
import { useTranslation } from 'react-i18next';

interface EmptyStateProps {
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ message, actionLabel, onAction }: EmptyStateProps) {
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        py: 6,
        color: 'text.secondary',
      }}
      data-testid="empty-state"
    >
      <InboxIcon sx={{ fontSize: 64, mb: 2, opacity: 0.5 }} aria-hidden="true" />
      <Typography variant="body1" sx={{ mb: 2 }}>
        {message ?? t('common.noData')}
      </Typography>
      {actionLabel && onAction && (
        <Button variant="contained" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </Box>
  );
}
