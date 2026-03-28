import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/species';
import type { PlantTrait } from '@/api/types';

const schema = z.object({
  name: z.string().min(1),
  breeder: z.string().nullable(),
  breeding_year: z.number().nullable(),
  traits: z.array(z.string()),
  patent_status: z.string(),
  days_to_maturity: z.number().nullable(),
  disease_resistances: z.array(z.string()),
});

type FormData = z.infer<typeof schema>;

interface CultivarPayload extends Omit<FormData, 'traits'> {
  traits: PlantTrait[];
}

interface Props {
  speciesKey: string;
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function CultivarCreateDialog({ speciesKey, open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      breeder: null,
      breeding_year: null,
      traits: [],
      patent_status: '',
      days_to_maturity: null,
      disease_resistances: [],
    },
  });
  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);


  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createCultivar(speciesKey, data as unknown as CultivarPayload);
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="create-dialog">
      <DialogTitle>{t('pages.cultivars.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Identification */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.cultivars.sectionIdentification')}
          </Typography>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.cultivars.name')}
            helperText={t('pages.cultivars.nameHelper')}
            required
            autoFocus
          />
          <FormRow>
            <FormTextField
              name="breeder"
              control={control}
              label={t('pages.cultivars.breeder')}
              helperText={t('pages.cultivars.breederHelper')}
            />
            <FormNumberField
              name="breeding_year"
              control={control}
              label={t('pages.cultivars.breedingYear')}
              helperText={t('pages.cultivars.breedingYearHelper')}
            />
          </FormRow>

          {/* Characteristics */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.cultivars.sectionCharacteristics')}
          </Typography>
          <FormNumberField
            name="days_to_maturity"
            control={control}
            label={t('pages.cultivars.daysToMaturity')}
            helperText={t('pages.cultivars.daysToMaturityHelper')}
            min={1}
            max={365}
          />
          <FormChipInput
            name="traits"
            control={control}
            label={t('pages.cultivars.traits')}
            helperText={t('pages.cultivars.traitsHelper')}
          />
          <FormChipInput
            name="disease_resistances"
            control={control}
            label={t('pages.cultivars.diseaseResistances')}
            helperText={t('pages.cultivars.diseaseResistancesHelper')}
          />
          <FormTextField
            name="patent_status"
            control={control}
            label={t('pages.cultivars.patentStatus')}
            helperText={t('pages.cultivars.patentStatusHelper')}
          />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
