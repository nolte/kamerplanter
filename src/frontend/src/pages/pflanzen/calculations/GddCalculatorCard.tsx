import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import ButtonGroup from '@mui/material/ButtonGroup';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/calculations';
import type { GDDResponse } from '@/api/types';
import { GDD_BASE_TEMP_PRESETS } from './phasePresets';

interface DayRow {
  id: number;
  min: number;
  max: number;
}

let rowSeq = 0;
function makeRow(min: number, max: number): DayRow {
  rowSeq += 1;
  return { id: rowSeq, min, max };
}

const INITIAL_ROWS: DayRow[] = [makeRow(15, 25), makeRow(14, 24), makeRow(16, 28)];

/**
 * GDD calculator. Replaces the raw CSV multiline field with an editable
 * per-day min/max row editor (the biggest usability weakness of the old page).
 * Base temperature offers per-crop presets. The request payload is unchanged:
 * `{ daily_temps: [min, max][], base_temp_c }` sent to `POST /calculations/gdd`.
 */
export default function GddCalculatorCard() {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  const [rows, setRows] = useState<DayRow[]>(INITIAL_ROWS);
  const [baseTemp, setBaseTemp] = useState(10);
  const [result, setResult] = useState<GDDResponse | null>(null);

  const updateRow = useCallback((id: number, patch: Partial<DayRow>) => {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  }, []);

  const addRow = useCallback(() => {
    setRows((prev) => {
      const last = prev[prev.length - 1];
      return [...prev, makeRow(last?.min ?? 15, last?.max ?? 25)];
    });
  }, []);

  const removeRow = useCallback((id: number) => {
    setRows((prev) => (prev.length > 1 ? prev.filter((r) => r.id !== id) : prev));
  }, []);

  const invalidRow = useMemo(
    () => rows.some((r) => Number.isNaN(r.min) || Number.isNaN(r.max) || r.max < r.min),
    [rows],
  );

  const calculate = async () => {
    if (invalidRow) return;
    try {
      const daily_temps = rows.map((r) => [r.min, r.max] as [number, number]);
      const res = await calcApi.calculateGDD({ daily_temps, base_temp_c: baseTemp });
      setResult(res);
    } catch (err) {
      handleError(err);
    }
  };

  return (
    <Card>
      <CardContent>
        <HelpTooltip term="gdd">
          <Typography variant="h6" component="h2">
            {t('pages.calculations.gdd')}
          </Typography>
        </HelpTooltip>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
          {t('pages.calculations.gddIntro')}
        </Typography>

        <TextField
          type="number"
          label={t('pages.calculations.gddBaseTemp')}
          value={baseTemp}
          onChange={(e) => setBaseTemp(Number(e.target.value))}
          fullWidth
          sx={{ mb: 1 }}
          slotProps={{
            htmlInput: { min: 0, max: 30, step: 0.5 },
            input: { endAdornment: <InputAdornment position="end">°C</InputAdornment> },
          }}
        />
        <ButtonGroup size="small" variant="outlined" sx={{ mb: 2, flexWrap: 'wrap' }}>
          {GDD_BASE_TEMP_PRESETS.map((preset) => (
            <Button
              key={preset.key}
              onClick={() => setBaseTemp(preset.value)}
              variant={baseTemp === preset.value ? 'contained' : 'outlined'}
            >
              {t(`pages.calculations.gddBasePresets.${preset.key}`)} ({preset.value}°C)
            </Button>
          ))}
        </ButtonGroup>

        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          {t('pages.calculations.gddDailyTemps')}
        </Typography>
        <Stack spacing={1} sx={{ mb: 2 }}>
          {rows.map((row, index) => (
            <Box key={row.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ minWidth: 56 }}
              >
                {t('pages.calculations.gddDay', { day: index + 1 })}
              </Typography>
              <TextField
                type="number"
                label={t('pages.calculations.gddMinTemp')}
                value={row.min}
                onChange={(e) => updateRow(row.id, { min: Number(e.target.value) })}
                size="small"
                error={row.max < row.min}
                slotProps={{
                  htmlInput: { step: 0.5, 'aria-label': `${t('pages.calculations.gddMinTemp')} ${index + 1}` },
                  input: { endAdornment: <InputAdornment position="end">°C</InputAdornment> },
                }}
              />
              <TextField
                type="number"
                label={t('pages.calculations.gddMaxTemp')}
                value={row.max}
                onChange={(e) => updateRow(row.id, { max: Number(e.target.value) })}
                size="small"
                error={row.max < row.min}
                slotProps={{
                  htmlInput: { step: 0.5, 'aria-label': `${t('pages.calculations.gddMaxTemp')} ${index + 1}` },
                  input: { endAdornment: <InputAdornment position="end">°C</InputAdornment> },
                }}
              />
              <IconButton
                onClick={() => removeRow(row.id)}
                disabled={rows.length <= 1}
                aria-label={t('pages.calculations.gddRemoveDay', { day: index + 1 })}
                size="small"
              >
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            </Box>
          ))}
        </Stack>
        {invalidRow && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {t('pages.calculations.gddInvalidRow')}
          </Alert>
        )}
        <Button
          startIcon={<AddIcon />}
          onClick={addRow}
          size="small"
          sx={{ mb: 2 }}
        >
          {t('pages.calculations.gddAddDay')}
        </Button>

        <Button variant="contained" onClick={calculate} fullWidth disabled={invalidRow}>
          {t('pages.calculations.calculate')}
        </Button>

        {result && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Box sx={{ fontWeight: 600 }}>
              {t('pages.calculations.gddResult')}: {result.accumulated_gdd}
            </Box>
            <Box sx={{ mt: 0.5 }}>
              {t('pages.calculations.gddDaysCounted', { count: result.days_counted })}
            </Box>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
