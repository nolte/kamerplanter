/**
 * "Record soil analysis" (REQ-053 GP-FR-122): the values of one lab sheet, test kit or probe reading - each with
 * parameter, value, unit and method - plus when, from where and at which depth the sample was taken. The analysis is
 * a care event (`soil_analysis`); the server writes the newest pH, EC, humus and lime values with their method into
 * the soil profile. Nothing is converted between methods or units, and no amount is suggested from it.
 */
import { useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import { useApiError } from '@/hooks/useApiError';
import { performedAtBounds } from '../care/careForm';
import { recordSoilAnalysis } from './bedApi';
import {
  MAX_ROWS,
  buildSoilAnalysisBody,
  contentClassAllowed,
  emptyRow,
  emptySoilAnalysisForm,
  hasErrors,
  methodEnumGroup,
  methodRequired,
  methodsFor,
  validateSoilAnalysis,
  withParameter,
  type MeasurementRow,
  type SoilAnalysisFormState,
} from './soilAnalysisForm';
import {
  SOIL_ANALYSIS_SOURCES,
  SOIL_CONTENT_CLASSES,
  SOIL_PARAMETERS,
  UNITS_BY_PARAMETER,
  type SoilAnalysisSource,
  type SoilParameter,
} from './soilAnalysisTypes';

const TOUCH = { '& .MuiInputBase-root': { minHeight: 48 } };
const PREFIX = 'pages.bed.soil.analysis';

interface SoilAnalysisDialogProps {
  bedKey: string;
  bedName: string;
  onClose: () => void;
  /** The analysis was stored; the tab reloads the profile and the history. */
  onSaved: () => void;
}

export default function SoilAnalysisDialog({ bedKey, bedName, onClose, onSaved }: SoilAnalysisDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const now = useMemo(() => new Date(), []);
  const bounds = useMemo(() => performedAtBounds(now), [now]);
  const [form, setForm] = useState<SoilAnalysisFormState>(() => emptySoilAnalysisForm(now));
  const [nextId, setNextId] = useState(2);
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);
  // The row that was just added takes the focus; after a removal the focus returns to "add value".
  const [focusRowId, setFocusRowId] = useState<number | null>(null);
  const addButtonRef = useRef<HTMLButtonElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const errors = showErrors ? validateSoilAnalysis(form, now) : { rows: {} };

  const patchRow = (id: number, change: (row: MeasurementRow) => MeasurementRow) =>
    setForm((current) => ({ ...current, rows: current.rows.map((row) => (row.id === id ? change(row) : row)) }));

  const addRow = () => {
    // A new row starts with the first parameter not yet in the analysis.
    const used = new Set(form.rows.map((row) => row.parameter));
    const parameter = SOIL_PARAMETERS.find((value) => !used.has(value)) ?? 'ph';
    setForm((current) => ({ ...current, rows: [...current.rows, emptyRow(nextId, parameter)] }));
    setFocusRowId(nextId);
    setNextId((value) => value + 1);
  };

  const removeRow = (id: number) => {
    setForm((current) => ({ ...current, rows: current.rows.filter((row) => row.id !== id) }));
    setFocusRowId(null);
    addButtonRef.current?.focus();
  };

  const unitLabel = (unit: string) => t(`enums.soilUnit.${unit}`, { defaultValue: unit });
  const parameterLabel = (parameter: string) => t(`enums.soilParameter.${parameter}`, { defaultValue: parameter });

  const summaryOf = (state: SoilAnalysisFormState): string => {
    const values = state.rows.map((row) => `${parameterLabel(row.parameter)} ${row.value.trim()} ${unitLabel(row.unit)}`);
    return `${t(`${PREFIX}.summary`, { source: t(`enums.soilAnalysisSource.${state.source}`) })}: ${values.join(', ')}`.slice(
      0,
      500,
    );
  };

  const submit = async () => {
    if (hasErrors(validateSoilAnalysis(form, new Date()))) {
      setShowErrors(true);
      // Move the focus to the first field with a problem once the errors are rendered.
      window.setTimeout(() => contentRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus(), 0);
      return;
    }
    setSaving(true);
    try {
      await recordSoilAnalysis(buildSoilAnalysisBody(bedKey, form, summaryOf(form)));
      onSaved();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="md"
      aria-labelledby="soil-analysis-title"
      data-testid="soil-analysis-dialog"
    >
      <DialogTitle id="soil-analysis-title">{t(`${PREFIX}.title`, { name: bedName })}</DialogTitle>
      <DialogContent ref={contentRef}>
        <DialogContentText sx={{ mb: 2 }}>{t(`${PREFIX}.description`)}</DialogContentText>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              type="datetime-local"
              label={t(`${PREFIX}.performedAt`)}
              value={form.performedAt}
              onChange={(event) => setForm((current) => ({ ...current, performedAt: event.target.value }))}
              error={Boolean(errors.performedAt)}
              helperText={errors.performedAt ? t(`${PREFIX}.errors.${errors.performedAt}`) : t(`${PREFIX}.performedAtHelper`)}
              required
              fullWidth
              sx={TOUCH}
              slotProps={{
                inputLabel: { shrink: true },
                htmlInput: { min: bounds.min, max: bounds.max, 'data-testid': 'soil-analysis-performed-at' },
              }}
            />
            <TextField
              select
              label={t(`${PREFIX}.source`)}
              value={form.source}
              onChange={(event) =>
                setForm((current) => ({ ...current, source: event.target.value as SoilAnalysisSource }))
              }
              helperText={t(`${PREFIX}.sourceHelper`)}
              fullWidth
              sx={TOUCH}
              slotProps={{ htmlInput: { 'data-testid': 'soil-analysis-source' } }}
            >
              {SOIL_ANALYSIS_SOURCES.map((source) => (
                <MenuItem key={source} value={source}>
                  {t(`enums.soilAnalysisSource.${source}`)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label={t(`${PREFIX}.depth`)}
              value={form.depth}
              onChange={(event) => setForm((current) => ({ ...current, depth: event.target.value }))}
              error={Boolean(errors.depth)}
              helperText={errors.depth ? t(`${PREFIX}.errors.depth`) : t(`${PREFIX}.depthHelper`)}
              fullWidth
              sx={TOUCH}
              slotProps={{
                htmlInput: { inputMode: 'decimal', 'data-testid': 'soil-analysis-depth' },
                input: { endAdornment: <Typography color="text.secondary">cm</Typography> },
              }}
            />
          </Stack>

          <Typography variant="subtitle2" component="h3">
            {t(`${PREFIX}.values`)}
          </Typography>
          {form.rows.map((row, index) => (
            <MeasurementRowFields
              key={row.id}
              row={row}
              index={index}
              source={form.source}
              error={errors.rows[row.id] ?? {}}
              removable={form.rows.length > 1}
              onChange={(change) => patchRow(row.id, change)}
              onRemove={() => removeRow(row.id)}
              autoFocus={row.id === focusRowId}
              parameterLabel={parameterLabel}
              unitLabel={unitLabel}
            />
          ))}
          <Box>
            <Button
              startIcon={<AddIcon />}
              onClick={addRow}
              ref={addButtonRef}
              disabled={form.rows.length >= MAX_ROWS}
              sx={{ minHeight: 48 }}
              data-testid="soil-analysis-add-row"
            >
              {t(`${PREFIX}.addValue`)}
            </Button>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', px: 1 }}>
              {t(`${PREFIX}.rowCount`, { count: form.rows.length, max: MAX_ROWS })}
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.noConversion`)}
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          loading={saving}
          sx={{ minHeight: 48 }}
          data-testid="soil-analysis-submit"
        >
          {t(`${PREFIX}.submit`)}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

interface MeasurementRowFieldsProps {
  row: MeasurementRow;
  index: number;
  source: SoilAnalysisSource;
  error: { value?: string; method?: string };
  removable: boolean;
  onChange: (change: (row: MeasurementRow) => MeasurementRow) => void;
  onRemove: () => void;
  autoFocus: boolean;
  parameterLabel: (parameter: string) => string;
  unitLabel: (unit: string) => string;
}

function MeasurementRowFields({
  row,
  index,
  source,
  error,
  removable,
  onChange,
  onRemove,
  autoFocus,
  parameterLabel,
  unitLabel,
}: MeasurementRowFieldsProps) {
  const { t } = useTranslation();
  const position = index + 1;
  const methods = methodsFor(row.parameter);
  const required = methodRequired(row.parameter);
  const group = methodEnumGroup(row.parameter);
  const showClass = contentClassAllowed(row, source);

  return (
    <Paper
      variant="outlined"
      component="fieldset"
      sx={{ p: 2, m: 0, minWidth: 0 }}
      data-testid={`soil-analysis-row-${position}`}
    >
      <Box component="legend" sx={{ px: 0.5, typography: 'caption', color: 'text.secondary' }}>
        {t(`${PREFIX}.valueN`, { n: position })}
      </Box>
      {/* Phone: parameter and method full width, value + unit side by side; from sm one row of four fields. */}
      <Box
        sx={{
          display: 'grid',
          gap: 2,
          alignItems: 'start',
          gridTemplateColumns: { xs: 'repeat(2, minmax(0, 1fr))', sm: 'repeat(4, minmax(0, 1fr)) auto' },
          '& > .MuiTextField-root': { gridColumn: { xs: 'span 2', sm: 'auto' } },
          '& > .soil-value, & > .soil-unit': { gridColumn: { xs: 'span 1', sm: 'auto' } },
          '& > .soil-class': { gridColumn: { xs: 'span 2', sm: '1 / span 4' } },
        }}
      >
        <TextField
          select
          autoFocus={autoFocus}
          label={t(`${PREFIX}.parameter`)}
          value={row.parameter}
          onChange={(event) => onChange((current) => withParameter(current, event.target.value as SoilParameter))}
          fullWidth
          sx={TOUCH}
          slotProps={{ htmlInput: { 'data-testid': `soil-analysis-parameter-${position}` } }}
        >
          {SOIL_PARAMETERS.map((parameter) => (
            <MenuItem key={parameter} value={parameter}>
              {parameterLabel(parameter)}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          className="soil-value"
          label={t(`${PREFIX}.value`)}
          value={row.value}
          onChange={(event) => {
            const value = event.target.value;
            onChange((current) => ({ ...current, value }));
          }}
          required
          error={Boolean(error.value)}
          helperText={error.value ? t(`${PREFIX}.errors.value.${error.value}`) : undefined}
          fullWidth
          sx={TOUCH}
          slotProps={{ htmlInput: { inputMode: 'decimal', 'data-testid': `soil-analysis-value-${position}` } }}
        />
        <TextField
          select
          className="soil-unit"
          label={t(`${PREFIX}.unit`)}
          value={row.unit}
          onChange={(event) => {
            const unit = event.target.value;
            onChange((current) => ({ ...current, unit }));
          }}
          disabled={UNITS_BY_PARAMETER[row.parameter].length === 1}
          fullWidth
          sx={TOUCH}
          slotProps={{ htmlInput: { 'data-testid': `soil-analysis-unit-${position}` } }}
        >
          {UNITS_BY_PARAMETER[row.parameter].map((unit) => (
            <MenuItem key={unit} value={unit}>
              {unitLabel(unit)}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label={t(`${PREFIX}.method`)}
          value={row.method}
          onChange={(event) => {
            const method = event.target.value;
            onChange((current) => ({ ...current, method, contentClass: '' }));
          }}
          required={required}
          error={Boolean(error.method)}
          helperText={
            error.method ? t(`${PREFIX}.errors.method`) : required ? t(`${PREFIX}.methodHelper.${row.parameter}`) : undefined
          }
          fullWidth
          sx={TOUCH}
          slotProps={{ htmlInput: { 'data-testid': `soil-analysis-method-${position}` } }}
        >
          {!required && <MenuItem value="">{t(`${PREFIX}.methodNone`)}</MenuItem>}
          {methods.map((method) => (
            <MenuItem key={method} value={method}>
              {t(`enums.${group}.${method}`)}
            </MenuItem>
          ))}
        </TextField>
        {showClass && (
          <TextField
            select
            className="soil-class"
            label={t(`${PREFIX}.contentClass`)}
            value={row.contentClass}
            onChange={(event) => {
              const contentClass = event.target.value;
              onChange((current) => ({ ...current, contentClass }));
            }}
            helperText={t(`${PREFIX}.contentClassHelper`)}
            fullWidth
            sx={TOUCH}
            slotProps={{ htmlInput: { 'data-testid': `soil-analysis-class-${position}` } }}
          >
            <MenuItem value="">{t(`${PREFIX}.contentClassNone`)}</MenuItem>
            {SOIL_CONTENT_CLASSES.map((value) => (
              <MenuItem key={value} value={value}>
                {value}
              </MenuItem>
            ))}
          </TextField>
        )}
        {removable && (
          <Button
            onClick={onRemove}
            color="inherit"
            aria-label={t(`${PREFIX}.removeValue`, { n: position })}
            startIcon={<DeleteOutlinedIcon />}
            sx={{
              minWidth: 48,
              minHeight: 48,
              gridColumn: { xs: 'span 2', sm: 'auto' },
              justifySelf: { xs: 'end', sm: 'center' },
              '& .MuiButton-startIcon': { mr: { xs: 1, sm: 0 }, ml: { xs: -0.5, sm: 0 } },
            }}
            data-testid={`soil-analysis-remove-${position}`}
          >
            <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>
              {t(`${PREFIX}.removeValueShort`)}
            </Box>
          </Button>
        )}
      </Box>
    </Paper>
  );
}
