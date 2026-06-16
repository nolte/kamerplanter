import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Avatar from '@mui/material/Avatar';
import Tooltip from '@mui/material/Tooltip';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';

interface SpeciesThumbnailProps {
  /** External CC0/CC-BY image URL, or null when no representative image exists. */
  imageUrl?: string | null;
  /** Author/attribution — legally required to surface for CC-BY images. */
  attribution?: string | null;
  /** License identifier (e.g. "CC0", "CC-BY"). */
  license?: string | null;
  /** Accessible name for the avatar (typically the scientific name). */
  alt: string;
  /**
   * Avatar edge length in px.
   * Note: UI-NFR-001 R-011 requires touch-targets ≥ 48 px on mobile; callers
   * should wrap the thumbnail in a sufficiently large hit area when used as a
   * standalone interactive element. The default of 48 satisfies the requirement
   * for the MobileCard trailing slot.
   */
  size?: number;
}

/**
 * Small rounded species thumbnail for list/table/mobile-card contexts (REQ-029-A).
 *
 * Renders the external representative image when present, otherwise a neutral
 * plant-icon fallback — never a broken-image placeholder. A failed image load
 * (`onError`) clears the source so the icon fallback shows instead. Attribution
 * is surfaced via Tooltip (the small size makes a visible caption impractical;
 * the full caption is shown on the detail hero and gallery).
 *
 * The icon fallback carries an aria-label matching `alt` so screen-readers
 * still announce the species name even when no image is available.
 */
export function SpeciesThumbnail({
  imageUrl,
  attribution,
  license,
  alt,
  size = 48,
}: SpeciesThumbnailProps) {
  const { t } = useTranslation();
  const [failed, setFailed] = useState(false);
  const showImage = !!imageUrl && !failed;

  const avatar = (
    <Avatar
      variant="rounded"
      src={showImage ? imageUrl : undefined}
      alt={showImage ? alt : ''}
      aria-label={!showImage ? alt : undefined}
      sx={{
        width: size,
        height: size,
        bgcolor: 'action.hover',
        color: 'text.secondary',
        flexShrink: 0,
      }}
      slotProps={{
        img: {
          loading: 'lazy',
          referrerPolicy: 'no-referrer',
          onError: () => setFailed(true),
        },
      }}
      data-testid="species-thumbnail"
    >
      {/* aria-hidden: the Avatar itself carries the label via aria-label above */}
      <LocalFloristIcon fontSize="small" aria-hidden="true" />
    </Avatar>
  );

  if (!showImage) {
    return avatar;
  }

  const tooltipText = attribution
    ? t('pages.species.referenceImages.attributionTooltip', {
        attribution,
        license: license ?? '',
      })
    : (license ?? '');

  if (!tooltipText) {
    return avatar;
  }

  return (
    <Tooltip
      title={tooltipText.trim()}
      enterTouchDelay={0}
      leaveTouchDelay={3000}
    >
      {avatar}
    </Tooltip>
  );
}

export default SpeciesThumbnail;
