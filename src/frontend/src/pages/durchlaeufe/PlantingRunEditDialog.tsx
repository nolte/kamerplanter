import { useEffect, useRef, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormDateField from '@/components/form/FormDateField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import LocationTreeSelect from '@/components/form/LocationTreeSelect';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as runApi from '@/api/endpoints/plantingRuns';
import * as siteApi from '@/api/endpoints/sites';
import type { PlantingRun, Site } from '@/api/types';

const editSchema = z.object({
  name: z.string().min(1).max(200),
  site_key: z.string().nullable(),
  location_key: z.string().nullable(),
  notes: z.string().nullable(),
  planned_start_date: z.string().nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

interface PlantingRunEditDialogProps {
  open: boolean;
  run: PlantingRun;
  sitesList: Site[];
  initialSiteKey: string | null;
  onClose: () => void;
  onSaved: (updated: PlantingRun) => void;
}

export default function PlantingRunEditDialog({
  open,
  run,
  sitesList,
  initialSiteKey,
  onClose,
  onSaved,
}: PlantingRunEditDialogProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    setValue,
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: { name: '', site_key: null, location_key: null, notes: null, planned_start_date: null },
  });

  const editSiteKey = useWatch({ control, name: 'site_key' });

  // Reset form values when dialog opens or run changes
  useEffect(() => {
    if (open) {
      skipLocationReset.current = true;
      reset({
        name: run.name,
        site_key: initialSiteKey,
        location_key: run.location_key ?? null,
        notes: run.notes ?? null,
        planned_start_date: run.planned_start_date ?? null,
      });
    }
  }, [open, run, initialSiteKey, reset]);

  // Clear location when site changes (except initial load)
  const skipLocationReset = useRef(true);
  useEffect(() => {
    if (skipLocationReset.current) {
      skipLocationReset.current = false;
      return;
    }
    if (!editSiteKey) {
      setValue('location_key', null);
    }
  }, [editSiteKey, setValue]);

  const onSubmit = async (data: EditFormData) => {
    try {
      setSaving(true);
      const updated = await runApi.updatePlantingRun(run.key, {
        name: data.name,
        location_key: data.location_key,
        notes: data.notes,
        planned_start_date: data.planned_start_date,
      });
      notification.success(t('common.saved'));
      onSaved(updated);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      data-testid="planting-run-edit-dialog"
    >
      <DialogTitle>{t('pages.plantingRuns.editTitle')}</DialogTitle>
      <DialogContent>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.plantingRuns.editDesc')}
          </Typography>

          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.plantingRuns.editTitle')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.plantingRuns.editSectionDesc')}
              </Typography>
              <FormRow>
                <FormTextField
                  name="name"
                  control={control}
                  label={t('pages.plantingRuns.name')}
                  required
                  autoFocus
                />
                <FormDateField
                  name="planned_start_date"
                  control={control}
                  label={t('pages.plantingRuns.plannedStartDate')}
                />
              </FormRow>
              <FormRow>
                <FormSelectField
                  name="site_key"
                  control={control}
                  label={t('entities.site')}
                  options={[
                    { value: '', label: '\u2014' },
                    ...sitesList.map((s) => ({ value: s.key, label: s.name })),
                  ]}
                />
                <LocationTreeSelect
                  name="location_key"
                  control={control}
                  siteKey={editSiteKey}
                  label={t('pages.plantingRuns.location')}
                />
              </FormRow>
              <FormTextField
                name="notes"
                control={control}
                label={t('pages.plantingRuns.notes')}
                multiline
                minRows={3}
              />
            </CardContent>
          </Card>

          <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
          <FormActions onCancel={onClose} loading={saving} />
        </Box>
      </DialogContent>
    </Dialog>
  );
}

// Re-export helpers for sibling components that need site resolution
export async function resolveSiteKeyFromLocation(locationKey: string): Promise<string | null> {
  try {
    const loc = await siteApi.getLocation(locationKey);
    return loc.site_key;
  } catch {
    return null;
  }
}
