import { useState, useCallback, useId } from 'react';
import { useTranslation } from 'react-i18next';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Divider from '@mui/material/Divider';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import IconButton from '@mui/material/IconButton';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CloseIcon from '@mui/icons-material/Close';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { useNotification } from '@/hooks/useNotification';
import { downloadPlantLabelsPdf } from '@/api/endpoints/print';

interface PlantLabelDialogProps {
  open: boolean;
  onClose: () => void;
  plantKeys: string[];
  /** Optional mapping of plant key to display name for showing the selection. */
  plantNames?: Record<string, string>;
}

type LabelLayout = 'single' | 'grid_2x4' | 'grid_3x3';

interface FieldOption {
  key: string;
  i18nKey: string;
  defaultChecked: boolean;
  disabled?: boolean;
  helperI18nKey?: string;
}

const FIELD_OPTIONS: FieldOption[] = [
  { key: 'name', i18nKey: 'print.fieldName', defaultChecked: true },
  { key: 'scientific_name', i18nKey: 'print.fieldScientificName', defaultChecked: true },
  { key: 'family', i18nKey: 'print.fieldFamily', defaultChecked: false },
  { key: 'planted_date', i18nKey: 'print.fieldPlantedDate', defaultChecked: true },
  { key: 'current_phase', i18nKey: 'print.fieldCurrentPhase', defaultChecked: false },
  { key: 'location', i18nKey: 'print.fieldLocation', defaultChecked: false },
  { key: 'cultivar', i18nKey: 'print.fieldCultivar', defaultChecked: false },
  { key: 'note', i18nKey: 'print.fieldNote', defaultChecked: false },
  {
    key: 'qr_code',
    i18nKey: 'print.fieldQrCode',
    defaultChecked: true,
    disabled: true,
    helperI18nKey: 'print.fieldQrCodeHelper',
  },
];

interface LayoutOption {
  value: LabelLayout;
  i18nKey: string;
  helperI18nKey: string;
}

const LAYOUT_OPTIONS: LayoutOption[] = [
  { value: 'single', i18nKey: 'print.layoutSingle', helperI18nKey: 'print.layoutSingleHelper' },
  {
    value: 'grid_2x4',
    i18nKey: 'print.layoutGrid2x4',
    helperI18nKey: 'print.layoutGrid2x4Helper',
  },
  {
    value: 'grid_3x3',
    i18nKey: 'print.layoutGrid3x3',
    helperI18nKey: 'print.layoutGrid3x3Helper',
  },
];

function getDefaultSelectedFields(): Set<string> {
  return new Set(FIELD_OPTIONS.filter((f) => f.defaultChecked).map((f) => f.key));
}

