import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import type { ChipProps } from '@mui/material/Chip';

/**
 * REQ-046 §4.2 / AC-10 — visualises the provenance of a weather record: the
 * source (registry key → localized label) plus a `data_kind` label that keeps
 * measured HA current conditions (`observed`) visibly separate from a forecast
 * or a reanalysis. Reused by the connection-test preview and the dashboard
 * widget so both surfaces label provenance identically.
 */

const DATA_KIND_COLOR: Record<string, ChipProps['color']> = {
  forecast: 'info',
  observed: 'success',
  reanalysis: 'secondary',
};

interface Props {
  source: string;
  dataKind: string;
  isCurrentConditions?: boolean;
  size?: ChipProps['size'];
}

export default function WeatherProvenanceBadge({
  source,
  dataKind,
  isCurrentConditions = false,
  size = 'small',
}: Props) {
  const { t } = useTranslation();

  // Prefer the explicit "current conditions" label when the record is a live
  // HA reading; otherwise fall back to the data_kind classification.
  const kindKey = isCurrentConditions ? 'observed' : dataKind;

  return (
    <Box sx={{ display: 'inline-flex', gap: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
      <Chip
        label={t(`enums.weatherSource.${source}`, { defaultValue: source })}
        size={size}
        variant="outlined"
        color="default"
      />
      <Tooltip title={t(`enums.weatherDataKindHint.${kindKey}`, { defaultValue: '' })} arrow enterDelay={300}>
        <Chip
          label={t(`enums.weatherDataKind.${kindKey}`, { defaultValue: kindKey })}
          size={size}
          color={DATA_KIND_COLOR[kindKey] ?? 'default'}
          tabIndex={0}
        />
      </Tooltip>
    </Box>
  );
}
