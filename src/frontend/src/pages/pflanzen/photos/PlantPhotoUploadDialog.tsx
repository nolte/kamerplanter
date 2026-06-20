import { useCallback, useEffect, useState } from 'react';
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
import ImageCapturePanel from '@/components/identification/ImageCapturePanel';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { GALLERY_MAX_EDGE, GALLERY_JPEG_QUALITY } from '@/utils/imageNormalization';
import { uploadPlantPhoto } from '@/api/endpoints/plantPhotos';
import { isApiError } from '@/api/errors';

const GALLERY_NORMALIZE_OPTIONS = { maxEdge: GALLERY_MAX_EDGE, quality: GALLERY_JPEG_QUALITY };

interface PlantPhotoUploadDialogProps {
  open: boolean;
  plantInstanceKey: string;
  onClose: () => void;
  /** Called after a successful upload so the gallery can refresh. */
  onUploaded: () => void;
}

/**
 * REQ-034 §2.2 — gallery photo upload. Reuses the recognition capture UX
 * (webcam / smartphone rear camera / file upload, {@link ImageCapturePanel})
 * but normalizes to a higher gallery resolution. The selected image is shown as
 * a preview before the user confirms the upload.
 */
export default function PlantPhotoUploadDialog({
  open,
  plantInstanceKey,
  onClose,
  onUploaded,
}: PlantPhotoUploadDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { level } = useExpertiseLevel();

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset all state and revoke any preview URL when the dialog closes/unmounts
  // (effect cleanup runs on close, avoiding a synchronous setState in the body).
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
      await uploadPlantPhoto(plantInstanceKey, file);
      onUploaded();
      onClose();
    } catch (err) {
      if (isApiError(err) && (err.errorCode === 'PHOTO_QUOTA_EXCEEDED' || err.statusCode === 409)) {
        setError(t('pages.plantPhotos.quotaExceeded'));
      } else if (isApiError(err) && err.statusCode === 413) {
        setError(t('pages.plantPhotos.fileTooLarge'));
      } else if (isApiError(err) && err.statusCode === 403) {
        setError(t('pages.plantPhotos.uploadForbidden'));
      } else {
        setError(t('pages.plantPhotos.uploadError'));
      }
      setUploading(false);
    }
  }, [file, plantInstanceKey, onUploaded, onClose, t]);

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={uploading ? undefined : onClose}
      maxWidth="sm"
      fullWidth
      data-testid="plant-photo-upload-dialog"
      aria-labelledby="plant-photo-upload-title"
    >
      <DialogTitle id="plant-photo-upload-title" sx={{ pr: 6 }}>
        {t('pages.plantPhotos.uploadTitle')}
        <IconButton
          onClick={onClose}
          disabled={uploading}
          aria-label={t('common.close')}
          sx={{ position: 'absolute', right: 8, top: 8 }}
          data-testid="plant-photo-upload-close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        {!file ? (
          <ImageCapturePanel
            onImageReady={handleImageReady}
            level={level}
            disabled={uploading}
            normalizeOptions={GALLERY_NORMALIZE_OPTIONS}
          />
        ) : (
          <Box sx={{ textAlign: 'center' }}>
            <Box
              component="img"
              src={previewUrl ?? undefined}
              alt={t('pages.plantPhotos.previewAlt')}
              sx={{
                maxWidth: '100%',
                maxHeight: 360,
                borderRadius: 1,
                objectFit: 'contain',
                bgcolor: 'action.hover',
              }}
              data-testid="plant-photo-upload-preview"
            />
            <Box sx={{ mt: 1 }}>
              <Button
                startIcon={<ReplayIcon />}
                onClick={handleRetake}
                disabled={uploading}
                data-testid="plant-photo-upload-retake"
              >
                {t('pages.plantPhotos.retake')}
              </Button>
            </Box>
          </Box>
        )}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="plant-photo-upload-error">
            {error}
          </Alert>
        )}
        {!file && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            {t('pages.plantPhotos.uploadHint')}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={uploading} data-testid="plant-photo-upload-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!file || uploading}
          startIcon={uploading ? <CircularProgress size={16} color="inherit" /> : undefined}
          data-testid="plant-photo-upload-confirm"
        >
          {t('pages.plantPhotos.upload')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
