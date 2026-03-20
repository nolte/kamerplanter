import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Alert from '@mui/material/Alert';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import type { SiteWaterConfig, WaterSourceWarning } from '@/api/types';
import { waterSourceFieldConfig } from '@/config/fieldConfigs';

interface WaterSourceSectionProps {
  value: SiteWaterConfig;
  onChange: (config: SiteWaterConfig) => void;
  warnings?: WaterSourceWarning[];
}

export default function WaterSourceSection({
  value,
  onChange,
  warnings = [],
}: WaterSourceSectionProps) {
  const { t } = useTranslation();
  const w = (key: string) => t(`pages.sites.water.${key}`);
  const fc = waterSourceFieldConfig;

  const tap = value.tap_water_profile ?? {
    ec_ms: 0.3,
    ph: 7.0,
    alkalinity_ppm: 0,
    gh_ppm: 0,
    calcium_ppm: 0,
    magnesium_ppm: 0,
    chlorine_ppm: 0,
    chloramine_ppm: 0,
    measurement_date: null,
    source_note: null,
  };

  const ro = value.ro_water_profile ?? { ec_ms: 0.02, ph: 6.5 };

  const updateTap = (field: string, val: number | string | null) => {
    onChange({
      ...value,
      tap_water_profile: { ...tap, [field]: val },
    });
  };

  const updateRo = (field: string, val: number) => {
    onChange({
      ...value,
      ro_water_profile: { ...ro, [field]: val },
    });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Typography variant="subtitle1">{w('waterConfig')}</Typography>

      {/* Warnings */}
      {warnings.map((warning) => (
        <Alert
          key={warning.code}
          severity={warning.severity === 'warning' ? 'warning' : 'info'}
          data-testid={`water-warning-${warning.code}`}
        >
          {warning.message}
        </Alert>
      ))}

      {/* Tap Water — basic */}
      <Typography variant="subtitle2">{w('tapWaterProfile')}</Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
        <TextField
          label={w('ecMs')}
          type="number"
          value={tap.ec_ms}
          onChange={(e) => updateTap('ec_ms', parseFloat(e.target.value) || 0)}
          inputProps={{ step: 0.01, min: 0, max: 2.0, inputMode: 'decimal' }}
          InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, whiteSpace: 'nowrap', color: 'text.secondary' }}>mS/cm</Typography> }}
          size="small"
          helperText="0.0 – 2.0 mS/cm"
          data-testid="tap-ec"
        />
        <TextField
          label={w('ph')}
          type="number"
          value={tap.ph}
          onChange={(e) => updateTap('ph', parseFloat(e.target.value) || 0)}
          inputProps={{ step: 0.1, min: 3.0, max: 10.0, inputMode: 'decimal' }}
          size="small"
          helperText="3.0 – 10.0"
          data-testid="tap-ph"
        />
      </Box>

      {/* Tap Water — expert fields */}
      <ExpertiseFieldWrapper minLevel={fc.alkalinity_ppm.level}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
          <TextField
            label={w('alkalinity')}
            type="number"
            value={tap.alkalinity_ppm}
            onChange={(e) => updateTap('alkalinity_ppm', parseFloat(e.target.value) || 0)}
            inputProps={{ step: 0.1, min: 0, max: 500, inputMode: 'decimal' }}
            InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, color: 'text.secondary' }}>ppm</Typography> }}
            size="small"
          />
          <TextField
            label={w('ghPpm')}
            type="number"
            value={tap.gh_ppm}
            onChange={(e) => updateTap('gh_ppm', parseFloat(e.target.value) || 0)}
            inputProps={{ step: 0.1, min: 0, max: 1000, inputMode: 'decimal' }}
            InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, color: 'text.secondary' }}>ppm</Typography> }}
            size="small"
          />
          <TextField
            label={w('calciumPpm')}
            type="number"
            value={tap.calcium_ppm}
            onChange={(e) => updateTap('calcium_ppm', parseFloat(e.target.value) || 0)}
            inputProps={{ step: 0.1, min: 0, max: 500, inputMode: 'decimal' }}
            InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, color: 'text.secondary' }}>ppm</Typography> }}
            size="small"
          />
          <TextField
            label={w('magnesiumPpm')}
            type="number"
            value={tap.magnesium_ppm}
            onChange={(e) => updateTap('magnesium_ppm', parseFloat(e.target.value) || 0)}
            inputProps={{ step: 0.1, min: 0, max: 200, inputMode: 'decimal' }}
            InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, color: 'text.secondary' }}>ppm</Typography> }}
            size="small"
          />
          <TextField
            label={w('chlorinePpm')}
            type="number"
            value={tap.chlorine_ppm}
            onChange={(e) => updateTap('chlorine_ppm', parseFloat(e.target.value) || 0)}
            inputProps={{ step: 0.1, min: 0, max: 5, inputMode: 'decimal' }}
            InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, color: 'text.secondary' }}>ppm</Typography> }}
            size="small"
          />
          <TextField
            label={w('chloraminePpm')}
            type="number"
            value={tap.chloramine_ppm}
            onChange={(e) => updateTap('chloramine_ppm', parseFloat(e.target.value) || 0)}
            inputProps={{ step: 0.1, min: 0, max: 5, inputMode: 'decimal' }}
            InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, color: 'text.secondary' }}>ppm</Typography> }}
            size="small"
          />
        </Box>
      </ExpertiseFieldWrapper>

      <ExpertiseFieldWrapper minLevel={fc.measurement_date.level}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
          <TextField
            label={w('measurementDate')}
            type="date"
            value={tap.measurement_date ?? ''}
            onChange={(e) => updateTap('measurement_date', e.target.value || null)}
            InputLabelProps={{ shrink: true }}
            size="small"
          />
          <TextField
            label={w('sourceNote')}
            value={tap.source_note ?? ''}
            onChange={(e) => updateTap('source_note', e.target.value || null)}
            size="small"
            placeholder={w('sourceNotePlaceholder')}
          />
        </Box>
      </ExpertiseFieldWrapper>

      {/* RO system toggle */}
      <FormControlLabel
        control={
          <Switch
            checked={value.has_ro_system}
            onChange={(e) => onChange({ ...value, has_ro_system: e.target.checked })}
            data-testid="ro-system-toggle"
          />
        }
        label={w('hasRoSystem')}
      />

      {/* RO Water fields — only visible when RO system is enabled */}
      {value.has_ro_system && (
        <>
          <Typography variant="subtitle2">{w('roWaterProfile')}</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
            <TextField
              label={w('ecMs')}
              type="number"
              value={ro.ec_ms}
              onChange={(e) => updateRo('ec_ms', parseFloat(e.target.value) || 0)}
              inputProps={{ step: 0.01, min: 0, max: 0.5, inputMode: 'decimal' }}
              InputProps={{ endAdornment: <Typography variant="caption" sx={{ pr: 1, whiteSpace: 'nowrap', color: 'text.secondary' }}>mS/cm</Typography> }}
              size="small"
              helperText="0.0 – 0.5 mS/cm"
              data-testid="ro-ec"
            />
            <TextField
              label={w('ph')}
              type="number"
              value={ro.ph}
              onChange={(e) => updateRo('ph', parseFloat(e.target.value) || 0)}
              inputProps={{ step: 0.1, min: 3.0, max: 10.0, inputMode: 'decimal' }}
              size="small"
              helperText="3.0 – 10.0"
              data-testid="ro-ph"
            />
          </Box>
        </>
      )}
    </Box>
  );
}
