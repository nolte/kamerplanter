/**
 * The plant info on touch (REQ-053 GP-FR-190, GP-UX-040): a bottom sheet instead of a hover bubble. Loaded
 * on the first tap only. The cover photo is part of the sheet, not of the hover bubble: showing it needs the
 * image, and hovering must not request anything (GP-FR-191).
 */
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import Typography from '@mui/material/Typography';
import AuthImage from '@/components/common/AuthImage';
import { diaryPhotoUri } from '@/api/endpoints/diary';
import { plantDetailPath, PlantInfoContent } from './PlantInfoPopover';
import { usePlantStateText } from './usePlantStateText';
import type { PlantStateView } from './usePlantStates';

interface PlantInfoSheetProps {
  view: PlantStateView | null;
  onClose: () => void;
}

export default function PlantInfoSheet({ view, onClose }: PlantInfoSheetProps) {
  const { t } = useTranslation();
  const text = usePlantStateText();
  const name = view ? text.name(view) : '';
  return (
    <Drawer
      anchor="bottom"
      open={view !== null}
      onClose={onClose}
      data-testid="plant-info-sheet"
      slotProps={{ paper: { sx: { maxHeight: '85vh' } } }}
    >
      {view ? (
        <Box
          role="region"
          aria-label={t('pages.gardenPlan.plantState.info.sheetTitle', { name })}
          sx={{
            p: 2,
            pb: 'calc(24px + env(safe-area-inset-bottom, 0px))',
            overflowY: 'auto',
            display: 'flex', flexDirection: 'column',
            gap: 1.5,
          }}
        >
          <Typography variant="overline" color="text.secondary" component="h2">
            {text.lifecycle(view.visual.lifecycle)}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
            {view.cover_photo_ref ? (
              <AuthImage
                uri={diaryPhotoUri(view.cover_photo_ref, 128)}
                alt={t('pages.gardenPlan.plantState.info.photo', { name })}
                width={96}
                height={96}
                sx={{ borderRadius: 1, flex: '0 0 auto' }}
              />
            ) : null}
            <Box sx={{ minWidth: 0, flex: '1 1 auto' }}>
              <PlantInfoContent view={view} />
            </Box>
          </Box>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'flex-end' }}>
            <Button component={RouterLink} to={plantDetailPath(view.plant_key)} sx={{ minHeight: 44, minWidth: 44 }}>
              {t('pages.gardenPlan.plantState.info.details')}
            </Button>
            <Button onClick={onClose} variant="contained" sx={{ minHeight: 44, minWidth: 44 }} autoFocus>
              {t('pages.gardenPlan.plantState.info.close')}
            </Button>
          </Box>
        </Box>
      ) : null}
    </Drawer>
  );
}
