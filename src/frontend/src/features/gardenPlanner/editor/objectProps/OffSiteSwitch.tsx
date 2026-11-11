/**
 * The switch "Außerhalb des Grundstücks" of a garden object (REQ-053 §9.5, V-03): `off_site` marks scenery outside the
 * garden boundary (the neighbour's house, a tree behind the fence), which is exempt from containment. Switched on it
 * is always valid; switched off, the object must lie inside its area and the boundary again, so the switch refuses
 * that while the shape sticks out and says what to do (the live validation, GP-UX-053; the server stays the
 * authority). One `update_fields`, one undo step.
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import Switch from '@mui/material/Switch';
import type { PlanOperation } from '../../model/types';
import type { ActionLabel } from '../tools/machineTypes';
import { OBJECT_PROPS_PREFIX, TARGET_PX } from './shared';

const PREFIX = `${OBJECT_PROPS_PREFIX}.offSite`;

interface OffSiteSwitchProps {
  objectKey: string;
  offSite: boolean;
  disabled: boolean;
  /** The violation the object would have inside the boundary (`firstViolation` without the exemption), or `null`. */
  violationOnSite: () => string | null;
  onCommit: (ops: PlanOperation[], label: ActionLabel) => void;
}

export function OffSiteSwitch({ objectKey, offSite, disabled, violationOnSite, onCommit }: OffSiteSwitchProps) {
  const { t } = useTranslation();
  const helpId = useId();
  const [refused, setRefused] = useState(false);
  const change = (next: boolean) => {
    if (!next && violationOnSite() !== null) {
      setRefused(true);
      return;
    }
    setRefused(false);
    onCommit(
      [{ op: 'update_fields', entity: 'garden_object', key: objectKey, fields: { off_site: next } }],
      'edit',
    );
  };
  return (
    <Box>
      <FormControlLabel
        control={
          <Switch
            checked={offSite}
            disabled={disabled}
            onChange={(_event, checked) => change(checked)}
            slotProps={{
              input: {
                'aria-describedby': helpId,
                'data-testid': 'garden-plan-panel-off-site-switch',
              } as Record<string, string>,
            }}
          />
        }
        label={t(`${PREFIX}.label`)}
        sx={{ minHeight: TARGET_PX, m: 0 }}
      />
      <FormHelperText
        id={helpId}
        error={refused}
        role={refused ? 'alert' : undefined}
        data-testid={refused ? 'garden-plan-panel-off-site-error' : undefined}
        sx={{ mx: 0 }}
      >
        {t(`${PREFIX}.${refused ? 'refused' : 'help'}`)}
      </FormHelperText>
    </Box>
  );
}
