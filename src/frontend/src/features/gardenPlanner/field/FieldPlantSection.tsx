/**
 * The plants of the bed sheet (REQ-053 §18.1 step 3, 7, 9): species, count and phase per group, the
 * phase colour as a swatch with a black outline (GP-UX-021 - the colour is never the only cue, the
 * phase is also named). "Show plants" opens the single plants with "Correct position" and "Photo".
 * Nothing here deletes or ends a plant: destructive actions stay in planning mode (GP-UX-023).
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import OpenWithIcon from '@mui/icons-material/OpenWith';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { phaseColor } from '../planting/phaseColors';
import type { PlantStateWire } from '../planting/plantStateApi';
import type { FieldPlantGroup } from './fieldPlants';

interface FieldPlantSectionProps {
  /** `null`: the plants could not be read (unknown, not "none"). */
  groups: readonly FieldPlantGroup[] | null;
  canEdit: boolean;
  /** Writes wait while the device is offline. */
  offline: boolean;
  /** The bed is drawn: a position can be corrected on it. */
  canCorrect: boolean;
  onCorrect: (plant: PlantStateWire) => void;
  onPhoto: (plant: PlantStateWire) => void;
}

const SWATCH_PX = 24;

export default function FieldPlantSection({
  groups,
  canEdit,
  offline,
  canCorrect,
  onCorrect,
  onPhoto,
}: FieldPlantSectionProps) {
  const { t } = useTranslation();
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const count = groups?.reduce((sum, group) => sum + group.plants.length, 0) ?? 0;

  return (
    <Box component="section" aria-labelledby="field-plants-heading" data-testid="field-plants">
      <Typography id="field-plants-heading" variant="h6" component="h3" sx={{ mb: 1 }}>
        {t('pages.gardenPlan.field.plants.title', { count })}
      </Typography>
      {groups === null && (
        <Typography variant="body1" data-testid="field-plants-unknown">
          {t('pages.gardenPlan.field.plants.unknown')}
        </Typography>
      )}
      {groups !== null && groups.length === 0 && (
        <Typography variant="body1" data-testid="field-plants-empty">
          {t('pages.gardenPlan.field.plants.empty')}
        </Typography>
      )}
      <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0, display: 'flex', flexDirection: 'column', gap: 1 }}>
        {(groups ?? []).map((group) => {
          const expanded = openGroup === group.id;
          const listId = `field-plant-group-${group.id}-list`;
          return (
            <Box
              component="li"
              key={group.id}
              data-testid={`field-plant-group-${group.id}`}
              sx={{ border: 2, borderColor: 'divider', borderRadius: 1, p: 1.5 }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box
                  aria-hidden="true"
                  sx={{
                    width: SWATCH_PX,
                    height: SWATCH_PX,
                    flexShrink: 0,
                    borderRadius: '50%',
                    bgcolor: group.phaseName ? phaseColor(group.phaseName) : 'background.paper',
                    // GP-UX-021: phase colours get an outline - against sunlight and for colour-blind users.
                    border: 2,
                    borderColor: 'text.primary',
                  }}
                />
                <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                  <Typography variant="body1" sx={{ fontWeight: 700, overflowWrap: 'anywhere' }}>
                    {t('pages.gardenPlan.field.plants.group', {
                      species: group.cultivar ? `${group.species} '${group.cultivar}'` : group.species,
                      count: group.plants.length,
                    })}
                  </Typography>
                  <Typography variant="body1">
                    {group.phaseName
                      ? t('pages.gardenPlan.field.plants.phase', { phase: group.phaseName })
                      : t('pages.gardenPlan.field.plants.noPhase')}
                  </Typography>
                </Box>
                <Button
                  variant="outlined"
                  color="inherit"
                  onClick={() => setOpenGroup(expanded ? null : group.id)}
                  aria-expanded={expanded}
                  aria-controls={listId}
                  sx={{ minHeight: KIOSK_TOUCH_TARGET, minWidth: KIOSK_TOUCH_TARGET, flexShrink: 0, borderWidth: 2 }}
                  data-testid={`field-plant-group-toggle-${group.id}`}
                >
                  {expanded ? t('pages.gardenPlan.field.plants.hide') : t('pages.gardenPlan.field.plants.show')}
                </Button>
              </Box>
              {expanded && (
                <Box
                  component="ul"
                  id={listId}
                  sx={{ listStyle: 'none', p: 0, m: 0, mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}
                >
                  {group.plants.map((plant) => (
                    <Box
                      component="li"
                      key={plant.plant_key}
                      data-testid={`field-plant-${plant.plant_key}`}
                      sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}
                    >
                      <Typography variant="body1" sx={{ flex: '1 1 8rem', fontWeight: 700 }}>
                        {plant.instance_id}
                      </Typography>
                      {canEdit && canCorrect && plant.slot_key && (
                        <Button
                          variant="outlined"
                          color="inherit"
                          startIcon={<OpenWithIcon aria-hidden="true" />}
                          onClick={() => onCorrect(plant)}
                          disabled={offline}
                          sx={{ minHeight: KIOSK_TOUCH_TARGET, borderWidth: 2 }}
                          aria-label={t('pages.gardenPlan.field.plants.correctFor', { plant: plant.instance_id })}
                          data-testid={`field-plant-correct-${plant.plant_key}`}
                        >
                          {t('pages.gardenPlan.field.plants.correct')}
                        </Button>
                      )}
                      {canEdit && (
                        <Button
                          variant="outlined"
                          color="inherit"
                          startIcon={<AddAPhotoIcon aria-hidden="true" />}
                          onClick={() => onPhoto(plant)}
                          disabled={offline}
                          sx={{ minHeight: KIOSK_TOUCH_TARGET, borderWidth: 2 }}
                          aria-label={t('pages.gardenPlan.field.plants.photoFor', { plant: plant.instance_id })}
                          data-testid={`field-plant-photo-${plant.plant_key}`}
                        >
                          {t('pages.gardenPlan.field.plants.photo')}
                        </Button>
                      )}
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
