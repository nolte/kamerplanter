import { useCallback, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ImageCapturePanel from '@/components/identification/ImageCapturePanel';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useNotification } from '@/hooks/useNotification';
import { isLightMode } from '@/config/mode';
import { contributePestImage } from '@/api/endpoints/ipm';

interface PestImageContributeDialogProps {
  open: boolean;
  onClose: () => void;
  pestKey: string;
  /** Called after a successful upload so the parent can refresh the gallery. */
  onUploaded: () => void;
}

/**
 * REQ-010 — let a user contribute an own photo for a pest (upload or camera).
 *
 * Reuses {@link ImageCapturePanel} (webcam / phone camera / file + drag&drop,
 * client-side EXIF strip). The image is uploaded tenant-scoped via the
 * AttachmentService (server-side EXIF strip, virus scan, dedup) and appears
 * privately in the pest's gallery. Blocked in light mode (no tenant).
 */
export default function PestImageContributeDialog({
  open,
  onClose,
  pestKey,
  onUploaded,
}: PestImageContributeDialogProps) {
  const { t } = useTranslation();
  const { level } = useExpertiseLevel();
  const notification = useNotification();
  const theme = useTheme();
  // Full-screen on mobile so the camera panel has enough vertical space (UI-NFR-001 R-011).
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [caption, setCaption] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const titleId = useId();

  const handleClose = useCallback(() => {
    if (uploading) return;
    setError(null);
    setCaption('');
    onClose();
  }, [uploading, onClose]);

  const handleImageReady = useCallback(
    async (file: File) => {
      setUploading(true);
      setError(null);
      try {
        await contributePestImage(pestKey, file, caption.trim() || undefined);
        notification.success(t('pages.pestDetail.contributeSuccess'));
        onUploaded();
        setCaption('');
        onClose();
      } catch {
        setError(t('pages.pestDetail.contributeError'));
      } finally {
        setUploading(false);
      }
    },
    [pestKey, caption, onUploaded, onClose, t, notification],
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      fullScreen={fullScreen}
      aria-labelledby={titleId}
      data-testid="pest-contribute-dialog"
    >
      <DialogTitle id={titleId}>{t('pages.pestDetail.contributeTitle')}</DialogTitle>
      <DialogContent dividers>
        {isLightMode ? (
          <Alert severity="info" data-testid="pest-contribute-light">
            {t('pages.pestDetail.contributeLightBlocked')}
          </Alert>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.pestDetail.contributeIntro')}
            </Typography>
            <TextField
              fullWidth
              size="small"
              label={t('pages.pestDetail.captionLabel')}
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              disabled={uploading}
              slotProps={{ htmlInput: { maxLength: 500 } }}
              sx={{ mb: 2 }}
              data-testid="pest-contribute-caption"
              autoFocus
            />
            {uploading ? (
              <Box sx={{ textAlign: 'center', py: 3 }} aria-live="polite" aria-busy="true">
                <CircularProgress aria-hidden="true" />
                <Typography sx={{ mt: 2 }}>{t('pages.pestDetail.contributeUploading')}</Typography>
              </Box>
            ) : (
              <ImageCapturePanel onImageReady={handleImageReady} level={level} disabled={uploading} />
            )}
            {error && (
              <Alert severity="error" sx={{ mt: 2 }} role="alert" data-testid="pest-contribute-error">
                {error}
              </Alert>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={uploading} sx={{ minHeight: 44 }}>
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
