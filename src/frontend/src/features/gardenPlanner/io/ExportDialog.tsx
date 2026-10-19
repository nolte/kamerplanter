/**
 * The export dialog of the garden plan (REQ-053 GP-UX-050): format, paper, scale, layers, a preview, progress and
 * the reason when it fails. On a phone only the JSON backup and the PDF with their standard options are offered.
 * Lazy: the route chunk stays inside its budget (UI-NFR-003).
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import FormLabel from '@mui/material/FormLabel';
import MenuItem from '@mui/material/MenuItem';
import Skeleton from '@mui/material/Skeleton';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { describeExportFailure, fetchPlanExport, saveBlob } from './ioApi';
import { usePlanPreview } from './usePlanPreview';
import {
  DEFAULT_EXPORT_OPTIONS,
  EXPORT_LAYERS,
  EXPORT_SCALES,
  type ExportFormat,
  type ExportLayer,
  type ExportOptions,
  type ExportOrientation,
  type ExportPaper,
  type ExportScale,
} from './types';

const PREFIX = 'pages.gardenPlan.io.export';

interface ExportDialogProps {
  open: boolean;
  siteKey: string;
  onClose: () => void;
}

function errorKey(code: string | null, status: number | null): string {
  if (code === 'plan.empty') return 'empty';
  if (code === 'plan.does_not_fit') return 'doesNotFit';
  if (status === 429) return 'rateLimited';
  if (status === 403) return 'forbidden';
  return 'failed';
}

function formatSize(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function ExportDialog({ open, siteKey, onClose }: ExportDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const phone = useMediaQuery(theme.breakpoints.down('sm'));
  const [options, setOptions] = useState<ExportOptions>(DEFAULT_EXPORT_OPTIONS);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  // On a phone the standard options apply and SVG is not offered (GP-UX-050).
  const effective: ExportOptions = phone
    ? { ...DEFAULT_EXPORT_OPTIONS, format: options.format === 'json' ? 'json' : 'pdf' }
    : options;
  const preview = usePlanPreview(siteKey, effective, open);
  const patch = (change: Partial<ExportOptions>) => {
    setFailure(null);
    setOptions((previous) => ({ ...previous, ...change }));
  };
  const toggleLayer = (layer: ExportLayer) =>
    patch({
      layers: effective.layers.includes(layer)
        ? effective.layers.filter((entry) => entry !== layer)
        : EXPORT_LAYERS.filter((entry) => entry === layer || effective.layers.includes(entry)),
    });

  const download = async () => {
    setBusy(true);
    setFailure(null);
    try {
      const file = await fetchPlanExport(siteKey, effective);
      saveBlob(file.blob, file.filename);
      onClose();
    } catch (error) {
      const reason = await describeExportFailure(error);
      setFailure(errorKey(reason.code, reason.status));
    } finally {
      setBusy(false);
    }
  };

  const shownError =
    failure ?? (preview.status === 'error' ? errorKey(preview.code, preview.httpStatus) : null);
  const scaled = effective.format !== 'json';

  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onClose}
      fullScreen={phone}
      maxWidth="md"
      fullWidth
      aria-labelledby="plan-export-title"
      data-testid="plan-export-dialog"
    >
      <DialogTitle id="plan-export-title">{t(`${PREFIX}.title`)}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <FormControl>
          <FormLabel id="plan-export-format-label">{t(`${PREFIX}.format`)}</FormLabel>
          <ToggleButtonGroup
            exclusive
            fullWidth
            value={effective.format}
            onChange={(_, value: ExportFormat | null) => value && patch({ format: value })}
            aria-labelledby="plan-export-format-label"
            sx={{ mt: 0.5 }}
          >
            <ToggleButton value="pdf" sx={{ minHeight: 48 }} data-testid="plan-export-format-pdf">
              {t(`${PREFIX}.formats.pdf`)}
            </ToggleButton>
            {!phone && (
              <ToggleButton value="svg" sx={{ minHeight: 48 }} data-testid="plan-export-format-svg">
                {t(`${PREFIX}.formats.svg`)}
              </ToggleButton>
            )}
            <ToggleButton value="json" sx={{ minHeight: 48 }} data-testid="plan-export-format-json">
              {t(`${PREFIX}.formats.json`)}
            </ToggleButton>
          </ToggleButtonGroup>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {t(`${PREFIX}.formatHints.${effective.format}`)}
          </Typography>
        </FormControl>

        {scaled && !phone && (
          <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' } }}>
            <TextField
              select
              label={t(`${PREFIX}.paper`)}
              value={effective.paper}
              onChange={(event) => patch({ paper: event.target.value as ExportPaper })}
              slotProps={{ htmlInput: { 'data-testid': 'plan-export-paper' } }}
            >
              <MenuItem value="a4">A4</MenuItem>
              <MenuItem value="a3">A3</MenuItem>
            </TextField>
            <TextField
              select
              label={t(`${PREFIX}.orientation`)}
              value={effective.orientation}
              onChange={(event) => patch({ orientation: event.target.value as ExportOrientation })}
              slotProps={{ htmlInput: { 'data-testid': 'plan-export-orientation' } }}
            >
              <MenuItem value="landscape">{t(`${PREFIX}.orientations.landscape`)}</MenuItem>
              <MenuItem value="portrait">{t(`${PREFIX}.orientations.portrait`)}</MenuItem>
            </TextField>
            <TextField
              select
              label={t(`${PREFIX}.scale`)}
              value={effective.scale}
              onChange={(event) => patch({ scale: event.target.value as ExportScale })}
              helperText={
                effective.scale === 'auto' && preview.status === 'svg' && preview.scale
                  ? t(`${PREFIX}.scaleChosen`, { scale: preview.scale })
                  : t(`${PREFIX}.scaleHelp`)
              }
              slotProps={{ htmlInput: { 'data-testid': 'plan-export-scale' } }}
            >
              {EXPORT_SCALES.map((scale) => (
                <MenuItem key={scale} value={scale}>
                  {scale === 'auto' ? t(`${PREFIX}.scaleAuto`) : scale}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        )}

        {scaled && !phone && (
          <FormControl component="fieldset" variant="standard">
            <FormLabel component="legend">{t(`${PREFIX}.layers`)}</FormLabel>
            <FormGroup row>
              {EXPORT_LAYERS.map((layer) => (
                <FormControlLabel
                  key={layer}
                  control={
                    <Checkbox
                      checked={effective.layers.includes(layer)}
                      onChange={() => toggleLayer(layer)}
                      slotProps={{ input: { 'data-testid': `plan-export-layer-${layer}` } as object }}
                    />
                  }
                  label={t(`${PREFIX}.layerNames.${layer}`)}
                  sx={{ minHeight: 44 }}
                />
              ))}
              {effective.format === 'pdf' && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={effective.bedList}
                      onChange={(event) => patch({ bedList: event.target.checked })}
                      slotProps={{ input: { 'data-testid': 'plan-export-bed-list' } as object }}
                    />
                  }
                  label={t(`${PREFIX}.bedList`)}
                  sx={{ minHeight: 44 }}
                />
              )}
            </FormGroup>
          </FormControl>
        )}

        {phone && effective.format !== 'json' && (
          <Typography variant="body2" color="text.secondary" data-testid="plan-export-phone-note">
            {t(`${PREFIX}.phoneNote`)}
          </Typography>
        )}

        <Typography variant="caption" color="text.secondary">
          {t(`${PREFIX}.privacy`)}
        </Typography>

        {shownError !== null && (
          <Alert severity="warning" data-testid="plan-export-error">
            {t(`${PREFIX}.errors.${shownError}`)}
          </Alert>
        )}
        {preview.status === 'svg' && preview.suggestA3 && effective.paper === 'a4' && (
          <Alert severity="info" data-testid="plan-export-suggest-a3">
            {t(`${PREFIX}.suggestA3`)}
          </Alert>
        )}

        <Box
          sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 1, minHeight: 160 }}
          data-testid="plan-export-preview"
          role="group"
          aria-label={t(`${PREFIX}.preview`)}
          aria-busy={preview.status === 'loading' || preview.status === 'idle'}
        >
          <Typography variant="subtitle2" component="h3" sx={{ mb: 1 }}>
            {t(`${PREFIX}.preview`)}
          </Typography>
          {(preview.status === 'loading' || preview.status === 'idle') && (
            <Skeleton
              variant="rectangular"
              height={140}
              role="status"
              aria-label={t(`${PREFIX}.previewLoading`)}
            />
          )}
          {preview.status === 'svg' && (
            <Box
              component="img"
              src={preview.url}
              alt={t(`${PREFIX}.previewAlt`, { scale: preview.scale ?? '' })}
              sx={{ width: '100%', maxHeight: 320, objectFit: 'contain', bgcolor: 'common.white' }}
            />
          )}
          {preview.status === 'json' && (
            <Typography variant="body2" data-testid="plan-export-json-summary">
              {t(`${PREFIX}.jsonSummary`, {
                locations: preview.summary.locations,
                objects: preview.summary.gardenObjects,
                slots: preview.summary.slots,
                size: formatSize(preview.summary.bytes),
              })}
            </Typography>
          )}
          {preview.status === 'error' && (
            <Typography variant="body2" color="text.secondary">
              {t(`${PREFIX}.previewUnavailable`)}
            </Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={download}
          loading={busy}
          disabled={preview.status === 'error' && preview.code === 'plan.empty'}
          sx={{ minHeight: 44 }}
          data-testid="plan-export-download"
        >
          {t(`${PREFIX}.download`)}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
