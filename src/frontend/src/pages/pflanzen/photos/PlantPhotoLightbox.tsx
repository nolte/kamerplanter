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
import EditIcon from '@mui/icons-material/Edit';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import { formatDate } from '@/utils/formatting';
import AuthImage from '@/components/common/AuthImage';
import type { PlantPhoto } from '@/api/endpoints/plantPhotos';
import QualityRatingBadge from './QualityRatingBadge';

interface PlantPhotoLightboxProps {
  /** The photo to show full-size, or `null` when the lightbox is closed. */
  photo: PlantPhoto | null;
  onClose: () => void;
  /** When true, the cover and delete action buttons are shown. */
  canWrite?: boolean;
  /** Called when the user wants to set this photo as cover (write-only). */
  onSetCover?: (photo: PlantPhoto) => void;
  /** Called when the user wants to edit caption/date — caller opens the dialog. */
  onEdit?: (photo: PlantPhoto) => void;
  /** Called when the user wants to check the photo's recognition quality. */
  onAssess?: (photo: PlantPhoto) => void;
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
  onEdit,
  onAssess,
  onDelete,
}: PlantPhotoLightboxProps) {
  const { t } = useTranslation();
  const src = photo ? (photo.thumbnail_uris?.large ?? photo.uri) : undefined;
  const closeRef = useRef<HTMLButtonElement>(null);
  // Display date: explicit capture date, else the upload date (REQ-034 §2.1).
  const displayDate = photo ? formatDate(photo.taken_on ?? photo.created_at) : '';

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

  const handleEdit = useCallback(() => {
    if (photo && onEdit) {
      onEdit(photo);
      onClose();
    }
  }, [photo, onEdit, onClose]);

  const handleAssess = useCallback(() => {
    if (photo && onAssess) {
      onAssess(photo);
      onClose();
    }
  }, [photo, onAssess, onClose]);

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
          /* Authenticated blob fetch (Bearer header) — loads the large (1280px)
             rendition; the grid never loads originals. */
          <AuthImage
            uri={src}
            alt={t('pages.plantPhotos.lightboxAlt')}
            objectFit="contain"
            width="100%"
            height="auto"
            sx={{
              maxHeight: { xs: '80vh', sm: '85vh' },
              bgcolor: 'transparent',
            }}
            data-testid="plant-photo-lightbox-image"
          />
        )}
      </DialogContent>

      {/* Metadata footer — capture date + full caption, visible to everyone
          (including viewers, AC-13). The grid only shows a truncated caption. */}
      {photo && (
        <Box
          sx={{ bgcolor: 'rgba(0, 0, 0, 0.75)', px: 2, pt: 1.5, pb: photo.caption ? 1.5 : 1 }}
          data-testid="plant-photo-lightbox-meta"
        >
          <Typography
            variant="caption"
            color="grey.400"
            sx={{ display: 'block' }}
            data-testid="plant-photo-lightbox-date"
          >
            {displayDate}
          </Typography>
          {photo.caption && (
            <Typography
              variant="body2"
              color="common.white"
              sx={{ mt: 0.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
              data-testid="plant-photo-lightbox-caption"
            >
              {photo.caption}
            </Typography>
          )}

          {/* Persisted quality verdict (REQ-034 §4a.2) — visible to everyone
              incl. viewers (AC-13): badge + the top suggestions. */}
          {photo.quality_assessment && (
            <Box sx={{ mt: 1.5 }} data-testid="plant-photo-lightbox-quality">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <QualityRatingBadge rating={photo.quality_assessment.rating} size="small" />
                <Typography variant="caption" color="grey.400">
                  {t(`pages.plantPhotos.quality.resultHeadline.${photo.quality_assessment.rating}`)}
                </Typography>
              </Box>
              {photo.quality_assessment.suggestions.length > 0 && (
                <Typography variant="caption" color="grey.400" sx={{ display: 'block', mt: 0.5 }}>
                  {t('pages.plantPhotos.quality.topSuggestion', {
                    name: photo.quality_assessment.suggestions[0].scientific_name,
                    percent: Math.round(photo.quality_assessment.suggestions[0].confidence * 100),
                  })}
                </Typography>
              )}
            </Box>
          )}
        </Box>
      )}

      {/* Write actions inside the lightbox — viewer sees none (AC-13). */}
      {canWrite && photo && (
        <DialogActions
          sx={{
            bgcolor: 'rgba(0, 0, 0, 0.75)',
            justifyContent: 'space-between',
            px: 2,
            py: 1,
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <Typography variant="caption" color="grey.400" sx={{ flexShrink: 0 }}>
            {photo.is_cover ? t('pages.plantPhotos.coverLabel') : ''}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {onAssess && (
              <Button
                size="small"
                startIcon={<FactCheckIcon />}
                onClick={handleAssess}
                sx={{ color: 'common.white' }}
                data-testid="plant-photo-lightbox-assess"
              >
                {t('pages.plantPhotos.quality.checkQuality')}
              </Button>
            )}
            {onEdit && (
              <Button
                size="small"
                startIcon={<EditIcon />}
                onClick={handleEdit}
                sx={{ color: 'common.white' }}
                data-testid="plant-photo-lightbox-edit"
              >
                {t('pages.plantPhotos.editPhoto')}
              </Button>
            )}
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
