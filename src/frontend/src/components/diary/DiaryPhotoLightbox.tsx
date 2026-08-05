import { useEffect, useRef } from 'react';
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
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import AuthImage from '@/components/common/AuthImage';
import { diaryPhotoUri } from '@/api/endpoints/diary';

interface DiaryPhotoLightboxProps {
  /** All attachment ids of the entry, so the viewer can page through them. */
  photoRefs: string[];
  /** Index of the photo to show, or `null` when the lightbox is closed. */
  index: number | null;
  onClose: () => void;
  onNavigate: (index: number) => void;
}

/**
 * REQ-050 §2.5.1 — full-size viewer for the photos of a diary entry.
 *
 * **Why not `PlantPhotoLightbox`.** That component is typed on `PlantPhoto`
 * (`api/endpoints/plantPhotos.ts:50`) and needs `uri`, `thumbnail_uris`,
 * `is_cover`, `taken_on`, `caption` and `quality_assessment` — none of which a
 * diary entry has; `photo_refs` is a list of bare attachment ids. It also
 * offers "set as cover", "assess quality" and "edit metadata", three gallery
 * actions that mean nothing on a diary photo. Reusing it would have meant
 * fabricating a fake gallery photo per id and then suppressing three quarters
 * of the dialog.
 *
 * Loads the 1280-px rendition, never the original — the same rule the gallery
 * follows and the same one §4.4 imposes on the MCP path.
 */
export default function DiaryPhotoLightbox({
  photoRefs,
  index,
  onClose,
  onNavigate,
}: DiaryPhotoLightboxProps) {
  const { t } = useTranslation();
  const closeRef = useRef<HTMLButtonElement>(null);
  const open = index !== null && index >= 0 && index < photoRefs.length;
  const attachmentId = open ? photoRefs[index] : null;

  // Give keyboard and screen-reader users a labelled entry point as soon as the
  // dialog opens; deferred so MUI's own focus sequence runs first.
  useEffect(() => {
    if (!open) return;
    const id = setTimeout(() => closeRef.current?.focus(), 50);
    return () => clearTimeout(id);
  }, [open]);

  const hasPrevious = open && index > 0;
  const hasNext = open && index < photoRefs.length - 1;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="diary-photo-lightbox-title"
      data-testid="diary-photo-lightbox"
    >
      <DialogTitle id="diary-photo-lightbox-title" sx={{ pr: 6 }}>
        {t('pages.plantDiary.photos.lightboxTitle', {
          index: open ? index + 1 : 0,
          total: photoRefs.length,
        })}
        <IconButton
          ref={closeRef}
          onClick={onClose}
          aria-label={t('common.close')}
          sx={{ position: 'absolute', right: 8, top: 8 }}
          data-testid="diary-photo-lightbox-close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton
            onClick={() => open && onNavigate(index - 1)}
            disabled={!hasPrevious}
            aria-label={t('pages.plantDiary.photos.previous')}
            data-testid="diary-photo-lightbox-prev"
            /* 44px minimum touch target (UI-NFR-001 R-008). */
            sx={{ minWidth: 44, minHeight: 44 }}
          >
            <NavigateBeforeIcon />
          </IconButton>
          {attachmentId && (
            <AuthImage
              uri={diaryPhotoUri(attachmentId, 1280)}
              alt={t('pages.plantDiary.photos.fullAlt')}
              objectFit="contain"
              height="auto"
              sx={{ flex: 1, maxHeight: { xs: '60vh', sm: '70vh' }, minWidth: 0 }}
              data-testid="diary-photo-lightbox-image"
            />
          )}
          <IconButton
            onClick={() => open && onNavigate(index + 1)}
            disabled={!hasNext}
            aria-label={t('pages.plantDiary.photos.next')}
            data-testid="diary-photo-lightbox-next"
            sx={{ minWidth: 44, minHeight: 44 }}
          >
            <NavigateNextIcon />
          </IconButton>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('pages.plantDiary.photos.renditionHint')}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 44 }} data-testid="diary-photo-lightbox-dismiss">
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
