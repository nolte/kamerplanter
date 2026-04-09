import { useCallback, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import NfcIcon from '@mui/icons-material/Nfc';
import QrCode2Icon from '@mui/icons-material/QrCode2';
import CheckIcon from '@mui/icons-material/Check';
import { QRCodeSVG } from 'qrcode.react';
import { useNotification } from '@/hooks/useNotification';

interface PlantTagDialogProps {
  open: boolean;
  onClose: () => void;
  plantKey: string;
  plantName: string;
}

const nfcSupported = typeof window !== 'undefined' && 'NDEFReader' in window;

export default function PlantTagDialog({ open, onClose, plantKey, plantName }: PlantTagDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const [tab, setTab] = useState(0);
  const [nfcWriting, setNfcWriting] = useState(false);
  const [nfcSuccess, setNfcSuccess] = useState(false);
  const [nfcError, setNfcError] = useState<string | null>(null);
  const qrRef = useRef<HTMLDivElement>(null);

  const plantUrl = useMemo(
    () => `${window.location.origin}/pflanzen/plant-instances/${plantKey}`,
    [plantKey],
  );

  const handleCopyUrl = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(plantUrl);
      notification.success(t('pages.plantInstances.tag.urlCopied'));
    } catch {
      notification.error(t('common.error'));
    }
  }, [plantUrl, notification, t]);

  const handleDownloadQr = useCallback(() => {
    const svgEl = qrRef.current?.querySelector('svg');
    if (!svgEl) return;

    const svgData = new XMLSerializer().serializeToString(svgEl);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);
      const link = document.createElement('a');
      link.download = `plant-${plantKey}-qr.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    };
    img.src = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgData)))}`;
  }, [plantKey]);

  const handleWriteNfc = useCallback(async () => {
    if (!nfcSupported) return;

    setNfcWriting(true);
    setNfcError(null);
    setNfcSuccess(false);

    try {
      const reader = new NDEFReader();
      await reader.write({
        records: [{ recordType: 'url', data: plantUrl }],
      });
      setNfcSuccess(true);
      notification.success(t('pages.plantInstances.tag.nfcSuccess'));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setNfcError(message);
    } finally {
      setNfcWriting(false);
    }
  }, [plantUrl, notification, t]);

  const handleClose = () => {
    setNfcWriting(false);
    setNfcSuccess(false);
    setNfcError(null);
    setTab(0);
    onClose();
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={handleClose} maxWidth="sm" fullWidth data-testid="plant-tag-dialog">
      <DialogTitle>{t('pages.plantInstances.tag.title')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plantInstances.tag.description', { name: plantName })}
        </Typography>

        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab icon={<QrCode2Icon />} label={t('pages.plantInstances.tag.qrTab')} data-testid="tag-tab-qr" />
          <Tab
            icon={<NfcIcon />}
            label={t('pages.plantInstances.tag.nfcTab')}
            disabled={!nfcSupported}
            data-testid="tag-tab-nfc"
          />
        </Tabs>

        {tab === 0 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <Box ref={qrRef} sx={{ p: 2, bgcolor: 'white', borderRadius: 1 }}>
              <QRCodeSVG value={plantUrl} size={200} level="M" />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <Typography
                variant="body2"
                sx={{
                  flex: 1,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                }}
              >
                {plantUrl}
              </Typography>
              <Tooltip title={t('pages.plantInstances.tag.copyUrl')}>
                <IconButton size="small" onClick={handleCopyUrl} data-testid="copy-url-button">
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>

            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadQr}
              data-testid="download-qr-button"
            >
              {t('pages.plantInstances.tag.downloadQr')}
            </Button>
          </Box>
        )}

        {tab === 1 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 2 }}>
            {!nfcSupported && (
              <Alert severity="warning">{t('pages.plantInstances.tag.nfcNotSupported')}</Alert>
            )}

            {nfcSupported && !nfcSuccess && !nfcError && (
              <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                {t('pages.plantInstances.tag.nfcInstructions')}
              </Typography>
            )}

            {nfcSuccess && (
              <Alert severity="success" icon={<CheckIcon />}>
                {t('pages.plantInstances.tag.nfcSuccess')}
              </Alert>
            )}

            {nfcError && (
              <Alert severity="error">{t('pages.plantInstances.tag.nfcError', { error: nfcError })}</Alert>
            )}

            <Button
              variant="contained"
              startIcon={nfcWriting ? <CircularProgress size={20} color="inherit" /> : <NfcIcon />}
              onClick={handleWriteNfc}
              disabled={nfcWriting || !nfcSupported}
              data-testid="write-nfc-button"
            >
              {nfcWriting
                ? t('pages.plantInstances.tag.nfcWriting')
                : t('pages.plantInstances.tag.nfcWrite')}
            </Button>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t('common.close')}</Button>
      </DialogActions>
    </Dialog>
  );
}
