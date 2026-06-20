import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined';
import type { QualityRating } from '@/api/endpoints/plantPhotos';

interface QualityRatingBadgeProps {
  rating: QualityRating;
  /** `small` for the thumbnail overlay, `medium` for the lightbox/details. */
  size?: 'small' | 'medium';
  /** Hide the text label (icon-only) — used for the compact thumbnail overlay. */
  iconOnly?: boolean;
  /** Optional `data-testid`. */
  'data-testid'?: string;
}

/**
 * REQ-034 §4a.2 — the image-quality traffic light as a coloured chip.
 *
 * Maps the derived rating onto theme palette tokens (no hex values, UI-NFR-006):
 * `good → success`, `fair → warning`, `poor → error`. The short label is
 * casual-user-friendly ("gut/brauchbar/ungeeignet"); the tooltip carries the
 * full explanation so the colour alone never has to carry the meaning (a11y,
 * UI-NFR-002 — colour is not the only signal: an icon + text accompany it).
 */
export default function QualityRatingBadge({
  rating,
  size = 'small',
  iconOnly = false,
  'data-testid': dataTestId,
}: QualityRatingBadgeProps) {
  const { t } = useTranslation();

  const config = useMemo(() => {
    const map = {
      good: { color: 'success' as const, icon: <CheckCircleIcon /> },
      fair: { color: 'warning' as const, icon: <WarningAmberIcon /> },
      poor: { color: 'error' as const, icon: <ErrorOutlineIcon /> },
    };
    const entry = map[rating];
    return {
      ...entry,
      label: t(`pages.plantPhotos.quality.rating.${rating}`),
      tooltip: t(`pages.plantPhotos.quality.ratingHint.${rating}`),
    };
  }, [rating, t]);

  return (
    <Tooltip title={config.tooltip}>
      <Chip
        icon={config.icon}
        label={iconOnly ? undefined : config.label}
        color={config.color}
        size={size}
        aria-label={`${t('pages.plantPhotos.quality.badgeLabel')}: ${config.label}`}
        data-testid={dataTestId ?? `quality-badge-${rating}`}
      />
    </Tooltip>
  );
}
