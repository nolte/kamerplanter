/**
 * Change the site conditions of one bed from the bed view (REQ-053 GP-FR-162/163/168, GP-API-010): microclimate,
 * wind, slope, aspect and access sides in a dialog, stored with ONE `PATCH /locations/{key}` that sends only the
 * keys that changed (the server merges them and keeps the legacy `frost_exposed` in step with the frost risk,
 * #2512). Everything is entered by hand; nothing is computed (§29).
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { patchSiteConditions } from './bedApi';
import SiteConditionsFields from './SiteConditionsFields';
import { appliedSitePatch, changedSitePatch, mergeSitePatch } from './siteConditionsPatch';
import type { SiteConditionsPatch, SiteConditionsSlice } from './types';

interface SiteConditionsDialogProps {
  bedKey: string;
  bedName: string;
  /** The stored `site_conditions`; absent = nothing recorded. */
  current?: SiteConditionsSlice | null;
  onClose: () => void;
  /** The conditions were stored; the page reloads its summary. */
  onChanged: () => void;
}

export default function SiteConditionsDialog({ bedKey, bedName, current, onClose, onChanged }: SiteConditionsDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const notification = useNotification();
  const [patch, setPatch] = useState<SiteConditionsPatch>({});
  const [saving, setSaving] = useState(false);
  const [valid, setValid] = useState(true);

  const submit = async () => {
    // An unreadable degrees entry is shown in red under the field; saving waits until it is fixed or cleared.
    if (!valid) {
      notification.warning(t('pages.gardenPlan.siteConditions.dialog.invalid'));
      return;
    }
    const changed = changedSitePatch(current, patch);
    if (Object.keys(changed).length === 0) {
      onClose();
      return;
    }
    setSaving(true);
    try {
      await patchSiteConditions(bedKey, changed);
      notification.success(t('pages.gardenPlan.siteConditions.dialog.saved'));
      onChanged();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
      aria-labelledby="bed-site-title"
      data-testid="bed-site-dialog"
    >
      <DialogTitle id="bed-site-title">{t('pages.gardenPlan.siteConditions.dialog.title', { bed: bedName })}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.gardenPlan.siteConditions.hint')}
        </Typography>
        <SiteConditionsFields
          value={appliedSitePatch(current, patch)}
          onChange={(next) => setPatch((previous) => mergeSitePatch(previous, next))}
          disabled={saving}
          onValidityChange={setValid}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          {t('pages.gardenPlan.siteConditions.dialog.cancel')}
        </Button>
        <Button variant="contained" onClick={() => void submit()} loading={saving} data-testid="bed-site-submit">
          {t('pages.gardenPlan.siteConditions.dialog.save')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
