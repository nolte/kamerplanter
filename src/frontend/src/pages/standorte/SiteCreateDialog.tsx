import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import ShowAllFieldsToggle from '@/components/common/ShowAllFieldsToggle';
import WaterSourceSection from '@/components/water/WaterSourceSection';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { siteFieldConfig } from '@/config/fieldConfigs';
import * as api from '@/api/endpoints/sites';
import type { SiteWaterConfig } from '@/api/types';

const schema = z.object({
  name: z.string().min(1),
  climate_zone: z.string(),
  total_area_m2: z.number().min(0),
  timezone: z.string(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function SiteCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const { showAllOverride, toggleShowAll, level } = useExpertiseLevel();
  const [waterConfig, setWaterConfig] = useState<SiteWaterConfig>({
    has_ro_system: false,
    tap_water_profile: null,
    ro_water_profile: null,
  });

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', climate_zone: '', total_area_m2: 0, timezone: 'UTC' },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const hasWaterData = waterConfig.tap_water_profile || waterConfig.has_ro_system;
      await api.createSite({
        ...data,
        water_config: hasWaterData ? waterConfig : undefined,
      });
      notification.success(t('common.create'));
      reset();
      setWaterConfig({ has_ro_system: false, tap_water_profile: null, ro_water_profile: null });
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const fc = siteFieldConfig;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.sites.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* beginner */}
          <FormTextField name="name" control={control} label={t('pages.sites.name')} required />
          {/* intermediate */}
          <ExpertiseFieldWrapper minLevel={fc.climate_zone.level}>
            <FormTextField name="climate_zone" control={control} label={t('pages.sites.climateZone')} />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.total_area_m2.level}>
            <FormNumberField name="total_area_m2" control={control} label={t('pages.sites.totalArea')} helperText={t('pages.sites.totalAreaHelper')} min={0} />
          </ExpertiseFieldWrapper>
          {/* water config (intermediate+) */}
          <ExpertiseFieldWrapper minLevel={fc.water_config.level}>
            <WaterSourceSection value={waterConfig} onChange={setWaterConfig} />
          </ExpertiseFieldWrapper>
          {/* expert */}
          <ExpertiseFieldWrapper minLevel={fc.timezone.level}>
            <FormTextField name="timezone" control={control} label={t('pages.sites.timezone')} helperText={t('pages.sites.timezoneHelper')} />
          </ExpertiseFieldWrapper>
          {level !== 'expert' && (
            <ShowAllFieldsToggle showAll={showAllOverride} onToggle={toggleShowAll} />
          )}
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
