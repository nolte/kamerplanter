/**
 * The field of a trellis (REQ-053 §9.5, GP-FR-180): its height - what `TrellisProps` carries. The height is required
 * in the model (the planting dialog offers trellises by it, W-005), so the field cannot be emptied.
 */
import { useTranslation } from 'react-i18next';
import type { TrellisProps } from '../../model/types';
import { MAX_HEIGHT_M, MIN_HEIGHT_M } from './limits';
import { PropNumberField } from './PropNumberField';
import { formatBound, OBJECT_PROPS_PREFIX, type ObjectFieldsProps } from './shared';
import { useCommitProps } from './useCommitProps';

export function TrellisFields(fields: ObjectFieldsProps<TrellisProps>) {
  const { t, i18n } = useTranslation();
  const commit = useCommitProps(fields);
  return (
    <PropNumberField
      label={t(`${OBJECT_PROPS_PREFIX}.trellis.height`)}
      value={fields.props.height_m}
      unit="m"
      min={MIN_HEIGHT_M}
      max={MAX_HEIGHT_M}
      required
      disabled={fields.disabled}
      helperText={t(`${OBJECT_PROPS_PREFIX}.trellis.heightHelp`)}
      invalidText={t(`${OBJECT_PROPS_PREFIX}.heightRequiredInvalid`, {
        min: formatBound(MIN_HEIGHT_M, i18n.language),
        max: formatBound(MAX_HEIGHT_M, i18n.language),
      })}
      testId="garden-plan-panel-trellis-height"
      onCommit={(value) => {
        if (value !== null) commit({ height_m: value });
      }}
    />
  );
}
