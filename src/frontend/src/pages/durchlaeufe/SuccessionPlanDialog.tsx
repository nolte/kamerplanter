import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormDateField from '@/components/form/FormDateField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import SpeciesAutocompleteField from '@/components/form/SpeciesAutocompleteField';
import LocationTreeSelect from '@/components/form/LocationTreeSelect';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as successionApi from '@/api/endpoints/successionPlans';
import * as speciesApi from '@/api/endpoints/species';
import * as sitesApi from '@/api/endpoints/sites';
import type {
  Cultivar,
  Site,
  Species,
  SuccessionPlan,
} from '@/api/types';

const schema = z.object({
  name: z.string().min(1).max(200),
  species_key: z.string().min(1),
  cultivar_key: z.string().nullable().optional(),
  interval_days: z.number().int().min(1),
  start_date: z.string().min(1),
  end_date: z.string().min(1),
  plants_per_batch: z.number().int().min(1),
  reminder_days_before: z.number().int().min(0),
  site_key: z.string().nullable().optional(),
  location_key: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  /** When provided, the dialog operates in edit mode. */
  plan?: SuccessionPlan | null;
}

/** Derives how many staggered batches the schedule produces (client-side preview). */
function estimateBatches(
  startDate: string,
  endDate: string,
  intervalDays: number,
): number {
  if (!startDate || !endDate || !intervalDays || intervalDays < 1) return 0;
  const start = new Date(startDate);
  const end = new Date(endDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
  if (end < start) return 0;
  const spanDays = Math.floor((end.getTime() - start.getTime()) / 86_400_000);
  return Math.floor(spanDays / intervalDays) + 1;
}

function defaultsFor(plan?: SuccessionPlan | null): FormData {
  const today = new Date().toISOString().split('T')[0];
  return {
    name: plan?.name ?? '',
    species_key: plan?.species_key ?? '',
    cultivar_key: plan?.cultivar_key ?? null,
    interval_days: plan?.interval_days ?? 21,
    start_date: plan?.start_date ?? today,
    end_date: plan?.end_date ?? today,
    plants_per_batch: plan?.plants_per_batch ?? 1,
    reminder_days_before: plan?.reminder_days_before ?? 3,
    site_key: null,
    location_key: plan?.location_key ?? null,
    notes: plan?.notes ?? null,
  };
}

export default function SuccessionPlanDialog({ open, onClose, onSaved, plan }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [sitesList, setSitesList] = useState<Site[]>([]);
  const [cultivarList, setCultivarList] = useState<Cultivar[]>([]);

  const isEdit = Boolean(plan);

  const { control, handleSubmit, reset, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: defaultsFor(plan),
  });

  const speciesKey = useWatch({ control, name: 'species_key' });
  const siteKey = useWatch({ control, name: 'site_key' });
  const startDate = useWatch({ control, name: 'start_date' });
  const endDate = useWatch({ control, name: 'end_date' });
  const intervalDays = useWatch({ control, name: 'interval_days' });

  const previewBatches = useMemo(
    () => estimateBatches(startDate, endDate, Number(intervalDays)),
    [startDate, endDate, intervalDays],
  );

  const invalidRange = useMemo(
    () => Boolean(startDate && endDate && endDate < startDate),
    [startDate, endDate],
  );

  useEffect(() => {
    if (open) {
      reset(defaultsFor(plan));
      speciesApi
        .listSpecies(0, 200)
        .then((r) => setSpeciesList(r.items))
        .catch(() => {});
      sitesApi
        .listSites(0, 200)
        .then(setSitesList)
        .catch(() => {});
    }
  }, [open, plan, reset]);

  // Load cultivars whenever the selected species changes.
  useEffect(() => {
    if (!speciesKey) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reset cultivars when species cleared
      setCultivarList([]);
      return;
    }
    speciesApi
      .listCultivars(speciesKey)
      .then(setCultivarList)
      .catch(() => setCultivarList([]));
  }, [speciesKey]);

  useEffect(() => {
    if (!siteKey) {
      setValue('location_key', null);
    }
  }, [siteKey, setValue]);

  const onSubmit = async (data: FormData) => {
    if (data.end_date < data.start_date) {
      notification.error(t('pages.successionPlans.endBeforeStart'));
      return;
    }
    try {
      setSaving(true);
      if (isEdit && plan) {
        await successionApi.updateSuccessionPlan(plan.key, {
          name: data.name,
          cultivar_key: data.cultivar_key || null,
          interval_days: data.interval_days,
          start_date: data.start_date,
          end_date: data.end_date,
          plants_per_batch: data.plants_per_batch,
          reminder_days_before: data.reminder_days_before,
          location_key: data.location_key || null,
          notes: data.notes || null,
        });
        notification.success(t('pages.successionPlans.planUpdated'));
      } else {
        await successionApi.createSuccessionPlan({
          name: data.name,
          species_key: data.species_key,
          cultivar_key: data.cultivar_key || null,
          interval_days: data.interval_days,
          start_date: data.start_date,
          end_date: data.end_date,
          plants_per_batch: data.plants_per_batch,
          reminder_days_before: data.reminder_days_before,
          location_key: data.location_key || null,
          notes: data.notes || null,
        });
        notification.success(t('pages.successionPlans.planCreated'));
      }
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="succession-plan-dialog-title"
      data-testid="succession-plan-dialog"
    >
      <DialogTitle id="succession-plan-dialog-title">
        {isEdit
          ? t('pages.successionPlans.editTitle')
          : t('pages.successionPlans.createTitle')}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.successionPlans.intro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.successionPlans.sectionCulture')}
          </Typography>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.successionPlans.name')}
            required
            autoFocus
          />
          <SpeciesAutocompleteField
            name="species_key"
            control={control}
            label={t('entities.species')}
            species={speciesList}
            required
            disabled={isEdit}
            helperText={
              isEdit
                ? t('pages.successionPlans.speciesLockedHelper')
                : undefined
            }
          />
          <FormSelectField
            name="cultivar_key"
            control={control}
            label={t('entities.cultivar')}
            disabled={!speciesKey}
            options={[
              { value: '', label: '—' },
              ...cultivarList.map((c) => ({ value: c.key, label: c.name })),
            ]}
          />
          <FormNumberField
            name="plants_per_batch"
            control={control}
            label={t('pages.successionPlans.plantsPerBatch')}
            min={1}
            step={1}
            helperText={t('pages.successionPlans.plantsPerBatchHelper')}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5, mt: 2 }}>
            {t('pages.successionPlans.sectionSchedule')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            {t('pages.successionPlans.sectionScheduleIntro')}
          </Typography>
          <FormNumberField
            name="interval_days"
            control={control}
            label={t('pages.successionPlans.intervalDays')}
            min={1}
            step={1}
            suffix={t('pages.successionPlans.daysSuffix')}
            helperText={t('pages.successionPlans.intervalDaysHelper')}
          />
          <FormRow>
            <FormDateField
              name="start_date"
              control={control}
              label={t('pages.successionPlans.startDate')}
              required
            />
            <FormDateField
              name="end_date"
              control={control}
              label={t('pages.successionPlans.endDate')}
              required
              error={invalidRange}
              helperText={invalidRange ? t('pages.successionPlans.endBeforeStart') : undefined}
            />
          </FormRow>
          <FormNumberField
            name="reminder_days_before"
            control={control}
            label={t('pages.successionPlans.reminderDaysBefore')}
            min={0}
            step={1}
            suffix={t('pages.successionPlans.daysSuffix')}
            helperText={t('pages.successionPlans.reminderDaysBeforeHelper')}
          />

          <Alert
            severity={invalidRange ? 'error' : 'info'}
            sx={{ mt: 1, mb: 2 }}
            data-testid="batch-preview"
          >
            <AlertTitle>{t('pages.successionPlans.previewTitle')}</AlertTitle>
            <Box>
              {invalidRange
                ? t('pages.successionPlans.endBeforeStart')
                : t('pages.successionPlans.previewBatches', {
                    count: previewBatches,
                  })}
            </Box>
          </Alert>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.successionPlans.sectionLocation')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="site_key"
              control={control}
              label={t('entities.site')}
              options={[
                { value: '', label: '—' },
                ...sitesList.map((s) => ({ value: s.key, label: s.name })),
              ]}
            />
            <LocationTreeSelect
              name="location_key"
              control={control}
              siteKey={siteKey}
              label={t('pages.successionPlans.location')}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.successionPlans.sectionNotes')}
          </Typography>
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.successionPlans.notes')}
            multiline
            minRows={2}
            maxRows={4}
          />

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            * {t('common.required')}
          </Typography>

          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={isEdit ? t('common.save') : t('common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
