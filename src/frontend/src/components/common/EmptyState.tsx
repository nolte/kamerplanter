import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { useTranslation } from 'react-i18next';
import { kamiStateEmpty } from '@/assets/brand/illustrations';

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
      {/*
        Decorative KAMI illustration — alt="" + aria-hidden is correct here
        since the surrounding message/description already carries the
        meaning (WCAG 1.1.1 decorative-image exception).
        maxHeight/opacity 180/0.85 is the shared "primary empty-state anchor"
        convention (see also DashboardPage's empty dashboard state); smaller
        supplementary illustrations shown alongside active content use
        150/0.9 instead (OnboardingWizard, KIAssistentPage, DiagnosePage).
        Dark-mode note: these vtracer-traced SVGs include some near-black
        detail fills (e.g. #1b1209/#2e291b) which sit close in value to the
        dark palette's background.default (#121212). Because the image is
        purely decorative (no WCAG 1.4.11 obligation), this is a visual nice
        -to-have, not an a11y bug — flag to the KAMI asset pipeline if a
        future regen should bake in a lighter outline for dark-mode legibility.
      */}
      <Box
        component="img"
        src={illustration ?? kamiStateEmpty}
        alt=""
        aria-hidden="true"
        sx={{ maxHeight: 180, maxWidth: '100%', objectFit: 'contain', mb: 2, opacity: 0.85 }}
      />
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
