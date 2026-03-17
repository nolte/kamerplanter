import { useCallback } from 'react';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import { useTranslation } from 'react-i18next';

interface FavoriteToggleProps {
  favorited: boolean;
  onToggle: () => void;
  size?: 'small' | 'medium';
  disabled?: boolean;
  /** Additional data-testid suffix so multiple toggles on one page are distinguishable */
  testId?: string;
}

export default function FavoriteToggle({
  favorited,
  onToggle,
  size = 'medium',
  disabled = false,
  testId,
}: FavoriteToggleProps) {
  const { t } = useTranslation();

  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onToggle();
    },
    [onToggle],
  );

  const label = favorited ? t('common.removeFavorite') : t('common.addFavorite');

  return (
    <Tooltip title={label}>
      {/* span is required so the Tooltip works when the button is disabled */}
      <span>
        <IconButton
          onClick={handleClick}
          disabled={disabled}
          size={size}
          aria-label={label}
          aria-pressed={favorited}
          data-testid={testId ? `favorite-toggle-${testId}` : 'favorite-toggle'}
          sx={{
            // Meet 48×48 px touch target requirement (UI-NFR-001 R-011)
            minWidth: 48,
            minHeight: 48,
            color: favorited ? 'warning.main' : 'action.disabled',
            transition: 'color 0.2s ease, transform 0.15s ease',
            '&:hover': {
              color: favorited ? 'warning.dark' : 'warning.light',
            },
            // Subtle pop when toggled on — respects prefers-reduced-motion
            '@media (prefers-reduced-motion: no-preference)': {
              '&:active': {
                transform: 'scale(1.2)',
              },
            },
          }}
        >
          {favorited ? (
            <StarIcon aria-hidden="true" />
          ) : (
            <StarBorderIcon aria-hidden="true" />
          )}
        </IconButton>
      </span>
    </Tooltip>
  );
}
