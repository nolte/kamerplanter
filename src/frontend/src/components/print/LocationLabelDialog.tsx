/**
 * "Etikett drucken" for a bed (REQ-053 GP-FR-052, GP-UX-028): one PDF label with the bed's name, site, type, area and
 * a QR code that opens the bed in field mode. The server builds the label (`GET /print/location-label/{key}`, the
 * plant-label path of REQ-032); this dialog only chooses the QR size and downloads it.
 */
import { useCallback, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormLabel from '@mui/material/FormLabel';
import IconButton from '@mui/material/IconButton';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { useNotification } from '@/hooks/useNotification';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { downloadLocationLabelPdf } from '@/api/endpoints/print';

/** The QR sizes on offer (REQ-032 §2.7: at least 20 mm); 40 mm is the server's default for a bed label. */
export const QR_SIZES_MM = [25, 40, 60] as const;
type QrSizeMm = (typeof QR_SIZES_MM)[number];
const QR_SIZE_LABEL: Record<QrSizeMm, string> = {
  25: 'print.qrSizeSmall',
  40: 'print.qrSizeMedium',
  60: 'print.qrSizeLarge',
};
const DEFAULT_QR_SIZE: QrSizeMm = 40;

interface LocationLabelDialogProps {
  open: boolean;
  onClose: () => void;
  locationKey: string;
  /** Display name of the bed, used in the intro and the file name. */
  locationName: string;
}

/** A file name from the bed name: letters and digits kept, everything else one dash. */
function fileName(name: string, key: string): string {
  const slug = name
    .normalize('NFKD')
    // The decomposed accents go, the letters stay: "Süd" becomes "sud", not "su-d".
    .replace(/\p{M}+/gu, '')
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase();
  return `bed-label-${slug || key}.pdf`;
}

export function LocationLabelDialog({ open, onClose, locationKey, locationName }: LocationLabelDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const online = useOnlineStatus();
  const [qrSize, setQrSize] = useState<QrSizeMm>(DEFAULT_QR_SIZE);
  const [loading, setLoading] = useState(false);
  const titleId = useId();
  const descId = useId();
  const sizeGroupId = useId();

  const handleDownload = useCallback(async () => {
    setLoading(true);
    try {
      const blob = await downloadLocationLabelPdf(locationKey, qrSize);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = fileName(locationName, locationKey);
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
      notification.success(t('print.success'));
      onClose();
    } catch {
      notification.error(t('print.error'));
    } finally {
      setLoading(false);
    }
  }, [locationKey, locationName, qrSize, notification, t, onClose]);

  return (
    <Dialog
      open={open}
      onClose={loading ? undefined : onClose}
      maxWidth="xs"
      fullWidth
      fullScreen={fullScreen}
      aria-labelledby={titleId}
      aria-describedby={descId}
      data-testid="bed-view-label-dialog"
    >
      <DialogTitle id={titleId} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pr: 1 }}>
        {t('print.bedLabelTitle')}
        <IconButton
          onClick={onClose}
          aria-label={t('common.close')}
          disabled={loading}
          data-testid="bed-view-label-dialog-close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <DialogContentText id={descId} variant="body2">
          {t('print.bedLabelIntro', { name: locationName })}
        </DialogContentText>
        {!online && (
          <Alert severity="info" role="status" data-testid="bed-view-label-offline">
            {t('print.bedLabelOffline')}
          </Alert>
        )}
        <Box>
          <FormLabel id={sizeGroupId} sx={{ fontWeight: 600 }}>
            {t('print.qrSizeLabel')}
          </FormLabel>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            {t('print.qrSizeIntro')}
          </Typography>
          <RadioGroup
            value={String(qrSize)}
            onChange={(_, value) => setQrSize(Number(value) as QrSizeMm)}
            aria-labelledby={sizeGroupId}
            data-testid="bed-view-label-qr-size"
          >
            {QR_SIZES_MM.map((size) => (
              <FormControlLabel
                key={size}
                value={String(size)}
                control={<Radio data-testid={`bed-view-label-qr-size-${size}`} />}
                label={t(QR_SIZE_LABEL[size])}
              />
            ))}
          </RadioGroup>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 2, py: 1.5 }}>
        <Button onClick={onClose} disabled={loading} data-testid="bed-view-label-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleDownload}
          disabled={loading || !online}
          startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <PictureAsPdfIcon />}
          data-testid="bed-view-label-download"
        >
          {loading ? t('print.printing') : t('print.downloadPdf')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default LocationLabelDialog;
