import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { formatDateTime } from '@/utils/formatting';
import type { DiaryEnvironmentReading } from '@/api/types';

interface DiaryEnvironmentReadingsProps {
  readings: DiaryEnvironmentReading[];
  /** Test-id prefix, so the dialog preview and the entry card stay addressable apart. */
  testIdPrefix: string;
}

/**
 * REQ-013 §2.3a — the machine-read values of an environment snapshot, read-only.
 *
 * Shared by the create dialog's preview and the stored entry's card, so the
 * grower sees the same rendering before and after saving and cannot be surprised
 * by what landed in the record.
 *
 * **Nothing here is editable, on purpose.** A corrected sensor reading is a
 * manual measurement and belongs in the `measurements` editor above it — offering
 * a pencil here would produce a value that looks automatic and is not, which is
 * the exact confusion the two separate fields exist to prevent.
 *
 * Every value shows *when* it was measured and *where it came from*, because a
 * bare "22 °C" on an entry is unreadable a year later: the reader has to be able
 * to tell a probe in the plant's own tent from a site-wide weather service.
 */
export default function DiaryEnvironmentReadings({
  readings,
  testIdPrefix,
}: DiaryEnvironmentReadingsProps) {
  const { t } = useTranslation();

  const rows = useMemo(
    () =>
      readings.map((reading) => ({
        reading,
        // The translated metric label where the vocabulary knows it; the raw
        // `metric_type` otherwise. The vocabulary is open (REQ-005 §2), so an
        // imported metric must still be displayable rather than blank.
        label: t([`enums.sensorMetricType.${reading.metric_type}`, reading.metric_type]),
      })),
    [readings, t],
  );

  return (
    <Box
      sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
      data-testid={`${testIdPrefix}-readings`}
    >
      {rows.map(({ reading, label }) => (
        <Box
          key={`${reading.metric_type}-${reading.sensor_key ?? reading.origin}`}
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'baseline',
            columnGap: 1,
            rowGap: 0.25,
          }}
          data-testid={`${testIdPrefix}-row-${reading.metric_type}`}
        >
          <Typography variant="body2" color="text.secondary" sx={{ minWidth: 0 }}>
            {label}
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {reading.unit ? `${reading.value} ${reading.unit}` : String(reading.value)}
          </Typography>
          <Tooltip title={t(`pages.plantDiary.environment.originHint.${reading.origin}`)}>
            <Chip
              size="small"
              variant="outlined"
              label={t(`pages.plantDiary.environment.origin.${reading.origin}`)}
              data-testid={`${testIdPrefix}-origin-${reading.metric_type}`}
            />
          </Tooltip>
          <Typography variant="caption" color="text.secondary">
            {t('pages.plantDiary.environment.measuredAt', {
              time: formatDateTime(reading.measured_at),
              source: reading.source,
            })}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}
