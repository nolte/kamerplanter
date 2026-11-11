/**
 * The object-specific fields of a garden object in the tab "Eigenschaften" (REQ-053 GP-FR-180, §9.5 / §9.8, WP 10.6):
 * per class exactly what its backend props model carries - window (sill height, glazing, derived orientation
 * read-only), door (swing), lamp (kind, height, reference PPFD), trellis (height); furniture has no props of its own -
 * and for every object the switch "outside the property" (`off_site`). The water source keeps its own section
 * (`WaterSourceFields`, WP 9.14). Every change is one `update_fields` through the pending plan model.
 */
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { GardenObject, PlanOperation } from '../../model/types';
import type { ActionLabel } from '../tools/machineTypes';
import { DoorFields } from './DoorFields';
import { LampFields } from './LampFields';
import { OffSiteSwitch } from './OffSiteSwitch';
import { OBJECT_PROPS_PREFIX } from './shared';
import { TrellisFields } from './TrellisFields';
import { WindowFields } from './WindowFields';

interface ObjectPropsFieldsProps {
  object: GardenObject;
  disabled: boolean;
  /** See `OffSiteSwitch.violationOnSite`. */
  violationOnSite: () => string | null;
  /** The window's derived orientation as text, `null` while none is derived (GP-FR-181). */
  windowOrientation?: string | null;
  /** The window's outside was taken from the drawing direction, not from the outline (GP-FR-181). */
  windowOrientationByConvention?: boolean;
  onCommit: (ops: PlanOperation[], label: ActionLabel) => void;
}

export function ObjectPropsFields({
  object,
  disabled,
  violationOnSite,
  windowOrientation = null,
  windowOrientationByConvention = false,
  onCommit,
}: ObjectPropsFieldsProps) {
  const { t } = useTranslation();
  const props = object.props;
  const common = { objectKey: object.key, disabled, onCommit };
  let fields: ReactNode;
  switch (props.object_type) {
    case 'window':
      fields = (
        <WindowFields
          {...common}
          props={props}
          orientation={windowOrientation}
          orientationByConvention={windowOrientationByConvention}
        />
      );
      break;
    case 'door':
      fields = <DoorFields {...common} props={props} />;
      break;
    case 'lamp':
      fields = <LampFields {...common} props={props} />;
      break;
    case 'trellis':
      fields = <TrellisFields {...common} props={props} />;
      break;
    case 'furniture':
      fields = (
        <Typography variant="body2" color="text.secondary" data-testid="garden-plan-panel-furniture-note">
          {t(`${OBJECT_PROPS_PREFIX}.furniture.note`)}
        </Typography>
      );
      break;
    default:
      fields = null;
  }
  const titleId = `garden-plan-panel-object-props-title-${object.key}`;
  return (
    <Box
      component="section"
      aria-labelledby={titleId}
      data-testid="garden-plan-panel-object-props"
      data-object-type={object.object_type}
      sx={{ display: 'grid', gap: 1.5 }}
    >
      <Typography variant="subtitle2" component="h4" id={titleId}>
        {t(`${OBJECT_PROPS_PREFIX}.title`)}
      </Typography>
      {fields}
      <OffSiteSwitch
        objectKey={object.key}
        offSite={object.off_site}
        disabled={disabled}
        violationOnSite={violationOnSite}
        onCommit={onCommit}
      />
    </Box>
  );
}
