import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Stack from '@mui/material/Stack';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Tooltip from '@mui/material/Tooltip';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import type { DiagnosisSymptom } from '@/api/types';

export interface SymptomPickerProps {
  /** The catalogue to choose from (already filtered by phase server-side). */
  symptoms: DiagnosisSymptom[];
  /** Currently selected symptom slugs. */
  selected: string[];
  /** Toggle callback for a single slug. */
  onToggle: (slug: string) => void;
}

/**
 * REQ-036 §5 — the wizard's symptom selection step.
 *
 * Groups the curated catalogue by category (each category translated via the
 * `diagnose.categories.*` namespace) and offers accessible checkboxes with a
 * cause-hint tooltip.
 */
export default function SymptomPicker({ symptoms, selected, onToggle }: SymptomPickerProps) {
  const { t } = useTranslation();

  const grouped = useMemo(() => {
    const byCategory = new Map<string, DiagnosisSymptom[]>();
    for (const symptom of symptoms) {
      const bucket = byCategory.get(symptom.category) ?? [];
      bucket.push(symptom);
      byCategory.set(symptom.category, bucket);
    }
    return Array.from(byCategory.entries());
  }, [symptoms]);

  const selectedSet = useMemo(() => new Set(selected), [selected]);

  return (
    <Box data-testid="symptom-picker">
      {grouped.map(([category, entries]) => (
        <Box key={category} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            {t(`diagnose.categories.${category}`, category)}
          </Typography>
          <FormGroup>
            {entries.map((symptom) => (
              // The cause-hint trigger is a sibling of FormControlLabel, not
              // nested inside its `label`: a descendant of a native <label>
              // forwards its click to the wrapped checkbox, so an icon placed
              // inside the label would toggle the symptom every time a user
              // taps it just to read the tooltip. Keeping it outside avoids
              // that trap entirely instead of fighting it with stopPropagation.
              <Stack
                key={symptom.slug}
                direction="row"
                sx={{ alignItems: 'center', minHeight: { xs: 48, sm: 40 } }}
              >
                <FormControlLabel
                  sx={{ flexGrow: 1, mr: 0 }}
                  control={
                    <Checkbox
                      checked={selectedSet.has(symptom.slug)}
                      onChange={() => onToggle(symptom.slug)}
                      slotProps={{ input: { 'aria-label': symptom.label } }}
                      data-testid={`symptom-${symptom.slug}`}
                    />
                  }
                  label={symptom.label}
                />
                {symptom.common_causes_hint ? (
                  <Tooltip title={symptom.common_causes_hint} enterTouchDelay={0} leaveTouchDelay={4000}>
                    <Box
                      component="span"
                      tabIndex={0}
                      aria-label={t('diagnose.symptoms.causeHintLabel', { label: symptom.label })}
                      data-testid={`symptom-hint-${symptom.slug}`}
                      sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minWidth: { xs: 48, sm: 40 },
                        minHeight: { xs: 48, sm: 40 },
                        cursor: 'help',
                      }}
                    >
                      <InfoOutlinedIcon fontSize="small" color="disabled" />
                    </Box>
                  </Tooltip>
                ) : null}
              </Stack>
            ))}
          </FormGroup>
        </Box>
      ))}
    </Box>
  );
}
