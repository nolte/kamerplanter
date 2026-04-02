import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import LocationTreeSelect from '@/components/form/LocationTreeSelect';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/tanks';
import * as sitesApi from '@/api/endpoints/sites';
import type { Site } from '@/api/types';

const tankTypes = ['nutrient', 'irrigation', 'reservoir', 'recirculation', 'stock_solution'] as const;
const materials = ['plastic', 'stainless_steel', 'glass', 'ibc'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  tank_type: z.enum(tankTypes),
  volume_liters: z.number().gt(0),
  material: z.enum(materials),
  location_key: z.string().nullable(),
  has_lid: z.boolean(),
  has_air_pump: z.boolean(),
  has_circulation_pump: z.boolean(),
  has_heater: z.boolean(),
  is_light_proof: z.boolean(),
  has_uv_sterilizer: z.boolean(),
  has_ozone_generator: z.boolean(),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function TankCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [sites, setSites] = useState<Site[]>([]);
  const [selectedSiteKey, setSelectedSiteKey] = useState('');

  const { control, handleSubmit, reset, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      tank_type: 'nutrient',
      volume_liters: 50,
      material: 'plastic',
      location_key: null,
      has_lid: false,
      has_air_pump: false,
      has_circulation_pump: false,
      has_heater: false,
      is_light_proof: false,
      has_uv_sterilizer: false,
      has_ozone_generator: false,
      notes: null,
    },
  });

  useEffect(() => {
    if (open) {
      sitesApi.listSites(0, 200).then(setSites).catch(() => {});
    }
  }, [open]);

  const handleSiteChange = (siteKey: string) => {
    setSelectedSiteKey(siteKey);
    setValue('location_key', null);
  };

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createTank({ ...data, location_key: data.location_key || null });
      notification.success(t('common.create'));
      reset();
      setSelectedSiteKey('');
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      data-testid="tank-create-dialog">
      <DialogTitle>{t('pages.tanks.create')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.tanks.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.tanks.sectionIdentification')}
          </Typography>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.tanks.name')}
            required
            autoFocus
          />
          <FormRow>
            <FormSelectField
              name="tank_type"
              control={control}
              label={t('pages.tanks.tankType')}
              options={tankTypes.map((v) => ({
                value: v,
                label: t(`enums.tankType.${v}`),
              }))}
            />
            <FormSelectField
              name="material"
              control={control}
              label={t('pages.tanks.material')}
              options={materials.map((v) => ({
                value: v,
                label: t(`enums.tankMaterial.${v}`),
              }))}
            />
          </FormRow>
          <FormNumberField
            name="volume_liters"
            control={control}
            label={t('pages.tanks.volumeLiters')}
            helperText={t('pages.tanks.volumeLitersHelper')}
            suffix="L"
            inputMode="decimal"
            min={0.1}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.tanks.sectionLocation')}
          </Typography>
          <TextField
            select
            label={t('pages.tanks.site')}
            value={selectedSiteKey}
            onChange={(e) => handleSiteChange(e.target.value)}
            fullWidth
            sx={{ mb: 2 }}
            data-testid="form-field-site"
          >
            <MenuItem value="">{'\u2014'}</MenuItem>
            {sites.map((s) => (
              <MenuItem key={s.key} value={s.key}>{s.name}</MenuItem>
            ))}
          </TextField>
          <LocationTreeSelect
            name="location_key"
            control={control}
            siteKey={selectedSiteKey || null}
            label={t('pages.tanks.location')}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5, mt: 1 }}>
            {t('pages.tanks.equipment')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.tanks.equipmentSectionIntro')}
          </Typography>
          <FormRow>
            <FormSwitchField
              name="has_lid"
              control={control}
              label={t('pages.tanks.hasLid')}
              helperText={t('pages.tanks.helperHasLid')}
            />
            <FormSwitchField
              name="has_air_pump"
              control={control}
              label={t('pages.tanks.hasAirPump')}
              helperText={t('pages.tanks.helperHasAirPump')}
            />
          </FormRow>
          <FormRow>
            <FormSwitchField
              name="has_circulation_pump"
              control={control}
              label={t('pages.tanks.hasCirculationPump')}
              helperText={t('pages.tanks.helperHasCirculationPump')}
            />
            <FormSwitchField
              name="has_heater"
              control={control}
              label={t('pages.tanks.hasHeater')}
              helperText={t('pages.tanks.helperHasHeater')}
            />
          </FormRow>
          <FormRow>
            <FormSwitchField
              name="is_light_proof"
              control={control}
              label={t('pages.tanks.isLightProof')}
              helperText={t('pages.tanks.helperIsLightProof')}
            />
            <FormSwitchField
              name="has_uv_sterilizer"
              control={control}
              label={t('pages.tanks.hasUvSterilizer')}
              helperText={t('pages.tanks.helperHasUvSterilizer')}
            />
          </FormRow>
          <FormSwitchField
            name="has_ozone_generator"
            control={control}
            label={t('pages.tanks.hasOzoneGenerator')}
            helperText={t('pages.tanks.helperHasOzoneGenerator')}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.tanks.sectionNotes')}
          </Typography>
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.tanks.notes')}
            multiline
            rows={3}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
