import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Autocomplete from '@mui/material/Autocomplete';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/calculations';
import type { SlotCapacityResponse } from '@/api/types';
import { SPACING_PRESETS } from './phasePresets';

interface StatTileProps {
  label: string;
  value: string;
}

function StatTile({ label, value }: StatTileProps) {
  return (
    <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center', height: '100%' }}>
      <Typography variant="h6" component="p" color="primary">
        {value}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
    </Paper>
  );
}

const SPACING_OPTIONS = SPACING_PRESETS.map(String);

/**
 * Slot-capacity calculator. Plant spacing is an `Autocomplete` with typical row
 * spacings (free-solo so any custom value is still accepted); results render as
 * readable stat tiles instead of the old dense inline alert. Payload unchanged:
 * `{ area_m2, plant_spacing_cm }` → `POST /calculations/slot-capacity`.
 */
export default function SlotCapacityCalculatorCard() {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  const [area, setArea] = useState(10);
  const [spacing, setSpacing] = useState(30);
  const [result, setResult] = useState<SlotCapacityResponse | null>(null);

  const calculate = async () => {
    try {
      const res = await calcApi.calculateSlotCapacity({
        area_m2: area,
        plant_spacing_cm: spacing,
      });
      setResult(res);
    } catch (err) {
      handleError(err);
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" sx={{ mb: 1 }}>
          {t('pages.calculations.slotCapacity')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.calculations.slotCapacityIntro')}
        </Typography>

        <TextField
          type="number"
          label={t('pages.calculations.areaMsq')}
          value={area}
          onChange={(e) => setArea(Number(e.target.value))}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{
            htmlInput: { min: 0.1, step: 0.1 },
            input: { endAdornment: <InputAdornment position="end">m²</InputAdornment> },
          }}
        />

        <Autocomplete
          freeSolo
          options={SPACING_OPTIONS}
          value={String(spacing)}
          onChange={(_event, value) => {
            const parsed = Number(value);
            if (!Number.isNaN(parsed) && parsed > 0) setSpacing(parsed);
          }}
          onInputChange={(_event, value) => {
            const parsed = Number(value);
            if (!Number.isNaN(parsed) && parsed > 0) setSpacing(parsed);
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t('pages.calculations.plantSpacing')}
              helperText={t('pages.calculations.plantSpacingHelp')}
            />
          )}
          sx={{ mb: 2 }}
        />

        <Button variant="contained" onClick={calculate} fullWidth>
          {t('pages.calculations.calculate')}
        </Button>

        {result && (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={1}>
              <Grid size={4}>
                <StatTile
                  label={t('pages.calculations.scMax')}
                  value={String(result.max_capacity)}
                />
              </Grid>
              <Grid size={4}>
                <StatTile
                  label={t('pages.calculations.scOptimal')}
                  value={`${result.optimal_range[0]}–${result.optimal_range[1]}`}
                />
              </Grid>
              <Grid size={4}>
                <StatTile
                  label={t('pages.calculations.scPerM2')}
                  value={String(result.plants_per_m2)}
                />
              </Grid>
            </Grid>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
