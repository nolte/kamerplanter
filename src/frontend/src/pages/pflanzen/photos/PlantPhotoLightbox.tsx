import { useCallback, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import DeleteIcon from '@mui/icons-material/Delete';
import type { PlantPhoto } from '@/api/endpoints/plantPhotos';

interface PlantPhotoLightboxProps {
  /** The photo to show full-size, or `null` when the lightbox is closed. */
  photo: PlantPhoto | null;
  onClose: () => void;
  /** When true, the cover and delete action buttons are shown. */
  canWrite?: boolean;
  /** Called when the user wants to set this photo as cover (write-only). */
  onSetCover?: (photo: PlantPhoto) => void;
  /** Called when the user requests deletion — caller shows the confirm dialog. */
  onDelete?: (photo: PlantPhoto) => void;
}

/**
 * REQ-034 §2.3 / AC-02 — full-size photo viewer. Loads the large (1280px)
 * rendition when available, falling back to the original URI. Only opened on an
 * explicit click; the grid itself never loads originals.
 *
 * A11y (UI-NFR-002): focus is trapped inside the Dialog by MUI; the close button
 * receives autoFocus so keyboard users can immediately dismiss with Enter/Space.
 * Escape always closes (Dialog default). The dialog has an accessible title via
 * aria-labelledby so screen readers announce context on open.
 */
export default function PlantPhotoLightbox({
  photo,
  onClose,
  canWrite = false,
  onSetCover,
  onDelete,
}: PlantPhotoLightboxProps) {
  const { t } = useTranslation();
  const src = photo ? (photo.thumbnail_uris?.large ?? photo.uri) : undefined;
  const closeRef = useRef<HTMLButtonElement>(null);

  // Move focus to the close button when the lightbox opens so keyboard users
  // and screen readers have an immediate, labelled entry point (UI-NFR-008 R-010).
  useEffect(() => {
    if (photo) {
      // Defer to let MUI's Dialog finish its own focus sequence first.
      const id = setTimeout(() => closeRef.current?.focus(), 50);
      return () => clearTimeout(id);
    }
  }, [photo]);

  const handleSetCover = useCallback(() => {
    if (photo && onSetCover) {
      onSetCover(photo);
      onClose();
    }
  }, [photo, onSetCover, onClose]);

  const handleDelete = useCallback(() => {
    if (photo && onDelete) {
      onDelete(photo);
      onClose();
    }
  }, [photo, onDelete, onClose]);

  return (
    <Dialog
      open={photo !== null}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      data-testid="plant-photo-lightbox"
      aria-labelledby="lightbox-dialog-title"
      sx={{
        '& .MuiDialog-paper': {
          bgcolor: 'common.black',
          m: { xs: 0, sm: 2 },
          width: { xs: '100%', sm: 'auto' },
          maxWidth: { sm: 'lg' },
          borderRadius: { xs: 0, sm: 2 },
        },
      }}
    >
      {/* Visually hidden title satisfies aria-labelledby for screen readers
          without disturbing the visual black-background photo layout. */}
      <DialogTitle
        id="lightbox-dialog-title"
        sx={{
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          clip: 'rect(0 0 0 0)',
          clipPath: 'inset(50%)',
          whiteSpace: 'nowrap',
        }}
      >
        {t('pages.plantPhotos.lightboxTitle')}
      </DialogTitle>

      <DialogContent
        sx={{
          p: 0,
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: { xs: '60vw', sm: 300 },
          '&.MuiDialogContent-root': { p: 0 },
        }}
      >
        {/* Close button — autoFocused via ref for keyboard entry point (UI-NFR-008 R-010) */}
        <IconButton
          ref={closeRef}
          onClick={onClose}
          aria-label={t('common.close')}
          data-testid="plant-photo-lightbox-close"
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            zIndex: 1,
            color: 'common.white',
            bgcolor: 'rgba(0, 0, 0, 0.55)',
            '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.75)' },
            '&:focus-visible': {
              outline: '2px solid',
              outlineColor: 'primary.main',
              outlineOffset: 2,
            },
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
              maxHeight: { xs: '80vh', sm: '85vh' },
              objectFit: 'contain',
            }}
            data-testid="plant-photo-lightbox-image"
          />
        )}
      </DialogContent>

      {/* Write actions inside the lightbox — viewer sees none (AC-13). */}
      {canWrite && photo && (
        <DialogActions
          sx={{
            bgcolor: 'rgba(0, 0, 0, 0.75)',
            justifyContent: 'space-between',
            px: 2,
            py: 1,
          }}
        >
          <Typography variant="caption" color="grey.400" sx={{ flexShrink: 0 }}>
            {photo.is_cover ? t('pages.plantPhotos.coverLabel') : ''}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {!photo.is_cover && onSetCover && (
              <Button
                size="small"
                startIcon={<StarBorderIcon />}
                onClick={handleSetCover}
                sx={{ color: 'common.white' }}
              >
                {t('pages.plantPhotos.setCover')}
              </Button>
            )}
            {onDelete && (
              <Button
                size="small"
                startIcon={<DeleteIcon />}
                onClick={handleDelete}
                color="error"
                sx={{ color: 'error.light' }}
              >
                {t('common.delete')}
              </Button>
            )}
          </Box>
        </DialogActions>
      )}
    </Dialog>
  );
}
