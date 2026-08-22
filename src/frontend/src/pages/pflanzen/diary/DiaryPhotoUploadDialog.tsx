import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';
import ReplayIcon from '@mui/icons-material/Replay';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ImageCapturePanel from '@/components/identification/ImageCapturePanel';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { GALLERY_MAX_EDGE, GALLERY_JPEG_QUALITY } from '@/utils/imageNormalization';
import { uploadDiaryPhoto } from '@/api/endpoints/diary';
import { isApiError } from '@/api/errors';

/** Same normalisation profile the gallery upload uses (REQ-034 §2.2). */
const DIARY_NORMALIZE_OPTIONS = { maxEdge: GALLERY_MAX_EDGE, quality: GALLERY_JPEG_QUALITY };

interface DiaryPhotoUploadDialogProps {
  open: boolean;
  onClose: () => void;
  /** Called with the fresh attachment id once the upload succeeded. */
  onUploaded: (attachmentId: string) => void;
}

/**
 * REQ-051 §6.1 — attach a photo to a diary entry.
 *
 * The three capture paths of REQ-034 §2.2 (webcam, phone rear camera, file
 * upload) come from {@link ImageCapturePanel}, the same component the gallery
 * upload uses — that part is genuinely shared, not re-implemented.
 *
 * **`PlantPhotoUploadDialog` itself is not reusable here.** It calls
 * `uploadPlantPhoto` (`plantPhotos.ts:118`), which posts to
 * `/plant-instances/{key}/photos`; that endpoint stores the file as
 * `AttachmentCategory.PLANT` and links it into the plant's gallery
 * (`photo_router.py:152`). A diary photo is neither: REQ-050 §0 pins it to
 * `category = diary`, which is what the DSGVO erasure scope and the
 * `STORAGE_KEEP_EXIF_DIARY` setting key off. Reusing the gallery dialog would
 * have silently filed every diary photo into the gallery under the wrong
 * category. So the capture UX is shared and the destination is not.
 */
export default function DiaryPhotoUploadDialog({
  open,
  onClose,
  onUploaded,
}: DiaryPhotoUploadDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  // Full-screen on phones — the capture panel needs the whole viewport.
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { level } = useExpertiseLevel();

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);

  // Reset on close and revoke the preview URL, so no blob reference leaks.
  useEffect(() => {
    if (!open) return;
    return () => {
      setFile(null);
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      setUploading(false);
      setError(null);
    };
  }, [open]);

  const handleImageReady = useCallback((selected: File, url: string) => {
    setError(null);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });
    setFile(selected);
    setTimeout(() => confirmRef.current?.focus(), 50);
  }, []);

  const handleRetake = useCallback(() => {
    setError(null);
    setFile(null);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const uploaded = await uploadDiaryPhoto(file);
      onUploaded(uploaded.attachment_id);
      onClose();
    } catch (err) {
      if (isApiError(err) && err.statusCode === 413) {
        setError(t('pages.plantDiary.photos.fileTooLarge'));
      } else if (isApiError(err) && err.statusCode === 403) {
        setError(t('pages.plantDiary.photos.uploadForbidden'));
      } else {
        setError(t('pages.plantDiary.photos.uploadError'));
      }
      setUploading(false);
    }
  }, [file, onUploaded, onClose, t]);

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={uploading ? undefined : onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="diary-photo-upload-title"
      data-testid="diary-photo-upload-dialog"
    >
      <DialogTitle id="diary-photo-upload-title" sx={{ pr: 6 }}>
        {t('pages.plantDiary.photos.uploadTitle')}
        <IconButton
          onClick={onClose}
          disabled={uploading}
          aria-label={t('common.close')}
          sx={{ position: 'absolute', right: 8, top: 8 }}
          data-testid="diary-photo-upload-close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {!file && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 2 }}
            data-testid="diary-photo-upload-hint"
          >
            {t('pages.plantDiary.photos.uploadHint')}
          </Typography>
        )}

        {!file ? (
          <ImageCapturePanel
            onImageReady={handleImageReady}
            level={level}
            disabled={uploading}
            normalizeOptions={DIARY_NORMALIZE_OPTIONS}
          />
        ) : (
          <Box sx={{ textAlign: 'center' }}>
            <Box
              component="img"
              src={previewUrl ?? undefined}
              alt={t('pages.plantDiary.photos.previewAlt')}
              sx={{
                maxWidth: '100%',
                maxHeight: { xs: 240, sm: 360 },
                borderRadius: 1,
                objectFit: 'contain',
                bgcolor: 'action.hover',
                display: 'block',
                mx: 'auto',
              }}
              data-testid="diary-photo-upload-preview"
            />
            <Box sx={{ mt: 1.5 }}>
              <Button
                startIcon={<ReplayIcon />}
                onClick={handleRetake}
                disabled={uploading}
                sx={{ minHeight: 44 }}
                data-testid="diary-photo-upload-retake"
              >
                {t('pages.plantDiary.photos.retake')}
              </Button>
            </Box>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="diary-photo-upload-error">
            {error}
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 2, py: 1.5, gap: 1 }}>
        <Button onClick={onClose} disabled={uploading} data-testid="diary-photo-upload-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          ref={confirmRef}
          variant="contained"
          onClick={handleUpload}
          disabled={!file || uploading}
          startIcon={uploading ? <CircularProgress size={16} color="inherit" /> : <CloudUploadIcon />}
          sx={{ minHeight: 44 }}
          data-testid="diary-photo-upload-confirm"
        >
          {uploading
            ? t('pages.plantDiary.photos.uploading')
            : t('pages.plantDiary.photos.upload')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
