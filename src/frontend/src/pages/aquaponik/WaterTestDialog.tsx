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
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormTextField from '@/components/form/FormTextField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/aquaponik';
import type { WaterTestSource } from '@/api/types';

// UI-NFR-008 R-042/R-046: fields with fachbegriffe (Ammoniak/TAN, Nitrit,
// Nitrat, pH, Karbonathärte, Gelöstsauerstoff) get a HelpTooltip next to
// them; this keeps the field and its info icon visually as one unit.
const fieldWithHelpSx = { display: 'flex', alignItems: 'flex-start', gap: 0.5, flex: 1 } as const;

const sources: WaterTestSource[] = ['manual', 'sensor', 'test_kit'];

const schema = z.object({
  ph: z.number().min(0).max(14),
  ammonia_tan_mgl: z.number().min(0),
  nitrite_mgl: z.number().min(0),
  nitrate_mgl: z.number().min(0),
  temperature_c: z.number().min(0).max(45),
  dissolved_oxygen_mgl: z.number().min(0).nullable(),
  kh_dh: z.number().min(0).nullable(),
  iron_ppm: z.number().min(0).nullable(),
  source: z.enum(['manual', 'sensor', 'test_kit']),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  systemKey: string;
  onClose: () => void;
  onRecorded: () => void;
}

export default function WaterTestDialog({ open, systemKey, onClose, onRecorded }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();

  const defaults: FormData = {
    ph: 7.0,
    ammonia_tan_mgl: 0,
    nitrite_mgl: 0,
    nitrate_mgl: 0,
    temperature_c: 24,
    dissolved_oxygen_mgl: null,
    kh_dh: null,
    iron_ppm: null,
    source: 'test_kit',
    notes: null,
  };

  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { isDirty, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: defaults });

  const onSubmit = async (data: FormData) => {
    try {
      await api.recordWaterTest(systemKey, data);
      reset(defaults);
      onRecorded();
    } catch (error) {
      handleError(error, (name, message) =>
        setError(name as keyof FormData, { message }),
      );
    }
  };

  const handleClose = () => {
    reset(defaults);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} fullWidth maxWidth="sm">
      <DialogTitle>{t('pages.aquaponik.recordWaterTest')}</DialogTitle>
      <DialogContent>
        <UnsavedChangesGuard dirty={isDirty} />
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
            {t('pages.aquaponik.sectionNitrogenCycle')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            {t('pages.aquaponik.sectionNitrogenCycleIntro')}
          </Typography>
          <FormRow>
            <Box sx={fieldWithHelpSx}>
              <FormNumberField name="ammonia_tan_mgl" control={control} label={t('pages.aquaponik.params.ammonia_tan')} step="any" min={0} suffix="mg/L" required autoFocus />
              <HelpTooltip term="ammonia_tan" iconOnly />
            </Box>
            <Box sx={fieldWithHelpSx}>
              <FormNumberField name="nitrite_mgl" control={control} label={t('pages.aquaponik.params.nitrite')} step="any" min={0} suffix="mg/L" required />
              <HelpTooltip term="nitrite" iconOnly />
            </Box>
          </FormRow>
          <FormRow>
            <Box sx={fieldWithHelpSx}>
              <FormNumberField name="nitrate_mgl" control={control} label={t('pages.aquaponik.params.nitrate')} step="any" min={0} suffix="mg/L" required />
              <HelpTooltip term="nitrate" iconOnly />
            </Box>
            <Box sx={fieldWithHelpSx}>
              <FormNumberField name="ph" control={control} label={t('pages.aquaponik.params.ph')} step="any" min={0} max={14} required />
              <HelpTooltip term="ph" iconOnly />
            </Box>
          </FormRow>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle1" sx={{ mb: 1.5 }}>
            {t('pages.aquaponik.sectionOtherWaterValues')}
          </Typography>
          <FormRow>
            <FormNumberField name="temperature_c" control={control} label={t('pages.aquaponik.params.temperature')} step="any" suffix="°C" required />
            <Box sx={fieldWithHelpSx}>
              <FormNumberField name="dissolved_oxygen_mgl" control={control} label={t('pages.aquaponik.params.dissolved_oxygen')} step="any" min={0} suffix="mg/L" />
              <HelpTooltip term="dissolved_oxygen" iconOnly />
            </Box>
          </FormRow>
          <FormRow>
            <Box sx={fieldWithHelpSx}>
              <FormNumberField name="kh_dh" control={control} label={t('pages.aquaponik.params.kh')} step="any" min={0} suffix="°dH" />
              <HelpTooltip term="alkalinity" iconOnly />
            </Box>
            <FormNumberField name="iron_ppm" control={control} label={t('pages.aquaponik.params.iron')} step="any" min={0} suffix="ppm" />
          </FormRow>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle1" sx={{ mb: 1.5 }}>
            {t('pages.aquaponik.sectionMetadata')}
          </Typography>
          <FormSelectField
            name="source"
            control={control}
            label={t('pages.aquaponik.fields.source')}
            options={sources.map((v) => ({ value: v, label: t(`enums.waterTestSource.${v}`) }))}
          />
          <FormTextField name="notes" control={control} label={t('pages.aquaponik.fields.notes')} multiline />
          <FormActions onCancel={handleClose} loading={isSubmitting} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
