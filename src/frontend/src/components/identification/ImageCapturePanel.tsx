import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Tooltip from '@mui/material/Tooltip';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import CloseIcon from '@mui/icons-material/Close';
import { useWebcamCapture } from '@/hooks/useWebcamCapture';
import { normalizeImage } from '@/utils/imageNormalization';
import type { ExperienceLevel } from '@/api/types';

interface ImageCapturePanelProps {
  /**
   * Called with the normalized (downscaled, EXIF-stripped JPEG) file and a
   * preview object URL once the user has captured/selected an image.
   */
  onImageReady: (file: File, previewUrl: string) => void;
  disabled?: boolean;
  /** Beginner gets a single prominent CTA; intermediate/expert see all paths. */
  level: ExperienceLevel;
}

/**
 * REQ-029 §4.1 / REQ-029-A §0.1.1 point 4 — three capture paths:
 *  (a) live webcam via getUserMedia (desktop/kiosk),
 *  (b) smartphone rear camera via <input capture="environment">,
 *  (c) file upload with drag & drop (desktop).
 *
 * All images are normalized client-side before they leave the component.
 *
 * Usability improvements over v1:
 * - Touch targets enforce minHeight 56px on mobile (UI-NFR-001 R-011)
 * - Photo-tips section helps casual users get better results
 * - aria-live region announces processing state to screen readers (UI-NFR-002 R-011)
 * - Dropzone hints include accepted formats (UI-NFR-008)
 * - Webcam cancel button has minimum touch target
 * - Webcam hint tooltip steers desktop vs. mobile usage
 */
