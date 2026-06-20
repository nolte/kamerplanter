import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import { listPlantPhotos } from '@/api/endpoints/plantPhotos';

interface PlantCoverPreviewProps {
  plantInstanceKey: string;
  /** Square edge length in pixels. */
  size?: number;
  /**
   * Pre-resolved cover thumbnail URI. When provided, the component renders it
   * directly and performs no fetch — used by list views that already loaded the
   * gallery. When omitted, the component lazily resolves the cover itself.
   */
  coverThumbUri?: string | null;
}

/**
 * REQ-034 §2.3 / AC-06 — cover-photo preview for the info tab and list views.
 *
 * Loads only the small (128px) thumbnail (AC-02), never the original. Plants
 * without any photo show a neutral botanical placeholder — never a broken image.
 */
export default function PlantCoverPreview({
  plantInstanceKey,
  size = 56,
  coverThumbUri,
}: PlantCoverPreviewProps) {
  const { t } = useTranslation();
  const hasExplicit = coverThumbUri !== undefined;
  // Self-resolved cover (only used when no explicit URI is passed).
  const [fetchedThumb, setFetchedThumb] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (hasExplicit) return;
    let active = true;
    setFailed(false);
    listPlantPhotos(plantInstanceKey)
      .then((result) => {
        if (!active) return;
        const cover = result.photos.find((p) => p.attachment_id === result.cover_photo_ref) ?? result.photos[0];
        setFetchedThumb(cover?.thumbnail_uris?.small ?? cover?.uri ?? null);
      })
      .catch(() => {
        if (active) setFetchedThumb(null);
      });
    return () => {
      active = false;
    };
  }, [plantInstanceKey, hasExplicit]);

  const thumb = hasExplicit ? (coverThumbUri ?? null) : fetchedThumb;
  const showPlaceholder = !thumb || failed;

  return (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: 1,
        overflow: 'hidden',
        flexShrink: 0,
        bgcolor: 'action.hover',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'text.disabled',
      }}
      data-testid="plant-cover-preview"
    >
      {showPlaceholder ? (
        <LocalFloristIcon
          aria-label={t('pages.plantPhotos.noCover')}
          data-testid="plant-cover-placeholder"
          sx={{ fontSize: size * 0.5 }}
        />
      ) : (
        <Box
          component="img"
          src={thumb}
          alt={t('pages.plantPhotos.coverAlt')}
          loading="lazy"
          onError={() => setFailed(true)}
          sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
          data-testid="plant-cover-image"
        />
      )}
    </Box>
  );
}
