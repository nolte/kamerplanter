/**
 * The trellis hint of a species that needs a support (REQ-053 W-005, §9.5 "Rankhilfe/Spalier", WP 10.10): the
 * trellises drawn in the bed, or that there is none. Information only - it never blocks and never draws a trellis.
 * Shown only when the species profile says `support_required: true` (G-W10 d); an unknown value says nothing.
 */
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import type { BedTrellisState } from './useBedTrellises';

const PREFIX = 'pages.bed.planting.hints.support';

interface SupportHintProps {
  speciesKey: string;
  speciesName: string;
  state: BedTrellisState;
}

export default function SupportHint({ speciesKey, speciesName, state }: SupportHintProps) {
  const { t, i18n } = useTranslation();
  const testId = `planting-support-${speciesKey}`;
  if (state.status === 'idle') return null;
  if (state.status === 'loading') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }} role="status" data-testid={testId} data-state="loading">
        <CircularProgress size={16} />
        <Typography variant="body2">{t(`${PREFIX}.checking`, { name: speciesName })}</Typography>
      </Box>
    );
  }
  if (state.status === 'error') {
    return (
      <Alert severity="info" data-testid={testId} data-state="unavailable">
        {t(`${PREFIX}.unavailable`, { name: speciesName })}
      </Alert>
    );
  }
  const { trellises } = state;
  if (trellises.length === 0) {
    return (
      <Alert severity="warning" data-testid={testId} data-state="missing" data-trellis-count="0">
        {t(`${PREFIX}.missing`, { name: speciesName })}
      </Alert>
    );
  }
  const height = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 });
  return (
    <Alert severity="info" data-testid={testId} data-state="present" data-trellis-count={trellises.length}>
      {t(`${PREFIX}.present`, { name: speciesName, count: trellises.length })}
      <Box component="ul" sx={{ m: 0, pl: 2 }}>
        {trellises.map((trellis) => {
          const name = trellis.label.trim() || t(`${PREFIX}.unnamed`);
          return (
            <li key={trellis.key} data-testid={`planting-support-trellis-${trellis.key}`}>
              {trellis.heightM !== null
                ? t(`${PREFIX}.trellisWithHeight`, { name, height: height.format(trellis.heightM) })
                : name}
            </li>
          );
        })}
      </Box>
    </Alert>
  );
}
