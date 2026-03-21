import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Slider from '@mui/material/Slider';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PreviewIcon from '@mui/icons-material/Visibility';
import SaveIcon from '@mui/icons-material/Save';
import CircularProgress from '@mui/material/CircularProgress';
import DialogActions from '@mui/material/DialogActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/substrates';
import type { Substrate, MixComponent } from '@/api/types';

interface MixRow {
  substrate_key: string;
  fraction: number;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function SubstrateMixDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t, i18n } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const lang = i18n.language?.startsWith('en') ? 'en' : 'de';

  const [substrates, setSubstrates] = useState<Substrate[]>([]);
  const [nameDe, setNameDe] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [rows, setRows] = useState<MixRow[]>([
    { substrate_key: '', fraction: 0.5 },
    { substrate_key: '', fraction: 0.5 },
  ]);
  const [preview, setPreview] = useState<Substrate | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      api.listSubstrates(0, 200).then(setSubstrates).catch(() => {});
      setNameDe('');
      setNameEn('');
      setRows([
        { substrate_key: '', fraction: 0.5 },
        { substrate_key: '', fraction: 0.5 },
      ]);
      setPreview(null);
    }
  }, [open]);

  // Filter out substrates that are already mixes (no nested mixes)
  const availableSubstrates = substrates.filter((s) => !s.is_mix);

  const totalFraction = rows.reduce((sum, r) => sum + r.fraction, 0);
  const isBalanced = Math.abs(totalFraction - 1.0) <= 0.01;
  const allSelected = rows.every((r) => r.substrate_key !== '');
  const noDuplicates = new Set(rows.map((r) => r.substrate_key)).size === rows.length;
  const canSubmit = rows.length >= 2 && isBalanced && allSelected && noDuplicates;

  const updateRow = (index: number, field: keyof MixRow, value: string | number) => {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
    setPreview(null);
  };

  const addRow = () => {
    setRows((prev) => [...prev, { substrate_key: '', fraction: 0 }]);
    setPreview(null);
  };

  const removeRow = (index: number) => {
    if (rows.length <= 2) return;
    setRows((prev) => prev.filter((_, i) => i !== index));
    setPreview(null);
  };

  const distributeEvenly = () => {
    const fraction = Math.round((1.0 / rows.length) * 100) / 100;
    setRows((prev) => prev.map((r, i) => ({
      ...r,
      fraction: i === prev.length - 1 ? Math.round((1.0 - fraction * (prev.length - 1)) * 100) / 100 : fraction,
    })));
    setPreview(null);
  };

  const buildComponents = (): MixComponent[] =>
    rows.map((r) => ({ substrate_key: r.substrate_key, fraction: r.fraction }));

  const onPreview = async () => {
    if (!canSubmit) return;
    try {
      setPreviewing(true);
      const result = await api.previewSubstrateMix({
        name_de: nameDe,
        name_en: nameEn,
        components: buildComponents(),
      });
      setPreview(result);
    } catch (err) {
      handleError(err);
    } finally {
      setPreviewing(false);
    }
  };

  const onSave = async () => {
    if (!canSubmit) return;
    try {
      setSaving(true);
      await api.createSubstrateMix({
        name_de: nameDe,
        name_en: nameEn,
        components: buildComponents(),
      });
      notification.success(t('common.create'));
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t('pages.substrates.createMix')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.substrates.mixIntro')}
        </Typography>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, mb: 2 }}>
          <TextField
            label={`${t('pages.substrates.name')} (DE)`}
            value={nameDe}
            onChange={(e) => setNameDe(e.target.value)}
            size="small"
            fullWidth
          />
          <TextField
            label={`${t('pages.substrates.name')} (EN)`}
            value={nameEn}
            onChange={(e) => setNameEn(e.target.value)}
            size="small"
            fullWidth
          />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2" color="text.secondary">
            {t('pages.substrates.mixComponents')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button size="small" onClick={distributeEvenly}>
              {t('pages.substrates.distributeEvenly')}
            </Button>
            <Button size="small" startIcon={<AddIcon />} onClick={addRow}>
              {t('pages.substrates.addComponent')}
            </Button>
          </Box>
        </Box>

        {rows.map((row, index) => (
          <Box key={index} sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1.5 }}>
            <TextField
              select
              label={t('entities.substrate')}
              value={row.substrate_key}
              onChange={(e) => updateRow(index, 'substrate_key', e.target.value)}
              size="small"
              sx={{ flex: 2 }}
            >
              {availableSubstrates.map((s) => (
                <MenuItem
                  key={s.key}
                  value={s.key}
                  disabled={rows.some((r, i) => i !== index && r.substrate_key === s.key)}
                >
                  {(lang === 'en' ? s.name_en : s.name_de) || `${t(`enums.substrateType.${s.type}`)} ${s.brand ?? ''}`}
                </MenuItem>
              ))}
            </TextField>
            <Box sx={{ flex: 1, px: 1 }}>
              <Slider
                value={row.fraction}
                onChange={(_, val) => updateRow(index, 'fraction', Math.round((val as number) * 100) / 100)}
                min={0.01}
                max={1.0}
                step={0.01}
                size="small"
                valueLabelDisplay="auto"
                valueLabelFormat={(v) => `${Math.round(v * 100)}%`}
              />
            </Box>
            <Typography variant="body2" sx={{ minWidth: 48, textAlign: 'right' }}>
              {Math.round(row.fraction * 100)}%
            </Typography>
            <IconButton
              size="small"
              onClick={() => removeRow(index)}
              disabled={rows.length <= 2}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        ))}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1, mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.substrates.totalFraction')}:
          </Typography>
          <Chip
            label={`${Math.round(totalFraction * 100)}%`}
            size="small"
            color={isBalanced ? 'success' : 'error'}
          />
          {!isBalanced && (
            <Typography variant="caption" color="error">
              {t('pages.substrates.fractionsMustSum100')}
            </Typography>
          )}
          {!noDuplicates && allSelected && (
            <Typography variant="caption" color="error">
              {t('pages.substrates.noDuplicateComponents')}
            </Typography>
          )}
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Button
            variant="outlined"
            startIcon={previewing ? <CircularProgress size={16} /> : <PreviewIcon />}
            onClick={onPreview}
            disabled={!canSubmit || previewing}
          >
            {t('pages.substrates.previewMix')}
          </Button>
        </Box>

        {preview && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              {t('pages.substrates.mixPreviewTitle')}
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 1 }}>
              <Box>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.type')}</Typography>
                <Typography variant="body2">{t(`enums.substrateType.${preview.type}`)}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.phBase')}</Typography>
                <Typography variant="body2">{preview.ph_base.toFixed(1)}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.ecBase')}</Typography>
                <Typography variant="body2">{preview.ec_base_ms.toFixed(2)} mS/cm</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.waterRetention')}</Typography>
                <Typography variant="body2">{t(`enums.waterRetention.${preview.water_retention}`)}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.airPorosity')}</Typography>
                <Typography variant="body2">{preview.air_porosity_percent.toFixed(1)}%</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.bufferCapacity')}</Typography>
                <Typography variant="body2">{t(`enums.bufferCapacity.${preview.buffer_capacity}`)}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.reusable')}</Typography>
                <Typography variant="body2">{preview.reusable ? t('common.yes') : t('common.no')}</Typography>
              </Box>
              {preview.irrigation_strategy && (
                <Box>
                  <Typography variant="caption" color="text.secondary">{t('pages.substrates.irrigationStrategy')}</Typography>
                  <Typography variant="body2">{t(`enums.irrigationStrategy.${preview.irrigation_strategy}`)}</Typography>
                </Box>
              )}
            </Box>
            {Object.keys(preview.composition).length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">{t('pages.substrates.composition')}</Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                  {Object.entries(preview.composition).map(([material, pct]) => (
                    <Chip key={material} label={`${material}: ${Math.round(pct * 100)}%`} size="small" variant="outlined" />
                  ))}
                </Box>
              </Box>
            )}
          </>
        )}

        {!isBalanced && rows.every((r) => r.substrate_key) && (
          <Alert severity="info" sx={{ mt: 1 }}>
            {t('pages.substrates.adjustFractions')}
          </Alert>
        )}

      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>{t('common.cancel')}</Button>
        <Button
          variant="contained"
          startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
          onClick={onSave}
          disabled={!canSubmit || saving}
        >
          {t('common.create')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