export default function ImageCapturePanel({
  onImageReady,
  disabled = false,
  level,
}: ImageCapturePanelProps) {
  const { t } = useTranslation();
  const videoRef = useRef<HTMLVideoElement>(null);
  const webcam = useWebcamCapture(videoRef);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [processing, setProcessing] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File | null | undefined) => {
      if (!file) return;
      setLocalError(null);
      setProcessing(true);
      try {
        const { file: normalized, previewUrl } = await normalizeImage(file);
        onImageReady(normalized, previewUrl);
      } catch {
        setLocalError(t('pages.plantIdentification.unsupportedFormat'));
      } finally {
        setProcessing(false);
      }
    },
    [onImageReady, t],
  );

  const handleWebcamShot = useCallback(async () => {
    setProcessing(true);
    try {
      const shot = await webcam.capture();
      if (shot) {
        const { file, previewUrl } = await normalizeImage(shot);
        webcam.stop();
        onImageReady(file, previewUrl);
      }
    } catch {
      setLocalError(t('pages.plantIdentification.unsupportedFormat'));
    } finally {
      setProcessing(false);
    }
  }, [webcam, onImageReady, t]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (disabled) return;
      handleFile(e.dataTransfer.files?.[0]);
    },
    [disabled, handleFile],
  );

  // Stop the webcam if the panel is disabled mid-stream (e.g. dialog closing).
  useEffect(() => {
    if (disabled && webcam.isActive) webcam.stop();
  }, [disabled, webcam]);

  const webcamErrorKey = webcam.error
    ? `pages.plantIdentification.webcam.${webcam.error}`
    : null;

  return (
    <Box data-testid="image-capture-panel">
      {/* aria-live region: announces processing state to screen readers (UI-NFR-002 R-011).
          clipPath replaces the deprecated clip property. */}
      <Box
        aria-live="polite"
        aria-atomic="true"
        sx={{
          position: 'absolute',
          width: 1,
          height: 1,
          overflow: 'hidden',
          clipPath: 'inset(50%)',
          whiteSpace: 'nowrap',
        }}
      >
        {processing ? t('pages.plantIdentification.processingImage') : ''}
      </Box>

      {/* Live webcam preview when active */}
      {webcam.isActive && (
        <Box sx={{ mb: 2 }}>
          {/* webcam-preview-hint is the visually hidden description for the video
              element — screen readers announce it via aria-describedby so the user
              understands what the live feed is showing (UI-NFR-002 R-012). */}
          <span
            id="webcam-preview-hint"
            style={{
              position: 'absolute',
              width: 1,
              height: 1,
              overflow: 'hidden',
              clipPath: 'inset(50%)',
              whiteSpace: 'nowrap',
            }}
          >
            {t('pages.plantIdentification.webcam.livePreviewHint')}
          </span>
          <Box
            component="video"
            ref={videoRef}
            autoPlay
            playsInline
            muted
            aria-label={t('pages.plantIdentification.webcam.livePreview')}
            aria-describedby="webcam-preview-hint"
            sx={{
              width: '100%',
              maxHeight: 360,
              borderRadius: 1,
              bgcolor: 'common.black',
              objectFit: 'contain',
            }}
            data-testid="webcam-preview"
          />
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <Button
              variant="contained"
              startIcon={<PhotoCameraIcon />}
              onClick={handleWebcamShot}
              disabled={disabled || processing}
              fullWidth
              data-testid="webcam-shoot"
              sx={{ minHeight: { xs: 56, sm: 44 } }}
            >
              {t('pages.plantIdentification.webcam.shoot')}
            </Button>
            <Button
              variant="outlined"
              color="inherit"
              startIcon={<CloseIcon />}
              onClick={webcam.stop}
              data-testid="webcam-cancel"
              aria-label={t('common.cancel')}
              sx={{ minHeight: { xs: 56, sm: 44 }, minWidth: { xs: 56, sm: 'auto' } }}
            >
              {t('common.cancel')}
            </Button>
          </Stack>
        </Box>
      )}

      {!webcam.isActive && (
        <>
          {/* Drop zone doubles as the primary file picker */}
          <Box
            onDragOver={(e) => {
              e.preventDefault();
              if (!disabled) setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => !disabled && fileInputRef.current?.click()}
            role="button"
            tabIndex={disabled ? -1 : 0}
            aria-label={t('pages.plantIdentification.uploadPhoto')}
            aria-disabled={disabled}
            onKeyDown={(e) => {
              if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
                e.preventDefault();
                fileInputRef.current?.click();
              }
            }}
            data-testid="capture-dropzone"
            sx={{
              border: '2px dashed',
              borderColor: dragActive ? 'primary.main' : 'divider',
              borderRadius: 2,
              p: { xs: 3, sm: 4 },
              textAlign: 'center',
              cursor: disabled ? 'default' : 'pointer',
              bgcolor: dragActive ? 'action.hover' : 'transparent',
              transition: 'background-color 0.15s, border-color 0.15s',
              opacity: disabled ? 0.6 : 1,
              minHeight: { xs: 100, sm: 120 },
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {processing ? (
              <CircularProgress size={28} data-testid="capture-processing" />
            ) : (
              <>
                <UploadFileIcon color="action" sx={{ fontSize: { xs: 40, sm: 36 }, mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  {t('pages.plantIdentification.dropzoneHint')}
                </Typography>
                <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5 }}>
                  {t('pages.plantIdentification.dropzoneHintFormats')}
                </Typography>
              </>
            )}
          </Box>

          {/* Photo tips (beginner only — keep advanced users uncluttered) */}
          {level === 'beginner' && (
            <Box
              sx={{
                mt: 1.5,
                p: 1.5,
                borderRadius: 1,
                bgcolor: 'action.hover',
              }}
            >
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                {t('pages.plantIdentification.photoTipTitle')}
              </Typography>
              <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2 }}>
                {(['photoTip1', 'photoTip2', 'photoTip3'] as const).map((key) => (
                  <Typography
                    key={key}
                    component="li"
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'list-item' }}
                  >
                    {t(`pages.plantIdentification.${key}`)}
                  </Typography>
                ))}
              </Box>
            </Box>
          )}

          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            useFlexGap
            sx={{ mt: 2, flexWrap: 'wrap' }}
          >
            {/* (b) Smartphone rear camera — always offered (mobile-first primary CTA) */}
            <Button
              component="label"
              variant={level === 'beginner' ? 'contained' : 'outlined'}
              startIcon={<PhotoCameraIcon />}
              disabled={disabled || processing}
              fullWidth
              data-testid="capture-mobile-camera"
              sx={{ minHeight: { xs: 56, sm: 44 } }}
            >
              {t('pages.plantIdentification.takePhoto')}
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                hidden
                onChange={(e) => handleFile(e.target.files?.[0])}
                data-testid="capture-camera-input"
              />
            </Button>

            {/* (a) Desktop webcam — only when supported; tooltip steers mobile users away */}
            {webcam.isSupported && (
              <Tooltip title={t('pages.plantIdentification.webcamHint')} placement="top">
                <span style={{ display: 'contents' }}>
                  <Button
                    variant="outlined"
                    startIcon={<CameraAltIcon />}
                    onClick={webcam.start}
                    disabled={disabled || processing || webcam.isStarting}
                    fullWidth
                    data-testid="capture-webcam-start"
                    sx={{ minHeight: { xs: 56, sm: 44 } }}
                  >
                    {t('pages.plantIdentification.webcam.start')}
                  </Button>
                </span>
              </Tooltip>
            )}

            {/* (c) Explicit file upload button */}
            <Button
              component="label"
              variant="outlined"
              startIcon={<UploadFileIcon />}
              disabled={disabled || processing}
              fullWidth
              data-testid="capture-upload"
              sx={{ minHeight: { xs: 56, sm: 44 } }}
            >
              {t('pages.plantIdentification.uploadPhoto')}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                hidden
                onChange={(e) => handleFile(e.target.files?.[0])}
                data-testid="capture-file-input"
              />
            </Button>
          </Stack>
        </>
      )}

      {webcamErrorKey && (
        <Alert severity="warning" sx={{ mt: 2 }} data-testid="webcam-error">
          {t(webcamErrorKey)}
        </Alert>
      )}
      {localError && (
        <Alert severity="error" sx={{ mt: 2 }} data-testid="capture-error">
          {localError}
        </Alert>
      )}
    </Box>
  );
}