export function PlantLabelDialog({
  open,
  onClose,
  plantKeys,
  plantNames,
}: PlantLabelDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const [selectedFields, setSelectedFields] = useState<Set<string>>(getDefaultSelectedFields);
  const [layout, setLayout] = useState<LabelLayout>('grid_2x4');
  const [loading, setLoading] = useState(false);

  const titleId = useId();
  const descId = useId();
  const fieldsGroupId = useId();
  const layoutGroupId = useId();

  const handleFieldToggle = useCallback((fieldKey: string) => {
    setSelectedFields((prev) => {
      const next = new Set(prev);
      if (next.has(fieldKey)) {
        next.delete(fieldKey);
      } else {
        next.add(fieldKey);
      }
      return next;
    });
  }, []);

  const handleLayoutChange = useCallback(
    (_: React.ChangeEvent<HTMLInputElement>, value: string) => {
      setLayout(value as LabelLayout);
    },
    [],
  );

  const handleDownload = useCallback(async () => {
    setLoading(true);
    try {
      // Filter out qr_code from fields sent to backend (it is always included server-side)
      const fields = [...selectedFields].filter((f) => f !== 'qr_code');
      const blob = await downloadPlantLabelsPdf(plantKeys, fields, layout);

      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `plant-labels-${layout}.pdf`;
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
  }, [plantKeys, selectedFields, layout, notification, t, onClose]);

  const hasPlants = plantKeys.length > 0;

  return (
    <Dialog
      open={open}
      onClose={loading ? undefined : onClose}
      maxWidth="sm"
      fullWidth
      fullScreen={fullScreen}
      aria-labelledby={titleId}
      aria-describedby={descId}
      data-testid="plant-label-dialog"
    >
      <DialogTitle
        id={titleId}
        sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pr: 1 }}
      >
        {t('print.plantLabelsTitle')}
        <IconButton
          onClick={onClose}
          aria-label={t('common.close')}
          size="small"
          disabled={loading}
          data-testid="plant-label-dialog-close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Intro text */}
        <DialogContentText id={descId} variant="body2">
          {t('print.plantLabelsIntro')}
        </DialogContentText>

        {/* Selected plants section */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            {t('print.plantLabelsCount', { count: plantKeys.length })}
          </Typography>
          {!hasPlants && (
            <Alert severity="info" sx={{ mt: 1 }}>
              {t('print.plantLabelsNone')}
            </Alert>
          )}
          {hasPlants && plantNames && Object.keys(plantNames).length > 0 && (
            <Box
              sx={{
                display: 'flex',
                gap: 0.5,
                flexWrap: 'wrap',
                maxHeight: 120,
                overflowY: 'auto',
                p: 1,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                bgcolor: 'action.hover',
              }}
            >
              {plantKeys.map((key) => (
                <Chip key={key} label={plantNames[key] ?? key} size="small" variant="outlined" />
              ))}
            </Box>
          )}
        </Box>

        <Divider />

        {/* Field selection */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
            <FormLabel component="legend" id={fieldsGroupId} sx={{ fontWeight: 600 }}>
              {t('print.fieldsLabel')}
            </FormLabel>
            <Tooltip
              title={t('print.fieldsIntro')}
              arrow
              enterTouchDelay={0}
              leaveTouchDelay={4000}
            >
              <InfoOutlinedIcon
                sx={{ fontSize: 18, color: 'text.secondary', cursor: 'help' }}
                aria-label={t('print.fieldsIntro')}
                tabIndex={0}
              />
            </Tooltip>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            {t('print.fieldsIntro')}
          </Typography>
          <FormGroup data-testid="field-checkboxes" aria-labelledby={fieldsGroupId}>
            {FIELD_OPTIONS.map((field) => (
              <Box key={field.key}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={selectedFields.has(field.key)}
                      onChange={() => handleFieldToggle(field.key)}
                      disabled={field.disabled}
                      data-testid={`field-checkbox-${field.key}`}
                    />
                  }
                  label={t(field.i18nKey)}
                />
                {field.helperI18nKey && (
                  <FormHelperText sx={{ mt: -0.5, ml: 4 }}>
                    {t(field.helperI18nKey)}
                  </FormHelperText>
                )}
              </Box>
            ))}
          </FormGroup>
        </Box>

        <Divider />

        {/* Layout selection */}
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
            <FormLabel component="legend" id={layoutGroupId} sx={{ fontWeight: 600 }}>
              {t('print.layoutLabel')}
            </FormLabel>
            <Tooltip
              title={t('print.layoutIntro')}
              arrow
              enterTouchDelay={0}
              leaveTouchDelay={4000}
            >
              <InfoOutlinedIcon
                sx={{ fontSize: 18, color: 'text.secondary', cursor: 'help' }}
                aria-label={t('print.layoutIntro')}
                tabIndex={0}
              />
            </Tooltip>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            {t('print.layoutIntro')}
          </Typography>
          <RadioGroup
            value={layout}
            onChange={handleLayoutChange}
            data-testid="layout-radio-group"
            aria-labelledby={layoutGroupId}
          >
            {LAYOUT_OPTIONS.map((opt) => (
              <Box key={opt.value}>
                <FormControlLabel
                  value={opt.value}
                  control={<Radio data-testid={`layout-radio-${opt.value}`} />}
                  label={t(opt.i18nKey)}
                />
                <FormHelperText sx={{ mt: -0.5, ml: 4 }}>{t(opt.helperI18nKey)}</FormHelperText>
              </Box>
            ))}
          </RadioGroup>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 2, py: 1.5 }}>
        <Button onClick={onClose} disabled={loading} data-testid="plant-label-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={handleDownload}
          disabled={loading || !hasPlants}
          startIcon={
            loading ? <CircularProgress size={18} color="inherit" /> : <PictureAsPdfIcon />
          }
          data-testid="plant-label-download"
        >
          {loading ? t('print.printing') : t('print.downloadPdf')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
