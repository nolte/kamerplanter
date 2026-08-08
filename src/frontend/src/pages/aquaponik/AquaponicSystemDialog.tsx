import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/aquaponik';
import type { AquaponicSystemType, BiofilterType } from '@/api/types';

const fieldWithHelpSx = { display: 'flex', alignItems: 'flex-start', gap: 0.5, flex: 1 } as const;

const systemTypes: AquaponicSystemType[] = [
  'media_bed',
  'dwc',
  'nft',
  'hybrid',
  'wicking_bed',
];
const biofilterTypes: BiofilterType[] = [
  'media_bed_integrated',
  'mbbr',
  'trickle',
  'fluidized_bed',
];

const schema = z
  .object({
    name: z.string().min(1),
    system_type: z.enum(['media_bed', 'dwc', 'nft', 'hybrid', 'wicking_bed']),
    total_volume_liters: z.number().gt(0),
    grow_area_m2: z.number().gt(0),
    biofilter_type: z
      .enum(['media_bed_integrated', 'mbbr', 'trickle', 'fluidized_bed'])
      .nullable(),
    daily_feed_target_g: z.number().min(0),
    ph_target_min: z.number().min(5).max(9),
    ph_target_max: z.number().min(5).max(9),
    notes: z.string().nullable(),
  })
  .refine(
    (data) => data.system_type === 'media_bed' || data.biofilter_type !== null,
    { path: ['biofilter_type'], message: 'biofilterRequired' },
  )
  .refine((data) => data.ph_target_min <= data.ph_target_max, {
    path: ['ph_target_max'],
    message: 'phRange',
  });

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function AquaponicSystemDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const { handleError } = useApiError();

  const defaults: FormData = {
    name: '',
    system_type: 'dwc',
    total_volume_liters: 0,
    grow_area_m2: 0,
    biofilter_type: null,
    daily_feed_target_g: 0,
    ph_target_min: 6.8,
    ph_target_max: 7.2,
    notes: null,
  };

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: defaults });

  const onSubmit = async (data: FormData) => {
    try {
      await api.createSystem({
        name: data.name,
        system_type: data.system_type,
        total_volume_liters: data.total_volume_liters,
        grow_area_m2: data.grow_area_m2,
        biofilter_type: data.biofilter_type,
        daily_feed_target_g: data.daily_feed_target_g,
        ph_target_min: data.ph_target_min,
        ph_target_max: data.ph_target_max,
        notes: data.notes,
      });
      reset(defaults);
      onCreated();
    } catch (error) {
      // No coded field violation to render here; the generic toast is the floor.
      // The widened useApiError contract (#1015) keeps the English `reason` off
      // the German form — a future code is wired via `useFieldViolations`.
      handleError(error);
      notification.error(t('errors.generic'));
    }
  };

  const handleClose = () => {
    reset(defaults);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} fullWidth maxWidth="sm">
      <DialogTitle>{t('pages.aquaponik.createSystem')}</DialogTitle>
      <DialogContent>
        <UnsavedChangesGuard dirty={isDirty} />
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <Typography variant="subtitle1" sx={{ mb: 1.5 }}>
            {t('pages.aquaponik.sectionBasics')}
          </Typography>
          <FormTextField name="name" control={control} label={t('pages.aquaponik.fields.name')} required autoFocus />
          <FormSelectField
            name="system_type"
            control={control}
            label={t('pages.aquaponik.fields.systemType')}
            required
            options={systemTypes.map((v) => ({
              value: v,
              label: t(`enums.aquaponicSystemType.${v}`),
            }))}
          />
          <FormRow>
            <FormNumberField
              name="total_volume_liters"
              control={control}
              label={t('pages.aquaponik.fields.totalVolume')}
              step="any"
              min={0}
              suffix="L"
              required
            />
            <FormNumberField
              name="grow_area_m2"
              control={control}
              label={t('pages.aquaponik.fields.growArea')}
              step="any"
              min={0}
              suffix="m²"
              required
            />
          </FormRow>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
            {t('pages.aquaponik.sectionOperations')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            {t('pages.aquaponik.sectionOperationsIntro')}
          </Typography>
          <FormSelectField
            name="biofilter_type"
            control={control}
            label={t('pages.aquaponik.fields.biofilterType')}
            helperText={t('pages.aquaponik.fields.biofilterHelp')}
            options={biofilterTypes.map((v) => ({
              value: v,
              label: t(`enums.biofilterType.${v}`),
            }))}
          />
          <FormNumberField
            name="daily_feed_target_g"
            control={control}
            label={t('pages.aquaponik.fields.dailyFeedTarget')}
            step="any"
            min={0}
            suffix="g"
          />
          <FormRow>
            <Box sx={fieldWithHelpSx}>
              <FormNumberField
                name="ph_target_min"
                control={control}
                label={t('pages.aquaponik.fields.phTargetMin')}
                step="any"
                min={5}
                max={9}
              />
              <HelpTooltip term="ph" iconOnly />
            </Box>
            <FormNumberField
              name="ph_target_max"
              control={control}
              label={t('pages.aquaponik.fields.phTargetMax')}
              step="any"
              min={5}
              max={9}
            />
          </FormRow>
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.aquaponik.fields.notes')}
            multiline
          />
          <FormActions onCancel={handleClose} loading={isSubmitting} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
