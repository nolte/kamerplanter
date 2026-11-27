/**
 * What the app proposes after a soil-borne loss (REQ-053 §11.3a Nr. 5, #2888 F-20), from `soil_hazard_follow_up` of
 * the remove answer:
 *
 * - `offer`: the loss names a confirmed pathogen from the list. The app asks whether the bed takes it over as a soil
 *   hazard; only "Ins Beet übernehmen" writes it (`POST /locations/{key}/soil-hazards` with the plant key - pathogen,
 *   date and source come from the stored loss, so an unconfirmed loss cannot become an entry through this dialog).
 * - `clean_system`: a hydroponic location has no soil - the hint to clean and disinfect the system before replanting.
 *
 * Nothing is written silently: closing the offer keeps the bed as it is.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { formatDate } from '@/utils/formatting';
import { takeOverLossAsSoilHazard } from './soilHazardApi';
import type { SoilHazardFollowUp } from './soilHazardTypes';

const PREFIX = 'pages.bed.soilHazards.followUp';

interface SoilHazardFollowUpDialogProps {
  followUp: SoilHazardFollowUp;
  plantKey: string;
  plantName: string;
  onClose: () => void;
}

export default function SoilHazardFollowUpDialog({ followUp, plantKey, plantName, onClose }: SoilHazardFollowUpDialogProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  const [saving, setSaving] = useState(false);

  if (followUp.kind === 'clean_system') {
    return (
      <Dialog
        open
        onClose={onClose}
        maxWidth="sm"
        fullWidth
        aria-labelledby="soil-hazard-clean-system-title"
        aria-describedby="soil-hazard-clean-system-text"
        data-testid="soil-hazard-clean-system-dialog"
      >
        <DialogTitle id="soil-hazard-clean-system-title">{t(`${PREFIX}.cleanTitle`)}</DialogTitle>
        <DialogContent>
          <DialogContentText id="soil-hazard-clean-system-text">
            {t(`${PREFIX}.cleanMessage`, { plant: plantName })}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={onClose} sx={{ minHeight: 48 }} autoFocus data-testid="soil-hazard-clean-system-ok">
            {t(`${PREFIX}.cleanOk`)}
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  const hazard = followUp.hazard ? t(`enums.soilHazard.${followUp.hazard}`) : '';
  const accept = async () => {
    if (saving) return;
    setSaving(true);
    try {
      const result = await takeOverLossAsSoilHazard(followUp.location_key, plantKey);
      if (result.changed) {
        notification.success(t(`${PREFIX}.accepted`, { hazard }));
      } else {
        // Nothing written (review D3): the bed meanwhile carries the hazard with this or a later date.
        notification.info(t('pages.bed.soilHazards.unchanged', { hazard }));
      }
      onClose();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <ConfirmDialog
      open
      title={t(`${PREFIX}.offerTitle`)}
      message={t(`${PREFIX}.offerMessage`, {
        plant: plantName,
        hazard,
        source: followUp.source ? t(`enums.pathogenConfirmationSource.${followUp.source}`) : '',
        date: formatDate(followUp.confirmed_at ?? null),
      })}
      confirmLabel={t(`${PREFIX}.offerConfirm`)}
      onConfirm={() => void accept()}
      onCancel={onClose}
      loading={saving}
      requiresConnectivity
    />
  );
}
