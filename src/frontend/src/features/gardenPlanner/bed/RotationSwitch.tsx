/**
 * "Crop rotation for this bed" (REQ-053 GP-FR-137, #2544): the bed's own switch of the rotation check
 * (`rotation_enabled`: default of the bed type / on / off) and the permanent-crop flag (`rotation_exempt`), written
 * through the existing `PATCH /locations/{key}`. Both at once - exempt and switched on - is refused by the server
 * (422 `patch.rotation_exempt_and_enabled`); the refusal is shown here in words, the stored state stays. A viewer
 * sees the state read-only.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { getFieldViolations } from '@/api/errors';
import { useApiError } from '@/hooks/useApiError';
import PlannerGlossary from '../glossary/PlannerGlossary';
import { patchRotationSwitch } from './bedApi';

const BOTH_TRUE = 'patch.rotation_exempt_and_enabled';

type SwitchValue = 'default' | 'on' | 'off';

function toValue(enabled: boolean | null | undefined): SwitchValue {
  if (enabled === true) return 'on';
  if (enabled === false) return 'off';
  return 'default';
}

function fromValue(value: SwitchValue): boolean | null {
  if (value === 'on') return true;
  if (value === 'off') return false;
  return null;
}

interface RotationSwitchProps {
  bedKey: string;
  rotationEnabled: boolean | null | undefined;
  rotationExempt: boolean | undefined;
  canEdit: boolean;
  /** The server stored the change; the page reloads its summary. */
  onSaved: () => void | Promise<void>;
}

export default function RotationSwitch({ bedKey, rotationEnabled, rotationExempt, canEdit, onSaved }: RotationSwitchProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [refusal, setRefusal] = useState(false);
  const [saved, setSaved] = useState(false);
  const exempt = rotationExempt === true;

  const save = async (change: { rotationEnabled?: boolean | null; rotationExempt?: boolean }) => {
    // Controls stay enabled while saving (a disabled control drops keyboard focus); a second change waits.
    if (saving) return;
    setSaving(true);
    setRefusal(false);
    setSaved(false);
    try {
      await patchRotationSwitch(bedKey, change);
      await onSaved();
      setSaved(true);
    } catch (error) {
      if (getFieldViolations(error).some((violation) => violation.code === BOTH_TRUE)) {
        setRefusal(true);
      } else {
        handleError(error);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box
      component="section"
      aria-labelledby="rotation-switch-title"
      data-testid="rotation-switch"
      aria-busy={saving}
      sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mb: 3 }}
    >
      <Typography id="rotation-switch-title" variant="h6" component="h2">
        {t('pages.bed.soil.rotation.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {canEdit ? t('pages.bed.soil.rotation.intro') : t('pages.bed.soil.rotation.introReadOnly')}
      </Typography>
      <PlannerGlossary id="rotation-switch" terms={['fruchtfolge', 'dauerkultur']} />

      <Box role="status" aria-live="polite" sx={{ minHeight: saving || saved ? undefined : 0 }}>
        {saving && (
          <Typography variant="caption" color="text.secondary" data-testid="rotation-switch-saving">
            {t('pages.bed.soil.rotation.saving')}
          </Typography>
        )}
        {saved && !saving && !refusal && (
          <Typography variant="caption" color="text.secondary" data-testid="rotation-switch-saved">
            {t('pages.bed.soil.rotation.saved')}
          </Typography>
        )}
      </Box>

      {refusal && (
        <Alert severity="error" onClose={() => setRefusal(false)} data-testid="rotation-switch-refusal">
          {t('pages.bed.soil.rotation.bothRefused')}
        </Alert>
      )}

      <FormControl disabled={!canEdit}>
        <FormLabel id="rotation-enabled-label">{t('pages.bed.soil.rotation.checkLabel')}</FormLabel>
        <RadioGroup
          aria-labelledby="rotation-enabled-label"
          aria-describedby="rotation-enabled-helper"
          value={toValue(rotationEnabled)}
          onChange={(event) => void save({ rotationEnabled: fromValue(event.target.value as SwitchValue) })}
          data-testid="rotation-enabled-group"
        >
          {(['default', 'on', 'off'] as const).map((value) => (
            <FormControlLabel
              key={value}
              value={value}
              control={<Radio />}
              label={t(`pages.bed.soil.rotation.check.${value}`)}
              sx={{ minHeight: 44 }}
              data-testid={`rotation-enabled-${value}`}
            />
          ))}
        </RadioGroup>
        <FormHelperText id="rotation-enabled-helper">{t('pages.bed.soil.rotation.checkHelper')}</FormHelperText>
      </FormControl>

      <FormControl disabled={!canEdit}>
        <FormControlLabel
          control={
            <Switch
              checked={exempt}
              onChange={(event) => void save({ rotationExempt: event.target.checked })}
              slotProps={{ input: { 'data-testid': 'rotation-exempt-switch', 'aria-describedby': 'rotation-exempt-helper' } as never }}
            />
          }
          label={t('pages.bed.soil.rotation.exemptLabel')}
          sx={{ minHeight: 44 }}
        />
        <FormHelperText id="rotation-exempt-helper">{t('pages.bed.soil.rotation.exemptHelper')}</FormHelperText>
      </FormControl>
    </Box>
  );
}
