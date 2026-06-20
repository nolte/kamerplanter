import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import type { PlantPhoto } from '@/api/endpoints/plantPhotos';

interface PlantPhotoLightboxProps {
  /** The photo to show full-size, or `null` when the lightbox is closed. */
  photo: PlantPhoto | null;
  onClose: () => void;
}

/**
 * REQ-034 §2.3 / AC-02 — full-size photo viewer. Loads the large (1280px)
 * rendition when available, falling back to the original URI. Only opened on an
 * explicit click; the grid itself never loads originals.
 */
export default function PlantPhotoLightbox({ photo, onClose }: PlantPhotoLightboxProps) {
  const { t } = useTranslation();
  const src = photo ? (photo.thumbnail_uris?.large ?? photo.uri) : undefined;

  return (
    <Dialog
      open={photo !== null}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      data-testid="plant-photo-lightbox"
      aria-label={t('pages.plantPhotos.lightboxAlt')}
    >
      <Box sx={{ position: 'relative', bgcolor: 'common.black' }}>
        <IconButton
          onClick={onClose}
          aria-label={t('common.close')}
          data-testid="plant-photo-lightbox-close"
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: 'common.white',
            bgcolor: 'rgba(0, 0, 0, 0.4)',
            '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.6)' },
          }}
        >
          <CloseIcon />
        </IconButton>
        {src && (
          <Box
            component="img"
            src={src}
            alt={t('pages.plantPhotos.lightboxAlt')}
            sx={{
              display: 'block',
              width: '100%',
              maxHeight: '85vh',
              objectFit: 'contain',
            }}
            data-testid="plant-photo-lightbox-image"
          />
        )}
      </Box>
    </Dialog>
  );
}
