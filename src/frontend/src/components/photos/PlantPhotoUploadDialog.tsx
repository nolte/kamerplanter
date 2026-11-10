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
import { uploadPlantPhoto } from '@/api/endpoints/plantPhotos';
import { isApiError } from '@/api/errors';

const GALLERY_NORMALIZE_OPTIONS = { maxEdge: GALLERY_MAX_EDGE, quality: GALLERY_JPEG_QUALITY };

/**
 * Where the photo goes: a plant's gallery (the default, `POST /plant-instances/{key}/photos`) or a caller's own
 * upload - the garden plan stores a bed photo as a `location` attachment and links it to the bed (REQ-053
 * GP-FR-051). An `upload` that throws shows the dialog's error; `errorMessage` may name a domain error first.
 */
type UploadTarget =
  | { plantInstanceKey: string; upload?: never }
  | { upload: (file: File) => Promise<unknown>; plantInstanceKey?: never };

type PlantPhotoUploadDialogProps = UploadTarget & {
  open: boolean;
  onClose: () => void;
  /** Dialog title; defaults to the plant-photo title. */
  title?: string;
  /** Maps a failed upload to a message before the generic ones (quota, size, forbidden); `null` falls through. */
  errorMessage?: (error: unknown) => string | null;
  /** Called after a successful upload so the gallery can refresh. */
  onUploaded: () => void;
  /**
   * Minimum edge in px of the dialog's buttons (close, retake, cancel, upload); the garden plan's field
   * mode passes the kiosk target (64 px, REQ-053 GP-UX-020). Unset keeps the regular sizes.
   */
  touchTarget?: number;
  /** The identification photo tips of the capture panel; a bed photo turns them off (#2764). Default on. */
  photoTips?: boolean;
};

/**
 * REQ-034 §2.2 — gallery photo upload. Reuses the recognition capture UX
 * (webcam / smartphone rear camera / file upload, {@link ImageCapturePanel})
 * but normalizes to a higher gallery resolution. The selected image is shown as
 * a preview before the user confirms the upload.
 *
 * A11y (UI-NFR-002 / UI-NFR-008):
 * - fullScreen on xs/sm for maximum capture-panel space on phones.
 * - Confirm button receives focus when a file is ready so Enter submits.
 * - Error Alert uses role="alert" (via MUI severity="error") so screen readers
 *   announce it without the user having to navigate there.
 * - Upload hint is shown BEFORE file selection so users know what to expect.
 */
export default function PlantPhotoUploadDialog({
  open,
  plantInstanceKey,
  upload,
  onClose,
  onUploaded,
  touchTarget,
  title,
  errorMessage,
  photoTips = true,
}: PlantPhotoUploadDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  // Full-screen on phones — the capture panel needs the full viewport (mobile-first).
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { level } = useExpertiseLevel();

  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ref to the confirm button so we can focus it once a preview is ready
  // (UI-NFR-008 R-010: autofocus on the primary action when file is ready).
  const confirmRef = useRef<HTMLButtonElement>(null);
  const targetSx = touchTarget ? { minHeight: touchTarget, minWidth: touchTarget } : {};

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
    // Defer focus to after the confirm button renders
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
      if (upload) await upload(file);
      else if (plantInstanceKey) await uploadPlantPhoto(plantInstanceKey, file);
      onUploaded();
      onClose();
    } catch (err) {
      const specific = errorMessage?.(err) ?? null;
      if (specific) {
        setError(specific);
      } else if (isApiError(err) && (err.errorCode === 'PHOTO_QUOTA_EXCEEDED' || err.statusCode === 409)) {
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
  }, [file, plantInstanceKey, upload, errorMessage, onUploaded, onClose, t]);

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
      <DialogTitle id="plant-photo-upload-title" sx={{ pr: touchTarget ? 10 : 6, overflowWrap: 'anywhere' }}>
        {title ?? t('pages.plantPhotos.uploadTitle')}
        <IconButton
          onClick={onClose}
          disabled={uploading}
          aria-label={t('common.close')}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            ...(touchTarget ? { width: touchTarget, height: touchTarget } : {}),
          }}
          data-testid="plant-photo-upload-close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>
        {/* Upload hint — shown BEFORE the capture panel so users know what
            to expect (not hidden after file selection). */}
        {!file && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 2 }}
            data-testid="plant-photo-upload-hint"
          >
            {t('pages.plantPhotos.uploadHint')}
          </Typography>
        )}

        {!file ? (
          <ImageCapturePanel
            onImageReady={handleImageReady}
            level={level}
            disabled={uploading}
            normalizeOptions={GALLERY_NORMALIZE_OPTIONS}
            photoTips={photoTips}
          />
        ) : (
          <Box sx={{ textAlign: 'center' }}>
            <Box
              component="img"
              src={previewUrl ?? undefined}
              alt={t('pages.plantPhotos.previewAlt')}
              sx={{
                maxWidth: '100%',
                maxHeight: { xs: 240, sm: 360 },
                borderRadius: 1,
                objectFit: 'contain',
                bgcolor: 'action.hover',
                display: 'block',
                mx: 'auto',
              }}
              data-testid="plant-photo-upload-preview"
            />
            {/* Contextual guidance when preview is shown (UI-NFR-008 R-038) */}
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {t('pages.plantPhotos.previewHint')}
            </Typography>
            <Box sx={{ mt: 1.5 }}>
              <Button
                startIcon={<ReplayIcon />}
                onClick={handleRetake}
                disabled={uploading}
                sx={targetSx}
                data-testid="plant-photo-upload-retake"
              >
                {t('pages.plantPhotos.retake')}
              </Button>
            </Box>
          </Box>
        )}

        {/* Error feedback — always rendered last so it does not displace
            the capture panel (UI-NFR-004: error stays visible on retry). */}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="plant-photo-upload-error">
            {error}
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 2, py: 1.5, gap: 1 }}>
        <Button
          onClick={onClose}
          disabled={uploading}
          sx={targetSx}
          data-testid="plant-photo-upload-cancel"
        >
          {t('common.cancel')}
        </Button>
        <Button
          ref={confirmRef}
          variant="contained"
          onClick={handleUpload}
          disabled={!file || uploading}
          startIcon={
            uploading ? (
              <CircularProgress size={16} color="inherit" />
            ) : (
              <CloudUploadIcon />
            )
          }
          /* Minimum 44px touch target on mobile (UI-NFR-001 R-008) */
          sx={{ minHeight: 44, ...targetSx }}
          data-testid="plant-photo-upload-confirm"
        >
          {uploading ? t('pages.plantPhotos.uploading') : t('pages.plantPhotos.upload')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
